using System.Text.Json.Serialization;

namespace api.Models;

public class QueryRequest
{
    [JsonPropertyName("tool")]
    public string Tool { get; set; } = string.Empty;

    [JsonPropertyName("dimensions")]
    public Dimensions Dimensions { get; set; } = new();

    [JsonPropertyName("aggregation")]
    public AggregationConfig Aggregation { get; set; } = new();

    [JsonPropertyName("pagination")]
    public PaginationConfig Pagination { get; set; } = new() { Limit = 1000, Offset = 0 };
}

public class Dimensions
{
    [JsonPropertyName("brands")]
    public List<string> Brands { get; set; } = new();

    [JsonPropertyName("categories")]
    public List<string> Categories { get; set; } = new();

    [JsonPropertyName("geographies")]
    public List<string> Geographies { get; set; } = new();

    [JsonPropertyName("generations")]
    public List<string> Generations { get; set; } = new();

    [JsonPropertyName("incomeBands")]
    public List<string> IncomeBands { get; set; } = new();

    [JsonPropertyName("channels")]
    public List<string> Channels { get; set; } = new();

    [JsonPropertyName("dayOfWeek")]
    public List<string> DayOfWeek { get; set; } = new();

    [JsonPropertyName("paymentNetworks")]
    public List<string> PaymentNetworks { get; set; } = new();

    public bool HasHighCardinalityFilter => Brands.Count >= 1 || Categories.Count >= 1 || Geographies.Count >= 1;
}

public class AggregationConfig
{
    [JsonPropertyName("metric")]
    public string Metric { get; set; } = "sum";

    [JsonPropertyName("period")]
    public PeriodConfig Period { get; set; } = new();
}

public class PeriodConfig
{
    [JsonPropertyName("start")]
    public DateTime Start { get; set; }

    [JsonPropertyName("end")]
    public DateTime End { get; set; }

    public int TotalDays => (End - Start).Days;
}

public class PaginationConfig
{
    [JsonPropertyName("limit")]
    public int Limit { get; set; } = 1000;

    [JsonPropertyName("offset")]
    public int Offset { get; set; } = 0;
}

public class QueryResponse
{
    [JsonPropertyName("data")]
    public List<Dictionary<string, object>> Data { get; set; } = new();

    [JsonPropertyName("metadata")]
    public QueryMetadata Metadata { get; set; } = new();
}

public class QueryMetadata
{
    [JsonPropertyName("requestId")]
    public string RequestId { get; set; } = string.Empty;

    [JsonPropertyName("executionTimeMs")]
    public long ExecutionTimeMs { get; set; }

    [JsonPropertyName("rowsReturned")]
    public int RowsReturned { get; set; }

    [JsonPropertyName("aggregationLevel")]
    public AggregationLevel AggregationLevel { get; set; }
}

public enum AggregationLevel
{
    Daily,
    Weekly,
    Monthly,
    Quarterly,
    Annual
}

public class BatchQueryRequest
{
    [JsonPropertyName("queries")]
    public List<QueryRequest> Queries { get; set; } = new();
}

public class BatchQueryResponse
{
    [JsonPropertyName("results")]
    public Dictionary<string, QueryResponse> Results { get; set; } = new();

    [JsonPropertyName("latencyPerQuery")]
    public Dictionary<string, long> LatencyPerQuery { get; set; } = new();

    [JsonPropertyName("totalExecutionTimeMs")]
    public long TotalExecutionTimeMs { get; set; }

    [JsonPropertyName("synthesizedSummary")]
    public string? SynthesizedSummary { get; set; }
}

public class DimensionValue
{
    [JsonPropertyName("id")]
    public string Id { get; set; } = string.Empty;

    [JsonPropertyName("canonicalName")]
    public string CanonicalName { get; set; } = string.Empty;

    [JsonPropertyName("aliases")]
    public List<string> Aliases { get; set; } = new();
}

public class DimensionValuesResponse
{
    [JsonPropertyName("dimension")]
    public string Dimension { get; set; } = string.Empty;

    [JsonPropertyName("values")]
    public List<DimensionValue> Values { get; set; } = new();

    [JsonPropertyName("cachedAt")]
    public DateTime CachedAt { get; set; }

    [JsonPropertyName("cacheExpiresAt")]
    public DateTime CacheExpiresAt { get; set; }
}
