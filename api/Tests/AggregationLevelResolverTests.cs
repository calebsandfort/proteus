using Xunit;
using api.Models;
using api.Services;

namespace api.Tests;

public class AggregationLevelResolverTests
{
    private readonly AggregationLevelResolver _resolver = new();

    [Theory]
    [InlineData(1, AggregationLevel.Daily)]
    [InlineData(7, AggregationLevel.Daily)]
    [InlineData(14, AggregationLevel.Daily)]
    public void Resolve_With1To14Days_ReturnsDaily(int days, AggregationLevel expected)
    {
        // Arrange
        var start = new DateTime(2024, 1, 1);
        var end = start.AddDays(days);

        // Act
        var result = _resolver.Resolve(start, end);

        // Assert
        Assert.Equal(expected, result);
    }

    [Theory]
    [InlineData(15, AggregationLevel.Weekly)]
    [InlineData(30, AggregationLevel.Weekly)]
    [InlineData(90, AggregationLevel.Weekly)]
    public void Resolve_With15To90Days_ReturnsWeekly(int days, AggregationLevel expected)
    {
        // Arrange
        var start = new DateTime(2024, 1, 1);
        var end = start.AddDays(days);

        // Act
        var result = _resolver.Resolve(start, end);

        // Assert
        Assert.Equal(expected, result);
    }

    [Theory]
    [InlineData(91, AggregationLevel.Monthly)]
    [InlineData(180, AggregationLevel.Monthly)]
    [InlineData(365, AggregationLevel.Monthly)]
    public void Resolve_With91To365Days_ReturnsMonthly(int days, AggregationLevel expected)
    {
        // Arrange
        var start = new DateTime(2024, 1, 1);
        var end = start.AddDays(days);

        // Act
        var result = _resolver.Resolve(start, end);

        // Assert
        Assert.Equal(expected, result);
    }

    [Theory]
    [InlineData(366, AggregationLevel.Quarterly)]
    [InlineData(730, AggregationLevel.Quarterly)]
    public void Resolve_With1To2Years_ReturnsQuarterly(int days, AggregationLevel expected)
    {
        // Arrange
        var start = new DateTime(2024, 1, 1);
        var end = start.AddDays(days);

        // Act
        var result = _resolver.Resolve(start, end);

        // Assert
        Assert.Equal(expected, result);
    }

    [Theory]
    [InlineData(731, AggregationLevel.Annual)]
    [InlineData(1095, AggregationLevel.Annual)]
    public void Resolve_With2PlusYears_ReturnsAnnual(int days, AggregationLevel expected)
    {
        // Arrange
        var start = new DateTime(2024, 1, 1);
        var end = start.AddDays(days);

        // Act
        var result = _resolver.Resolve(start, end);

        // Assert
        Assert.Equal(expected, result);
    }

    [Fact]
    public void Resolve_EdgeCase_Exactly90Days_ReturnsWeekly()
    {
        // Arrange
        var start = new DateTime(2024, 1, 1);
        var end = start.AddDays(90);

        // Act
        var result = _resolver.Resolve(start, end);

        // Assert
        Assert.Equal(AggregationLevel.Weekly, result);
    }

    [Fact]
    public void Resolve_EdgeCase_Exactly365Days_ReturnsMonthly()
    {
        // Arrange
        var start = new DateTime(2024, 1, 1);
        var end = start.AddDays(365);

        // Act
        var result = _resolver.Resolve(start, end);

        // Assert
        Assert.Equal(AggregationLevel.Monthly, result);
    }
}
