-- Migration 0011: Seed dimension data
-- Unit 1: Database Infrastructure
-- FR Coverage: FR-6.3, FR-6.6, FR-6.7

-- ============================================================================
-- GENERATIONS SEED DATA
-- FR-6.7: Generational preferences
-- ============================================================================

INSERT INTO generations (id, name, birth_year_start, birth_year_end) VALUES
    ('gen_z', 'Gen Z', 1997, 2012),
    ('millennial', 'Millennials', 1981, 1996),
    ('gen_x', 'Gen X', 1965, 1980),
    ('baby_boomer', 'Baby Boomers', 1946, 1964),
    ('silent', 'Silent Generation', 1928, 1945)
ON CONFLICT (id) DO UPDATE SET
    name = EXCLUDED.name,
    birth_year_start = EXCLUDED.birth_year_start,
    birth_year_end = EXCLUDED.birth_year_end;

-- ============================================================================
-- INCOME BANDS SEED DATA
-- FR-6.6: Income multipliers
-- ============================================================================

INSERT INTO income_bands (id, name, min_income, max_income, income_multiplier) VALUES
    ('band_1', 'Under $25K', 0, 24999, 0.60),
    ('band_2', '$25K-$40K', 25000, 39999, 0.75),
    ('band_3', '$40K-$60K', 40000, 59999, 0.90),
    ('band_4', '$60K-$85K', 60000, 84999, 1.00),
    ('band_5', '$85K-$150K', 85000, 149999, 1.30),
    ('band_6', '$150K+', 150000, NULL, 1.70)
ON CONFLICT (id) DO UPDATE SET
    name = EXCLUDED.name,
    min_income = EXCLUDED.min_income,
    max_income = EXCLUDED.max_income,
    income_multiplier = EXCLUDED.income_multiplier;
