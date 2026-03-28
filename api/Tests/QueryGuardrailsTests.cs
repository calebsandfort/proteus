using Xunit;
using api.Models;
using api.Validators;

namespace api.Tests;

public class QueryGuardrailsTests
{
    private readonly QueryGuardrailValidator _validator = new();

    [Fact]
    public void Validate_WithValidBrandsFilter_ReturnsNoError()
    {
        // Arrange
        var request = CreateValidRequest();
        request.Dimensions.Brands = Enumerable.Range(1, 5).Select(i => $"Brand{i}").ToList();
        request.Dimensions.Categories = new List<string>();

        // Act
        var result = _validator.Validate(request);

        // Assert
        Assert.True(result.IsValid);
        Assert.Empty(result.Errors);
    }

    [Fact]
    public void Validate_WithTooManyBrands_ReturnsError()
    {
        // Arrange
        var request = CreateValidRequest();
        request.Dimensions.Brands = Enumerable.Range(1, 51).Select(i => $"Brand{i}").ToList(); // 51 brands

        // Act
        var result = _validator.Validate(request);

        // Assert
        Assert.False(result.IsValid);
        Assert.Contains(result.Errors, e => e.Code == ErrorCode.InsufficientFilters);
    }

    [Fact]
    public void Validate_WithZeroBrandsAndNoOtherFilters_ReturnsError()
    {
        // Arrange - a request with no brands, no categories, no geo, and no time range
        var request = CreateValidRequest();
        request.Dimensions.Brands = new List<string>(); // 0 brands
        request.Dimensions.Categories = new List<string>(); // 0 categories
        request.Dimensions.Geographies = new List<string>(); // 0 geographies
        request.Aggregation.Period = new PeriodConfig { Start = new DateTime(2024, 1, 1), End = new DateTime(2024, 1, 2) }; // only 1 day

        // Act
        var result = _validator.Validate(request);

        // Assert
        Assert.False(result.IsValid);
        Assert.Contains(result.Errors, e => e.Code == ErrorCode.InsufficientFilters);
    }

    [Fact]
    public void Validate_WithTooManyCategories_ReturnsError()
    {
        // Arrange
        var request = CreateValidRequest();
        request.Dimensions.Categories = Enumerable.Range(1, 11).Select(i => $"Category{i}").ToList(); // 11 categories

        // Act
        var result = _validator.Validate(request);

        // Assert
        Assert.False(result.IsValid);
        Assert.Contains(result.Errors, e => e.Code == ErrorCode.InsufficientFilters);
    }

    [Fact]
    public void Validate_WithTooManyGeographies_ReturnsError()
    {
        // Arrange
        var request = CreateValidRequest();
        request.Dimensions.Geographies = Enumerable.Range(1, 21).Select(i => $"Geo{i}").ToList(); // 21 geographies

        // Act
        var result = _validator.Validate(request);

        // Assert
        Assert.False(result.IsValid);
        Assert.Contains(result.Errors, e => e.Code == ErrorCode.InsufficientFilters);
    }

    [Fact]
    public void Validate_WithValidTimeRangeOver90Days_ReturnsNoError()
    {
        // Arrange
        var request = CreateValidRequest();
        request.Dimensions.Brands = new List<string>(); // No brands
        request.Dimensions.Categories = new List<string>(); // No categories
        request.Dimensions.Geographies = new List<string>(); // No geographies
        // Set time range to > 90 days
        request.Aggregation.Period = new PeriodConfig
        {
            Start = new DateTime(2023, 1, 1),
            End = new DateTime(2024, 1, 1) // 366 days
        };

        // Act
        var result = _validator.Validate(request);

        // Assert
        Assert.True(result.IsValid);
    }

    [Fact]
    public void Validate_WithInsufficientFilters_ReturnsError()
    {
        // Arrange
        var request = CreateValidRequest();
        request.Dimensions.Brands = new List<string>();
        request.Dimensions.Categories = new List<string>();
        request.Dimensions.Geographies = new List<string>();
        // Time range < 90 days
        request.Aggregation.Period = new PeriodConfig
        {
            Start = new DateTime(2024, 1, 1),
            End = new DateTime(2024, 3, 1) // 60 days
        };

        // Act
        var result = _validator.Validate(request);

        // Assert
        Assert.False(result.IsValid);
        Assert.Contains(result.Errors, e => e.Code == ErrorCode.InsufficientFilters);
    }

    [Fact]
    public void Validate_WithExceedingLimit_ReturnsError()
    {
        // Arrange
        var request = CreateValidRequest();
        request.Pagination.Limit = 1001; // Over 1000

        // Act
        var result = _validator.Validate(request);

        // Assert
        Assert.False(result.IsValid);
        Assert.Contains(result.Errors, e => e.Code == ErrorCode.InsufficientFilters);
    }

    [Fact]
    public void Validate_WithInvalidMetric_ReturnsError()
    {
        // Arrange
        var request = CreateValidRequest();
        request.Aggregation.Metric = "invalid_metric";

        // Act
        var result = _validator.Validate(request);

        // Assert
        Assert.False(result.IsValid);
        Assert.Contains(result.Errors, e => e.Code == ErrorCode.InvalidDimensionValue);
    }

    private static QueryRequest CreateValidRequest()
    {
        return new QueryRequest
        {
            Tool = "market_share",
            Dimensions = new Dimensions
            {
                Brands = new List<string> { "Nike" },
                Categories = new List<string>(),
                Geographies = new List<string>(),
                Generations = new List<string>(),
                IncomeBands = new List<string>(),
                Channels = new List<string>(),
                DayOfWeek = new List<string>(),
                PaymentNetworks = new List<string>()
            },
            Aggregation = new AggregationConfig
            {
                Metric = "sum",
                Period = new PeriodConfig
                {
                    Start = new DateTime(2024, 1, 1),
                    End = new DateTime(2024, 12, 31)
                }
            },
            Pagination = new PaginationConfig
            {
                Limit = 100,
                Offset = 0
            }
        };
    }
}
