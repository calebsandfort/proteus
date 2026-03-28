using System.Net;
using System.Text.Json;
using api.Models;

namespace api.Middleware;

public class ErrorHandlingMiddleware
{
    private readonly RequestDelegate _next;
    private readonly ILogger<ErrorHandlingMiddleware> _logger;

    public ErrorHandlingMiddleware(RequestDelegate next, ILogger<ErrorHandlingMiddleware> logger)
    {
        _next = next;
        _logger = logger;
    }

    public async Task InvokeAsync(HttpContext context)
    {
        try
        {
            await _next(context);
        }
        catch (OperationCanceledException)
        {
            // Request was cancelled (e.g., client disconnected)
            _logger.LogInformation("Request was cancelled");
            // Don't write response for cancelled requests
        }
        catch (Exception ex)
        {
            await HandleExceptionAsync(context, ex);
        }
    }

    private async Task HandleExceptionAsync(HttpContext context, Exception exception)
    {
        var requestId = context.TraceIdentifier;

        var (statusCode, errorCode, message, suggestions, retryAfter) = exception switch
        {
            TimeoutException => (
                HttpStatusCode.GatewayTimeout,
                ErrorCode.QueryTimeout,
                "The query timed out. Please try with a smaller time range or fewer dimensions.",
                new List<string> { "Reduce the time range", "Use fewer dimension filters", "Increase pagination offset" },
                (int?)30
            ),
            InvalidOperationException ex when ex.Message.Contains("database", StringComparison.OrdinalIgnoreCase) => (
                HttpStatusCode.ServiceUnavailable,
                ErrorCode.DatabaseUnavailable,
                "The database is currently unavailable. Please try again later.",
                new List<string> { "Wait a few minutes and retry", "Contact support if the issue persists" },
                (int?)60
            ),
            ArgumentException => (
                HttpStatusCode.BadRequest,
                ErrorCode.InvalidDimensionValue,
                exception.Message,
                new List<string> { "Check the request parameters" },
                (int?)null
            ),
            _ => (
                HttpStatusCode.InternalServerError,
                ErrorCode.InternalError,
                "An internal error occurred. Please try again later.",
                new List<string> { "Retry the request", "Contact support if the issue persists" },
                (int?)null
            )
        };

        _logger.LogError(exception, "Request {RequestId} failed with {ErrorCode}: {Message}",
            requestId, errorCode, exception.Message);

        var errorResponse = new ErrorResponse(
            requestId,
            errorCode,
            message,
            suggestions,
            retryAfter
        );

        context.Response.StatusCode = (int)statusCode;
        context.Response.ContentType = "application/json";

        var json = JsonSerializer.Serialize(errorResponse, new JsonSerializerOptions
        {
            PropertyNamingPolicy = JsonNamingPolicy.CamelCase
        });

        await context.Response.WriteAsync(json);
    }
}

public static class ErrorHandlingMiddlewareExtensions
{
    public static IApplicationBuilder UseErrorHandling(this IApplicationBuilder app)
    {
        return app.UseMiddleware<ErrorHandlingMiddleware>();
    }
}
