using api.Models;
using api.Repositories;
using api.Validators;

namespace api.Endpoints;

public static class BatchQueryEndpoint
{
    public static async Task<IResult> Handle(
        BatchQueryRequest request,
        IQueryRepository repository,
        QueryGuardrailValidator guardrailValidator,
        HttpContext httpContext,
        CancellationToken cancellationToken)
    {
        var requestId = httpContext.TraceIdentifier;

        if (request.Queries == null || request.Queries.Count == 0)
        {
            return Results.BadRequest(new ErrorResponse(
                requestId,
                ErrorCode.InvalidDimensionValue,
                "At least one query is required",
                new List<string> { "Provide at least one query in the queries array" }
            ));
        }

        // Validate all queries
        var validationErrors = new List<(int QueryIndex, ValidationError Error)>();
        for (var i = 0; i < request.Queries.Count; i++)
        {
            var validationResult = guardrailValidator.Validate(request.Queries[i]);
            if (!validationResult.IsValid)
            {
                foreach (var error in validationResult.Errors)
                {
                    validationErrors.Add((i, error));
                }
            }
        }

        if (validationErrors.Count > 0)
        {
            var firstError = validationErrors.First();
            var errorResponse = new ErrorResponse(
                requestId,
                firstError.Error.Code,
                $"Query[{firstError.QueryIndex}]: {firstError.Error.Message}",
                new List<string> { "Review all queries and ensure they meet guardrail requirements" }
            );
            return Results.BadRequest(errorResponse);
        }

        try
        {
            var response = await repository.ExecuteBatchQueryAsync(request, cancellationToken);
            return Results.Ok(response);
        }
        catch (OperationCanceledException)
        {
            return Results.BadRequest(new ErrorResponse(
                requestId,
                ErrorCode.QueryTimeout,
                "The batch request was cancelled",
                new List<string> { "Retry the request" }
            ));
        }
    }
}
