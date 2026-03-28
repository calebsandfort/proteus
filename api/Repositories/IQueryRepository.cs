using api.Models;

namespace api.Repositories;

public interface IQueryRepository
{
    Task<QueryResponse> ExecuteQueryAsync(QueryRequest request, string requestId, CancellationToken cancellationToken = default);
    Task<BatchQueryResponse> ExecuteBatchQueryAsync(BatchQueryRequest request, CancellationToken cancellationToken = default);
}
