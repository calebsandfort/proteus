using api.Models;
using api.Services;

namespace api.Endpoints;

public static class DimensionEndpoints
{
    public static async Task<IResult> Handle(
        string dimension,
        IDimensionCacheService cacheService,
        HttpContext httpContext,
        CancellationToken cancellationToken)
    {
        var requestId = httpContext.TraceIdentifier;

        var values = await cacheService.GetDimensionValuesAsync(dimension, cancellationToken);

        if (values == null)
        {
            var availableDimensions = cacheService.GetAvailableDimensions();
            var errorResponse = new ErrorResponse(
                requestId,
                ErrorCode.InvalidDimensionValue,
                $"Invalid dimension '{dimension}'. Available dimensions are: {string.Join(", ", availableDimensions)}",
                new List<string> { $"Use one of the available dimensions: {string.Join(", ", availableDimensions)}" }
            );
            return Results.BadRequest(errorResponse);
        }

        return Results.Ok(values);
    }
}
