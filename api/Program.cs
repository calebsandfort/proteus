using Dapper;
using Npgsql;
using api.Repositories;
using api.Services;
using api.Validators;
using api.Endpoints;
using api.Middleware;

var builder = WebApplication.CreateBuilder(args);

// Register services
builder.Services.AddSingleton<TimescaleRepository>();
builder.Services.AddSingleton<AggregationLevelResolver>();
builder.Services.AddSingleton<QueryGuardrailValidator>();
builder.Services.AddSingleton<IQueryRepository, QueryRepository>();

// Register dimension cache service
var configPath = Path.Combine(builder.Environment.ContentRootPath, "config", "dimensions");
builder.Services.AddSingleton<IDimensionCacheService>(new DimensionCacheService(configPath));

var app = builder.Build();

// Configure middleware pipeline
app.UseErrorHandling();

// Health check endpoint
app.MapGet("/health", () => Results.Ok(new { status = "healthy" }));

// Root endpoint
app.MapGet("/", () => Results.Ok(new { message = "ASP.NET Core API is running" }));

// Example TimescaleDB query endpoint
app.MapGet("/api/timescale/example", async (TimescaleRepository repo) =>
{
    var result = await repo.QueryAsync<dynamic>(
        @"SELECT time_bucket('1 hour', now()) AS bucket,
                 count(*) AS count
          FROM generate_series(now() - interval '24 hours', now(), interval '1 hour') AS t");
    return Results.Ok(result);
});

// POST /api/query endpoint
app.MapPost("/api/query", QueryEndpoint.Handle);

// POST /api/query/batch endpoint
app.MapPost("/api/query/batch", BatchQueryEndpoint.Handle);

// GET /api/dimensions/{dimension} endpoint
app.MapGet("/api/dimensions/{dimension}", DimensionEndpoints.Handle);

app.Run();
