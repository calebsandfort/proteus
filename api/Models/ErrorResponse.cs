using System.Text.Json.Serialization;
using System.Text.Json;

namespace api.Models;

/// <summary>
/// Custom JSON naming policy that converts enum values to SCREAMING_SNAKE_CASE.
/// </summary>
public class ScreamingSnakeCaseJsonNamingPolicy : JsonNamingPolicy
{
    public override string ConvertName(string name)
    {
        // Convert CamelCase to SCREAMING_SNAKE_CASE
        // e.g., "MissingRequiredDimension" -> "MISSING_REQUIRED_DIMENSION"
        var result = new System.Text.StringBuilder();
        for (int i = 0; i < name.Length; i++)
        {
            char c = name[i];
            if (char.IsUpper(c) && i > 0)
            {
                result.Append('_');
            }
            result.Append(char.ToUpperInvariant(c));
        }
        return result.ToString();
    }
}

public class ErrorResponse
{
    [JsonPropertyName("request_id")]
    public string RequestId { get; set; }

    [JsonPropertyName("error")]
    public ErrorCode Error { get; set; }

    [JsonPropertyName("message")]
    public string Message { get; set; }

    [JsonPropertyName("suggestions")]
    public List<string> Suggestions { get; set; }

    [JsonPropertyName("retry_after")]
    public int? RetryAfter { get; set; }

    public ErrorResponse(string requestId, ErrorCode error, string message, List<string> suggestions, int? retryAfter = null)
    {
        RequestId = requestId;
        Error = error;
        Message = message;
        Suggestions = suggestions;
        RetryAfter = retryAfter;
    }
}

public enum ErrorCode
{
    MissingRequiredDimension,
    InvalidDimensionValue,
    InsufficientFilters,
    QueryTimeout,
    RateLimitExceeded,
    DatabaseUnavailable,
    InternalError
}

public class ValidationError
{
    public ErrorCode Code { get; set; }
    public string Message { get; set; }
    public string? Field { get; set; }

    public ValidationError(ErrorCode code, string message, string? field = null)
    {
        Code = code;
        Message = message;
        Field = field;
    }
}

public class ValidationResult
{
    public bool IsValid => Errors.Count == 0;
    public List<ValidationError> Errors { get; set; } = new();

    public void AddError(ErrorCode code, string message, string? field = null)
    {
        Errors.Add(new ValidationError(code, message, field));
    }
}
