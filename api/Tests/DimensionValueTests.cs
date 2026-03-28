using Xunit;
using api.Models;

namespace api.Tests;

public class DimensionValueTests
{
    [Fact]
    public void DimensionValue_DeserializesCorrectly()
    {
        // Arrange
        var json = @"{
            ""id"": ""nike"",
            ""canonicalName"": ""Nike"",
            ""aliases"": [""Nike Inc."", ""Nike Brand""]
        }";

        // Act
        var value = System.Text.Json.JsonSerializer.Deserialize<DimensionValue>(json);

        // Assert
        Assert.NotNull(value);
        Assert.Equal("nike", value.Id);
        Assert.Equal("Nike", value.CanonicalName);
        Assert.Equal(2, value.Aliases.Count);
        Assert.Contains("Nike Inc.", value.Aliases);
    }

    [Fact]
    public void DimensionValue_WithEmptyAliases_SerializesCorrectly()
    {
        // Arrange
        var value = new DimensionValue
        {
            Id = "adidas",
            CanonicalName = "Adidas",
            Aliases = new List<string>()
        };

        // Act
        var json = System.Text.Json.JsonSerializer.Serialize(value);
        var deserialized = System.Text.Json.JsonSerializer.Deserialize<DimensionValue>(json);

        // Assert
        Assert.NotNull(deserialized);
        Assert.Empty(deserialized.Aliases);
    }

    [Fact]
    public void DimensionValuesResponse_ContainsValues()
    {
        // Arrange
        var response = new DimensionValuesResponse
        {
            Dimension = "brands",
            Values = new List<DimensionValue>
            {
                new() { Id = "nike", CanonicalName = "Nike", Aliases = new List<string>() },
                new() { Id = "adidas", CanonicalName = "Adidas", Aliases = new List<string>() }
            },
            CachedAt = DateTime.UtcNow,
            CacheExpiresAt = DateTime.UtcNow.AddHours(24)
        };

        // Assert
        Assert.Equal("brands", response.Dimension);
        Assert.Equal(2, response.Values.Count);
        Assert.True(response.CacheExpiresAt > response.CachedAt);
    }
}
