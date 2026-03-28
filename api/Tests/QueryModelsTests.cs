using System.Text.Json.Serialization;
using Xunit;
using api.Models;

namespace api.Tests;

public class QueryModelsTests
{
    [Fact]
    public void QueryRequest_DeserializesCorrectly()
    {
        // Arrange
        var json = @"{
            ""tool"": ""market_share"",
            ""dimensions"": {
                ""brands"": [""Nike"", ""Adidas""],
                ""categories"": [""Athletic""],
                ""geographies"": [""CA"", ""NY""],
                ""generations"": [],
                ""incomeBands"": [],
                ""channels"": [],
                ""dayOfWeek"": [],
                ""paymentNetworks"": []
            },
            ""aggregation"": {
                ""metric"": ""sum"",
                ""period"": {
                    ""start"": ""2024-01-01"",
                    ""end"": ""2024-12-31""
                }
            },
            ""pagination"": {
                ""limit"": 100,
                ""offset"": 0
            }
        }";

        // Act
        var request = System.Text.Json.JsonSerializer.Deserialize<QueryRequest>(json);

        // Assert
        Assert.NotNull(request);
        Assert.Equal("market_share", request.Tool);
        Assert.NotNull(request.Dimensions);
        Assert.Equal(2, request.Dimensions.Brands.Count);
        Assert.Equal("Nike", request.Dimensions.Brands[0]);
        Assert.Equal("sum", request.Aggregation.Metric);
        Assert.Equal(100, request.Pagination.Limit);
    }

    [Fact]
    public void QueryRequest_DefaultPaginationValues()
    {
        // Arrange
        var json = @"{
            ""tool"": ""revenue"",
            ""dimensions"": {},
            ""aggregation"": {
                ""metric"": ""avg"",
                ""period"": {
                    ""start"": ""2024-01-01"",
                    ""end"": ""2024-12-31""
                }
            }
        }";

        // Act
        var request = System.Text.Json.JsonSerializer.Deserialize<QueryRequest>(json);

        // Assert
        Assert.NotNull(request);
        Assert.Equal(1000, request.Pagination.Limit); // Default max
        Assert.Equal(0, request.Pagination.Offset);
    }

    [Fact]
    public void Dimensions_AllPropertiesSerializeCorrectly()
    {
        // Arrange
        var dimensions = new Dimensions
        {
            Brands = new List<string> { "Nike" },
            Categories = new List<string> { "Athletic", "Footwear" },
            Geographies = new List<string> { "CA" },
            Generations = new List<string>(),
            IncomeBands = new List<string>(),
            Channels = new List<string>(),
            DayOfWeek = new List<string>(),
            PaymentNetworks = new List<string>()
        };

        // Act
        var json = System.Text.Json.JsonSerializer.Serialize(dimensions);
        var deserialized = System.Text.Json.JsonSerializer.Deserialize<Dimensions>(json);

        // Assert
        Assert.NotNull(deserialized);
        Assert.Single(deserialized.Brands);
        Assert.Equal(2, deserialized.Categories.Count);
    }

    [Theory]
    [InlineData("sum")]
    [InlineData("avg")]
    [InlineData("count")]
    [InlineData("min")]
    [InlineData("max")]
    [InlineData("median")]
    public void AggregationConfig_AcceptsValidMetrics(string metric)
    {
        // Arrange
        var json = $@"{{
            ""metric"": ""{metric}"",
            ""period"": {{
                ""start"": ""2024-01-01"",
                ""end"": ""2024-12-31""
            }}
        }}";

        // Act
        var config = System.Text.Json.JsonSerializer.Deserialize<AggregationConfig>(json);

        // Assert
        Assert.NotNull(config);
        Assert.Equal(metric, config.Metric);
    }
}
