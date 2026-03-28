using api.Models;

namespace api.Services;

public class AggregationLevelResolver
{
    public AggregationLevel Resolve(DateTime start, DateTime end)
    {
        var totalDays = (end - start).Days;

        return totalDays switch
        {
            <= 14 => AggregationLevel.Daily,      // 1-14 days -> daily
            <= 90 => AggregationLevel.Weekly,     // 15-90 days -> weekly
            <= 365 => AggregationLevel.Monthly,  // 91-365 days -> monthly
            <= 730 => AggregationLevel.Quarterly, // 1-2 years -> quarterly
            _ => AggregationLevel.Annual          // 2+ years -> annual
        };
    }

    public AggregationLevel Resolve(PeriodConfig period)
    {
        return Resolve(period.Start, period.End);
    }
}
