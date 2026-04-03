using System.Diagnostics;
using api.Models;
using api.Services;

namespace api.Repositories;

public class ProteusQueryRepository : IQueryRepository
{
    private readonly TimescaleRepository _db;
    private readonly AggregationLevelResolver _resolver;

    public ProteusQueryRepository(TimescaleRepository db, AggregationLevelResolver resolver)
    {
        _db = db;
        _resolver = resolver;
    }

    public async Task<QueryResponse> ExecuteQueryAsync(QueryRequest request, string requestId, CancellationToken cancellationToken = default)
    {
        var sw = Stopwatch.StartNew();
        var level = _resolver.Resolve(request.Aggregation.Period);
        var (sql, parameters) = BuildQuery(request, level);

        var rows = await _db.QueryAsync<dynamic>(sql, parameters);
        var data = rows.Select(ToDict).ToList();

        sw.Stop();
        return new QueryResponse
        {
            Data = data,
            Metadata = new QueryMetadata
            {
                RequestId = requestId,
                ExecutionTimeMs = sw.ElapsedMilliseconds,
                RowsReturned = data.Count,
                AggregationLevel = level
            }
        };
    }

    public async Task<BatchQueryResponse> ExecuteBatchQueryAsync(BatchQueryRequest request, CancellationToken cancellationToken = default)
    {
        var sw = Stopwatch.StartNew();

        var tasks = request.Queries.Select(async (query, i) =>
        {
            var qSw = Stopwatch.StartNew();
            var queryId = $"query_{i}";
            var response = await ExecuteQueryAsync(query, queryId, cancellationToken);
            qSw.Stop();
            return (queryId, response, latency: qSw.ElapsedMilliseconds);
        });

        var results = await Task.WhenAll(tasks);
        sw.Stop();

        return new BatchQueryResponse
        {
            Results = results.ToDictionary(r => r.queryId, r => r.response),
            LatencyPerQuery = results.ToDictionary(r => r.queryId, r => r.latency),
            TotalExecutionTimeMs = sw.ElapsedMilliseconds,
            SynthesizedSummary = $"Executed {results.Length} queries in parallel. Total rows: {results.Sum(r => r.response.Metadata.RowsReturned)}."
        };
    }

    private static Dictionary<string, object> ToDict(dynamic row)
    {
        var result = new Dictionary<string, object>();
        foreach (var kvp in (IDictionary<string, object>)row)
            if (kvp.Value is not null)
                result[kvp.Key] = kvp.Value;
        return result;
    }

    private (string Sql, object Parameters) BuildQuery(QueryRequest request, AggregationLevel level) =>
        request.Tool switch
        {
            "market_share_trend" => MarketShareTrend(request, level),
            "brand_comparison"   => BrandComparison(request, level),
            "yoy_growth_analysis" => YoyGrowthAnalysis(request),
            "same_store_sales"   => SameStoreSales(request),
            "category_trends"    => CategoryTrends(request, level),
            "wallet_share"       => WalletShare(request, level),
            _                    => DefaultSpendQuery(request, level)
        };

    private static string BucketInterval(AggregationLevel level) => level switch
    {
        AggregationLevel.Daily     => "1 day",
        AggregationLevel.Weekly    => "7 days",
        AggregationLevel.Monthly   => "1 month",
        AggregationLevel.Quarterly => "3 months",
        _                          => "1 year"
    };

    private static string BaseTable(AggregationLevel level) => level switch
    {
        AggregationLevel.Daily  => "transactions_daily",
        AggregationLevel.Weekly => "transactions_weekly",
        _                       => "transactions_monthly"
    };

    // -------------------------------------------------------------------------
    // market_share_trend
    // Computes brand_spend / category_total_spend from the base transaction
    // aggregates. market_share_daily has limited date coverage so we derive
    // market share directly — this works for any date range with data.
    // -------------------------------------------------------------------------
    private static (string, object) MarketShareTrend(QueryRequest req, AggregationLevel level)
    {
        var interval = BucketInterval(level);
        var table    = BaseTable(level);
        var sql = $@"
            WITH brand_spend AS (
                SELECT
                    time_bucket('{interval}', t.bucket) AS period,
                    t.category_id,
                    t.brand_id,
                    SUM(t.total_spend)        AS brand_spend,
                    SUM(t.transaction_count)  AS transaction_count
                FROM {table} t
                WHERE t.bucket >= @start_date
                  AND t.bucket <  @end_date
                GROUP BY 1, 2, 3
            ),
            category_total AS (
                SELECT
                    time_bucket('{interval}', t.bucket) AS period,
                    t.category_id,
                    SUM(t.total_spend) AS category_total_spend
                FROM {table} t
                WHERE t.bucket >= @start_date
                  AND t.bucket <  @end_date
                GROUP BY 1, 2
            )
            SELECT
                bs.period,
                b.name                                                          AS brand,
                bs.brand_spend,
                ct.category_total_spend,
                CASE WHEN ct.category_total_spend > 0
                     THEN ROUND(bs.brand_spend / ct.category_total_spend * 100, 4)
                     ELSE 0 END                                                 AS market_share_pct,
                bs.transaction_count
            FROM brand_spend bs
            JOIN brands b        ON b.id  = bs.brand_id
            JOIN category_total ct ON ct.period      = bs.period
                                  AND ct.category_id = bs.category_id
            WHERE b.name = ANY(@brands)
            ORDER BY 1, 2
            LIMIT @limit OFFSET @offset";

        return (sql, StandardParams(req));
    }

    // -------------------------------------------------------------------------
    // brand_comparison
    // Direct spend comparison across brands over time.
    // -------------------------------------------------------------------------
    private static (string, object) BrandComparison(QueryRequest req, AggregationLevel level)
    {
        var interval = BucketInterval(level);
        var table    = BaseTable(level);
        var sql = $@"
            SELECT
                time_bucket('{interval}', t.bucket)  AS period,
                b.name                               AS brand,
                SUM(t.total_spend)                   AS total_spend,
                SUM(t.transaction_count)             AS transaction_count,
                ROUND(AVG(t.avg_spend), 2)           AS avg_transaction_value
            FROM {table} t
            JOIN brands b ON b.id = t.brand_id
            WHERE b.name = ANY(@brands)
              AND t.bucket >= @start_date
              AND t.bucket <  @end_date
            GROUP BY 1, 2
            ORDER BY 1, 2
            LIMIT @limit OFFSET @offset";

        return (sql, StandardParams(req));
    }

    // -------------------------------------------------------------------------
    // yoy_growth_analysis
    // Compares current period spend vs same period one year prior.
    // -------------------------------------------------------------------------
    private static (string, object) YoyGrowthAnalysis(QueryRequest req)
    {
        var sql = @"
            WITH current_period AS (
                SELECT b.name                AS brand,
                       SUM(t.total_spend)    AS current_spend,
                       SUM(t.transaction_count) AS current_count
                FROM transactions_monthly t
                JOIN brands b ON b.id = t.brand_id
                WHERE b.name = ANY(@brands)
                  AND t.bucket >= @start_date
                  AND t.bucket <  @end_date
                GROUP BY 1
            ),
            prior_period AS (
                SELECT b.name                AS brand,
                       SUM(t.total_spend)    AS prior_spend,
                       SUM(t.transaction_count) AS prior_count
                FROM transactions_monthly t
                JOIN brands b ON b.id = t.brand_id
                WHERE b.name = ANY(@brands)
                  AND t.bucket >= @start_date - INTERVAL '1 year'
                  AND t.bucket <  @end_date   - INTERVAL '1 year'
                GROUP BY 1
            )
            SELECT
                c.brand,
                c.current_spend,
                p.prior_spend,
                c.current_count,
                p.prior_count,
                CASE WHEN COALESCE(p.prior_spend, 0) > 0
                     THEN ROUND((c.current_spend - p.prior_spend) / p.prior_spend * 100, 2)
                     ELSE NULL END AS yoy_spend_growth_pct,
                CASE WHEN COALESCE(p.prior_count, 0) > 0
                     THEN ROUND((c.current_count::DECIMAL - p.prior_count) / p.prior_count * 100, 2)
                     ELSE NULL END AS yoy_count_growth_pct
            FROM current_period c
            LEFT JOIN prior_period p ON p.brand = c.brand
            ORDER BY c.brand
            LIMIT @limit OFFSET @offset";

        return (sql, StandardParams(req));
    }

    // -------------------------------------------------------------------------
    // same_store_sales
    // Retained-cohort approximation: panelists active in both periods.
    // -------------------------------------------------------------------------
    private static (string, object) SameStoreSales(QueryRequest req)
    {
        var sql = @"
            WITH brand_ids AS (
                SELECT id FROM brands WHERE name = ANY(@brands)
            ),
            retained_panelists AS (
                SELECT t1.panelist_id
                FROM transactions t1
                WHERE t1.brand_id IN (SELECT id FROM brand_ids)
                  AND t1.transaction_timestamp >= @start_date
                  AND t1.transaction_timestamp <  @end_date
                INTERSECT
                SELECT t2.panelist_id
                FROM transactions t2
                WHERE t2.brand_id IN (SELECT id FROM brand_ids)
                  AND t2.transaction_timestamp >= @start_date - INTERVAL '1 year'
                  AND t2.transaction_timestamp <  @end_date   - INTERVAL '1 year'
            ),
            current_period AS (
                SELECT b.name                        AS brand,
                       SUM(t.transaction_amount)     AS retained_spend,
                       COUNT(*)                      AS transaction_count
                FROM transactions t
                JOIN brands b ON b.id = t.brand_id
                WHERE b.name = ANY(@brands)
                  AND t.transaction_timestamp >= @start_date
                  AND t.transaction_timestamp <  @end_date
                  AND t.panelist_id IN (SELECT panelist_id FROM retained_panelists)
                GROUP BY 1
            ),
            prior_period AS (
                SELECT b.name                        AS brand,
                       SUM(t.transaction_amount)     AS prior_retained_spend
                FROM transactions t
                JOIN brands b ON b.id = t.brand_id
                WHERE b.name = ANY(@brands)
                  AND t.transaction_timestamp >= @start_date - INTERVAL '1 year'
                  AND t.transaction_timestamp <  @end_date   - INTERVAL '1 year'
                  AND t.panelist_id IN (SELECT panelist_id FROM retained_panelists)
                GROUP BY 1
            )
            SELECT
                c.brand,
                c.retained_spend                      AS current_spend,
                p.prior_retained_spend                AS prior_spend,
                c.transaction_count,
                CASE WHEN COALESCE(p.prior_retained_spend, 0) > 0
                     THEN ROUND((c.retained_spend - p.prior_retained_spend) / p.prior_retained_spend * 100, 2)
                     ELSE NULL END                    AS same_store_growth_pct
            FROM current_period c
            LEFT JOIN prior_period p ON p.brand = c.brand
            ORDER BY c.brand
            LIMIT @limit OFFSET @offset";

        return (sql, StandardParams(req));
    }

    // -------------------------------------------------------------------------
    // category_trends
    // Category-level transaction volume and spend over time.
    // -------------------------------------------------------------------------
    private static (string, object) CategoryTrends(QueryRequest req, AggregationLevel level)
    {
        var interval       = BucketInterval(level);
        var table          = BaseTable(level);
        var categoryFilter = req.Dimensions.Categories.Count > 0
            ? "AND c.level1 = ANY(@categories)"
            : "";

        var sql = $@"
            SELECT
                time_bucket('{interval}', t.bucket)  AS period,
                c.level1                             AS category,
                SUM(t.total_spend)                   AS total_spend,
                SUM(t.transaction_count)             AS transaction_count,
                ROUND(AVG(t.avg_spend), 2)           AS avg_spend
            FROM {table} t
            JOIN categories c ON c.id = t.category_id
            WHERE t.bucket >= @start_date
              AND t.bucket <  @end_date
              {categoryFilter}
            GROUP BY 1, 2
            ORDER BY 1, 2
            LIMIT @limit OFFSET @offset";

        return (sql, new
        {
            brands      = req.Dimensions.Brands.ToArray(),
            categories  = req.Dimensions.Categories.ToArray(),
            start_date  = req.Aggregation.Period.Start,
            end_date    = req.Aggregation.Period.End,
            limit       = req.Pagination.Limit,
            offset      = req.Pagination.Offset
        });
    }

    // -------------------------------------------------------------------------
    // wallet_share
    // Each brand's share of the combined spend across the queried brands.
    // -------------------------------------------------------------------------
    private static (string, object) WalletShare(QueryRequest req, AggregationLevel level)
    {
        var interval = BucketInterval(level);
        var table    = BaseTable(level);
        var sql = $@"
            WITH brand_spend AS (
                SELECT
                    time_bucket('{interval}', t.bucket)  AS period,
                    b.name                               AS brand,
                    SUM(t.total_spend)                   AS brand_spend,
                    SUM(t.transaction_count)             AS transaction_count
                FROM {table} t
                JOIN brands b ON b.id = t.brand_id
                WHERE b.name = ANY(@brands)
                  AND t.bucket >= @start_date
                  AND t.bucket <  @end_date
                GROUP BY 1, 2
            ),
            total_spend AS (
                SELECT
                    time_bucket('{interval}', t.bucket)  AS period,
                    SUM(t.total_spend)                   AS total_spend
                FROM {table} t
                JOIN brands b ON b.id = t.brand_id
                WHERE b.name = ANY(@brands)
                  AND t.bucket >= @start_date
                  AND t.bucket <  @end_date
                GROUP BY 1
            )
            SELECT
                bs.period,
                bs.brand,
                bs.brand_spend,
                ts.total_spend,
                CASE WHEN ts.total_spend > 0
                     THEN ROUND(bs.brand_spend / ts.total_spend * 100, 4)
                     ELSE 0 END AS wallet_share_pct,
                bs.transaction_count
            FROM brand_spend bs
            JOIN total_spend ts ON ts.period = bs.period
            ORDER BY 1, 2
            LIMIT @limit OFFSET @offset";

        return (sql, StandardParams(req));
    }

    // -------------------------------------------------------------------------
    // Default: generic brand spend query for unknown tool names.
    // -------------------------------------------------------------------------
    private static (string, object) DefaultSpendQuery(QueryRequest req, AggregationLevel level)
    {
        var interval    = BucketInterval(level);
        var table       = BaseTable(level);
        var brandFilter = req.Dimensions.Brands.Count > 0 ? "AND b.name = ANY(@brands)" : "";

        var sql = $@"
            SELECT
                time_bucket('{interval}', t.bucket)  AS period,
                b.name                               AS brand,
                SUM(t.total_spend)                   AS total_spend,
                SUM(t.transaction_count)             AS transaction_count
            FROM {table} t
            JOIN brands b ON b.id = t.brand_id
            WHERE t.bucket >= @start_date
              AND t.bucket <  @end_date
              {brandFilter}
            GROUP BY 1, 2
            ORDER BY 1, 2
            LIMIT @limit OFFSET @offset";

        return (sql, StandardParams(req));
    }

    private static object StandardParams(QueryRequest req) => new
    {
        brands     = req.Dimensions.Brands.ToArray(),
        start_date = req.Aggregation.Period.Start,
        end_date   = req.Aggregation.Period.End,
        limit      = req.Pagination.Limit,
        offset     = req.Pagination.Offset
    };
}
