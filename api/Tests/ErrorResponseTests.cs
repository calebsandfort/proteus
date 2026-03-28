using Xunit;
using api.Models;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace api.Tests;

public class ErrorResponseTests
{
    private static readonly JsonSerializerOptions JsonOptions = new()
    {
        Converters = { new JsonStringEnumConverter(new ScreamingSnakeCaseJsonNamingPolicy()) }
    };

    [Fact]
    public void ErrorResponse_ContainsAllRequiredFields()
    {
        // Arrange
        var errorResponse = new ErrorResponse(
            requestId: "test-uuid-123",
            error: ErrorCode.MissingRequiredDimension,
            message: "A required dimension is missing",
            suggestions: new List<string> { "Add a brand filter", "Add a category filter" },
            retryAfter: null
        );

        // Assert
        Assert.Equal("test-uuid-123", errorResponse.RequestId);
        Assert.Equal(ErrorCode.MissingRequiredDimension, errorResponse.Error);
        Assert.Equal("A required dimension is missing", errorResponse.Message);
        Assert.Equal(2, errorResponse.Suggestions.Count);
        Assert.Null(errorResponse.RetryAfter);
    }

    [Fact]
    public void ErrorResponse_WithRetryAfter()
    {
        // Arrange
        var errorResponse = new ErrorResponse(
            requestId: "test-uuid-456",
            error: ErrorCode.RateLimitExceeded,
            message: "Rate limit exceeded",
            suggestions: new List<string> { "Wait before retrying" },
            retryAfter: 60
        );

        // Assert
        Assert.Equal(60, errorResponse.RetryAfter);
    }

    [Theory]
    [InlineData(ErrorCode.MissingRequiredDimension, "MISSING_REQUIRED_DIMENSION")]
    [InlineData(ErrorCode.InvalidDimensionValue, "INVALID_DIMENSION_VALUE")]
    [InlineData(ErrorCode.InsufficientFilters, "INSUFFICIENT_FILTERS")]
    [InlineData(ErrorCode.QueryTimeout, "QUERY_TIMEOUT")]
    [InlineData(ErrorCode.RateLimitExceeded, "RATE_LIMIT_EXCEEDED")]
    [InlineData(ErrorCode.DatabaseUnavailable, "DATABASE_UNAVAILABLE")]
    [InlineData(ErrorCode.InternalError, "INTERNAL_ERROR")]
    public void ErrorCode_HasCorrectStringValue(ErrorCode code, string expected)
    {
        // Act
        var serialized = JsonSerializer.Serialize(code, JsonOptions);

        // Assert
        Assert.Equal($"\"{expected}\"", serialized);
    }
}
