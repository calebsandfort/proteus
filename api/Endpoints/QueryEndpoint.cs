using api.Models;
using api.Repositories;
using api.Services;
using api.Validators;

namespace api.Endpoints;

public static class QueryEndpoint
{
    public static async Task<IResult> Handle(
        QueryRequest request,
        IQueryRepository repository,
        QueryGuardrailValidator guardrailValidator,
        AggregationLevelResolver aggregationLevelResolver,
        HttpContext httpContext,
        CancellationToken cancellationToken)
    {
        var requestId = httpContext.TraceIdentifier;

        // Validate guardrails
        var validationResult = guardrailValidator.Validate(request);
        if (!validationResult.IsValid)
        {
            var firstError = validationResult.Errors.First();
            var errorResponse = new ErrorResponse(
                requestId,
                firstError.Code,
                firstError.Message,
                new List<string> { "Review the request parameters and try again" }
            );
            return Results.BadRequest(errorResponse);
        }

        try
        {
            var response = await repository.ExecuteQueryAsync(request, requestId, cancellationToken);

            // Ensure request_id is set in metadata
            if (string.IsNullOrEmpty(response.Metadata.RequestId))
            {
                response.Metadata.RequestId = requestId;
            }

            return Results.Ok(response);
        }
        catch (OperationCanceledException)
        {
            return Results.BadRequest(new ErrorResponse(
                requestId,
                ErrorCode.QueryTimeout,
                "The request was cancelled",
                new List<string> { "Retry the request" }
            ));
        }
    }
}
