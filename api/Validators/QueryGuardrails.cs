using api.Models;

namespace api.Validators;

public class QueryGuardrailValidator
{
    private static readonly HashSet<string> ValidMetrics = new(StringComparer.OrdinalIgnoreCase)
    {
        "sum", "avg", "count", "min", "max", "median"
    };

    private const int MinBrands = 1;
    private const int MaxBrands = 50;
    private const int MaxCategories = 10;
    private const int MaxGeographies = 20;
    private const int MinTimeRangeDays = 90;
    private const int MaxLimit = 1000;

    public ValidationResult Validate(QueryRequest request)
    {
        var result = new ValidationResult();

        ValidateMetric(request.Aggregation.Metric, result);
        ValidateHighCardinalityFilters(request, result);
        ValidatePaginationLimit(request.Pagination.Limit, result);

        return result;
    }

    private void ValidateMetric(string metric, ValidationResult result)
    {
        if (!ValidMetrics.Contains(metric))
        {
            result.AddError(
                ErrorCode.InvalidDimensionValue,
                $"Invalid metric '{metric}'. Valid values are: {string.Join(", ", ValidMetrics)}",
                "aggregation.metric"
            );
        }
    }

    private void ValidateHighCardinalityFilters(QueryRequest request, ValidationResult result)
    {
        var brandsCount = request.Dimensions.Brands.Count;
        var categoriesCount = request.Dimensions.Categories.Count;
        var geographiesCount = request.Dimensions.Geographies.Count;
        var timeRangeDays = request.Aggregation.Period.TotalDays;

        // Check brand constraints
        if (brandsCount > 0)
        {
            if (brandsCount < MinBrands || brandsCount > MaxBrands)
            {
                result.AddError(
                    ErrorCode.InsufficientFilters,
                    $"Brand filter must have between {MinBrands} and {MaxBrands} brands. Got {brandsCount}.",
                    "dimensions.brands"
                );
            }
        }

        // Check category constraints
        if (categoriesCount > MaxCategories)
        {
            result.AddError(
                ErrorCode.InsufficientFilters,
                $"Category filter must have at most {MaxCategories} categories. Got {categoriesCount}.",
                "dimensions.categories"
            );
        }

        // Check geography constraints
        if (geographiesCount > MaxGeographies)
        {
            result.AddError(
                ErrorCode.InsufficientFilters,
                $"Geography filter must have at most {MaxGeographies} geographies. Got {geographiesCount}.",
                "dimensions.geographies"
            );
        }

        // Require at least one high-cardinality filter OR 90+ day time range
        var hasValidHighCardinalityFilter =
            (brandsCount >= MinBrands && brandsCount <= MaxBrands) ||
            (categoriesCount >= MinBrands && categoriesCount <= MaxCategories) ||
            (geographiesCount >= MinBrands && geographiesCount <= MaxGeographies);

        var hasValidTimeRange = timeRangeDays >= MinTimeRangeDays;

        if (!hasValidHighCardinalityFilter && !hasValidTimeRange)
        {
            result.AddError(
                ErrorCode.InsufficientFilters,
                $"Query must have at least one high-cardinality dimension filter (1-{MaxBrands} brands, 1-{MaxCategories} categories, or 1-{MaxGeographies} geographies) OR a time range of {MinTimeRangeDays}+ days. " +
                $"Got {brandsCount} brands, {categoriesCount} categories, {geographiesCount} geographies, and {timeRangeDays} days.",
                "dimensions"
            );
        }
    }

    private void ValidatePaginationLimit(int limit, ValidationResult result)
    {
        if (limit > MaxLimit)
        {
            result.AddError(
                ErrorCode.InsufficientFilters,
                $"Pagination limit cannot exceed {MaxLimit}. Got {limit}.",
                "pagination.limit"
            );
        }

        if (limit < 1)
        {
            result.AddError(
                ErrorCode.InsufficientFilters,
                $"Pagination limit must be at least 1. Got {limit}.",
                "pagination.limit"
            );
        }
    }
}
