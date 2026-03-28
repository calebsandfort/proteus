using YamlDotNet.Serialization;
using YamlDotNet.Serialization.NamingConventions;
using api.Models;

namespace api.Services;

public interface IDimensionCacheService
{
    Task<DimensionValuesResponse?> GetDimensionValuesAsync(string dimension, CancellationToken cancellationToken = default);
    IReadOnlyList<string> GetAvailableDimensions();
}

public class DimensionCacheService : IDimensionCacheService
{
    private readonly Dictionary<string, DimensionValuesResponse> _cache = new();
    private readonly string _configPath;
    private readonly TimeSpan _cacheDuration = TimeSpan.FromHours(24);
    private readonly SemaphoreSlim _loadLock = new(1, 1);
    private bool _initialized = false;

    private static readonly HashSet<string> ValidDimensions = new(StringComparer.OrdinalIgnoreCase)
    {
        "brands", "categories", "states", "generations", "income-bands", "channels", "day-of-week", "payment-networks"
    };

    public DimensionCacheService(string configPath)
    {
        _configPath = configPath;
    }

    public IReadOnlyList<string> GetAvailableDimensions() => ValidDimensions.ToList();

    public async Task<DimensionValuesResponse?> GetDimensionValuesAsync(string dimension, CancellationToken cancellationToken = default)
    {
        var normalizedDimension = dimension.ToLowerInvariant().Replace("_", "-");

        if (!ValidDimensions.Contains(normalizedDimension))
        {
            return null;
        }

        await EnsureInitializedAsync(cancellationToken);

        return _cache.TryGetValue(normalizedDimension, out var response) ? response : null;
    }

    private async Task EnsureInitializedAsync(CancellationToken cancellationToken)
    {
        if (_initialized)
        {
            return;
        }

        await _loadLock.WaitAsync(cancellationToken);
        try
        {
            if (_initialized)
            {
                return;
            }

            await LoadAllDimensionsAsync(cancellationToken);
            _initialized = true;
        }
        finally
        {
            _loadLock.Release();
        }
    }

    private async Task LoadAllDimensionsAsync(CancellationToken cancellationToken)
    {
        foreach (var dimension in ValidDimensions)
        {
            var filePath = Path.Combine(_configPath, $"{dimension}.yaml");

            if (!File.Exists(filePath))
            {
                // Create default/empty cache entry for dimensions without YAML files
                _cache[dimension] = new DimensionValuesResponse
                {
                    Dimension = dimension,
                    Values = new List<DimensionValue>(),
                    CachedAt = DateTime.UtcNow,
                    CacheExpiresAt = DateTime.UtcNow.Add(_cacheDuration)
                };
                continue;
            }

            try
            {
                var yaml = await File.ReadAllTextAsync(filePath, cancellationToken);
                var deserializer = new DeserializerBuilder()
                    .WithNamingConvention(UnderscoredNamingConvention.Instance)
                    .Build();

                var values = deserializer.Deserialize<List<DimensionValue>>(yaml) ?? new List<DimensionValue>();

                _cache[dimension] = new DimensionValuesResponse
                {
                    Dimension = dimension,
                    Values = values,
                    CachedAt = DateTime.UtcNow,
                    CacheExpiresAt = DateTime.UtcNow.Add(_cacheDuration)
                };
            }
            catch (Exception)
            {
                // Log error in production, continue with empty cache for this dimension
                _cache[dimension] = new DimensionValuesResponse
                {
                    Dimension = dimension,
                    Values = new List<DimensionValue>(),
                    CachedAt = DateTime.UtcNow,
                    CacheExpiresAt = DateTime.UtcNow.Add(_cacheDuration)
                };
            }
        }
    }
}
