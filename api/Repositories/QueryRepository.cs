using System.Diagnostics;
using api.Models;
using api.Services;

namespace api.Repositories;

public class QueryRepository : IQueryRepository
{
    private readonly TimescaleRepository _timescaleRepository;
    private readonly AggregationLevelResolver _aggregationLevelResolver;

    public QueryRepository(TimescaleRepository timescaleRepository, AggregationLevelResolver aggregationLevelResolver)
    {
        _timescaleRepository = timescaleRepository;
        _aggregationLevelResolver = aggregationLevelResolver;
    }

    public async Task<QueryResponse> ExecuteQueryAsync(QueryRequest request, string requestId, CancellationToken cancellationToken = default)
    {
        var stopwatch = Stopwatch.StartNew();

        // Placeholder implementation - returns mock data
        // Actual TimescaleDB queries will be added in a future iteration
        await Task.Delay(10, cancellationToken); // Simulate query time

        stopwatch.Stop();

        var aggregationLevel = _aggregationLevelResolver.Resolve(request.Aggregation.Period);

        // Return mock response data
        var mockData = new List<Dictionary<string, object>>
        {
            new() { ["brand"] = request.Dimensions.Brands.FirstOrDefault() ?? "Unknown", ["metric_value"] = 1000.00m }
        };

        return new QueryResponse
        {
            Data = mockData,
            Metadata = new QueryMetadata
            {
                RequestId = requestId,
                ExecutionTimeMs = stopwatch.ElapsedMilliseconds,
                RowsReturned = mockData.Count,
                AggregationLevel = aggregationLevel
            }
        };
    }

    public async Task<BatchQueryResponse> ExecuteBatchQueryAsync(BatchQueryRequest request, CancellationToken cancellationToken = default)
    {
        var stopwatch = Stopwatch.StartNew();
        var results = new Dictionary<string, QueryResponse>();
        var latencyPerQuery = new Dictionary<string, long>();

        var queryIndex = 0;
        foreach (var query in request.Queries)
        {
            var queryStopwatch = Stopwatch.StartNew();
            var queryId = $"query_{queryIndex}";

            results[queryId] = await ExecuteQueryAsync(query, queryId, cancellationToken);

            queryStopwatch.Stop();
            latencyPerQuery[queryId] = queryStopwatch.ElapsedMilliseconds;

            queryIndex++;
        }

        stopwatch.Stop();

        // Generate synthesized summary
        var summary = $"Executed {request.Queries.Count} queries. " +
                     $"Total time: {stopwatch.ElapsedMilliseconds}ms. " +
                     $"Results: {results.Values.Sum(r => r.Metadata.RowsReturned)} total rows.";

        return new BatchQueryResponse
        {
            Results = results,
            LatencyPerQuery = latencyPerQuery,
            TotalExecutionTimeMs = stopwatch.ElapsedMilliseconds,
            SynthesizedSummary = summary
        };
    }
}
