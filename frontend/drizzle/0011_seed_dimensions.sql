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
    ('under_25k',  'Under $25K',          0,       24999,  0.60),
    ('25k_50k',    '$25K-$50K',       25000,       49999,  0.80),
    ('50k_75k',    '$50K-$75K',       50000,       74999,  1.00),
    ('75k_100k',   '$75K-$100K',      75000,       99999,  1.20),
    ('100k_150k',  '$100K-$150K',    100000,      149999,  1.40),
    ('150k_200k',  '$150K-$200K',    150000,      199999,  1.55),
    ('over_200k',  '$200K+',         200000,        NULL,  1.70)
ON CONFLICT (id) DO UPDATE SET
    name = EXCLUDED.name,
    min_income = EXCLUDED.min_income,
    max_income = EXCLUDED.max_income,
    income_multiplier = EXCLUDED.income_multiplier;
