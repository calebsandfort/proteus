using Xunit;
using api.Models;

namespace api.Tests;

public class BatchQueryTests
{
    [Fact]
    public void BatchQueryRequest_DeserializesCorrectly()
    {
        // Arrange
        var json = @"{
            ""queries"": [
                {
                    ""tool"": ""market_share"",
                    ""dimensions"": { ""brands"": [""Nike""] },
                    ""aggregation"": { ""metric"": ""sum"", ""period"": { ""start"": ""2024-01-01"", ""end"": ""2024-12-31"" } },
                    ""pagination"": { ""limit"": 100, ""offset"": 0 }
                },
                {
                    ""tool"": ""revenue"",
                    ""dimensions"": { ""categories"": [""Athletic""] },
                    ""aggregation"": { ""metric"": ""avg"", ""period"": { ""start"": ""2024-01-01"", ""end"": ""2024-12-31"" } },
                    ""pagination"": { ""limit"": 50, ""offset"": 0 }
                }
            ]
        }";

        // Act
        var request = System.Text.Json.JsonSerializer.Deserialize<BatchQueryRequest>(json);

        // Assert
        Assert.NotNull(request);
        Assert.Equal(2, request.Queries.Count);
        Assert.Equal("market_share", request.Queries[0].Tool);
        Assert.Equal("revenue", request.Queries[1].Tool);
    }

    [Fact]
    public void BatchQueryResponse_ContainsLatencyPerQuery()
    {
        // Arrange
        var response = new BatchQueryResponse
        {
            Results = new Dictionary<string, QueryResponse>(),
            LatencyPerQuery = new Dictionary<string, long>
            {
                { "query_1", 150 },
                { "query_2", 200 }
            },
            TotalExecutionTimeMs = 350,
            SynthesizedSummary = "Summary text"
        };

        // Assert
        Assert.Equal(2, response.LatencyPerQuery.Count);
        Assert.Equal(150, response.LatencyPerQuery["query_1"]);
        Assert.Equal(200, response.LatencyPerQuery["query_2"]);
        Assert.Equal(350, response.TotalExecutionTimeMs);
    }

    [Fact]
    public void QueryMetadata_ContainsRequestId()
    {
        // Arrange
        var metadata = new QueryMetadata
        {
            RequestId = "uuid-12345",
            ExecutionTimeMs = 100,
            RowsReturned = 50,
            AggregationLevel = AggregationLevel.Daily
        };

        // Assert
        Assert.Equal("uuid-12345", metadata.RequestId);
        Assert.Equal(100, metadata.ExecutionTimeMs);
        Assert.Equal(50, metadata.RowsReturned);
        Assert.Equal(AggregationLevel.Daily, metadata.AggregationLevel);
    }
}
