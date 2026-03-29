"""Contract tests: Unit 2 (Synthetic Data Generator) ↔ Unit 3 (ASP.NET Core Data API)

These units integrate through the shared TimescaleDB database (IU-1).
Unit 2 writes panelist/transaction data; Unit 3 reads and queries it.
The database seed SQL is the source of truth for dimension values.

Contract tests verify dimension value alignment across:
  - DB seed SQL (frontend/drizzle/0011_seed_dimensions.sql)
  - Unit 2 Python constants (backend/src/data/)
  - Unit 3 YAML configs (api/config/dimensions/)
"""

import inspect
import re
from dataclasses import fields
from pathlib import Path

import yaml

# Project root: two levels up from this test file
PROJECT_ROOT = Path(__file__).resolve().parents[3]

SEED_SQL_PATH = PROJECT_ROOT / "frontend" / "drizzle" / "0011_seed_dimensions.sql"
YAML_DIMENSIONS_DIR = PROJECT_ROOT / "api" / "config" / "dimensions"


def parse_generation_ids_from_seed_sql() -> set[str]:
    """Extract generation IDs from the DB seed SQL INSERT statement."""
    sql = SEED_SQL_PATH.read_text()
    # Match: ('gen_z', 'Gen Z', 1997, 2012)
    return set(re.findall(r"INSERT INTO generations.*?;", sql, re.DOTALL)[0]
               and re.findall(r"\('([^']+)',\s*'[^']+',\s*\d+,\s*\d+\)", sql))


def parse_income_band_ids_from_seed_sql() -> set[str]:
    """Extract income band IDs from the DB seed SQL INSERT statement."""
    sql = SEED_SQL_PATH.read_text()
    # Match: ('under_25k', 'Under $25K', 0, 24999, 0.60)
    # IDs are the first single-quoted string on each VALUES row
    income_section = re.search(
        r"INSERT INTO income_bands.*?ON CONFLICT", sql, re.DOTALL
    )
    if not income_section:
        return set()
    return set(re.findall(r"\('([^']+)',\s*'[^']+',\s*\d+", income_section.group()))


def parse_yaml_dimension_ids(dimension_name: str) -> list[str]:
    """Parse IDs from a Unit 3 YAML dimension config file."""
    yaml_path = YAML_DIMENSIONS_DIR / f"{dimension_name}.yaml"
    with open(yaml_path) as f:
        entries = yaml.safe_load(f)
    return [entry["id"] for entry in entries]


# =============================================================================
# Category 1: Type/Value Compatibility — Unit 2 vs DB Seed
# =============================================================================


class TestUnit2DimensionAlignment:
    """Verify Unit 2 generated dimension values match DB seed data."""

    def test_unit2_generation_ids_match_db_seed(self):
        """Unit 2 panelist generator generation IDs must match DB seed generations."""
        from src.data.panelist_generator import DEFAULT_GENERATION_DISTRIBUTION

        db_generation_ids = parse_generation_ids_from_seed_sql()
        unit2_generation_ids = set(DEFAULT_GENERATION_DISTRIBUTION.keys())

        assert unit2_generation_ids.issubset(db_generation_ids), (
            f"Unit 2 generation IDs not in DB seed.\n"
            f"  Unit 2 has:  {sorted(unit2_generation_ids)}\n"
            f"  DB seed has: {sorted(db_generation_ids)}\n"
            f"  Missing from DB: {sorted(unit2_generation_ids - db_generation_ids)}"
        )

    def test_unit2_income_band_id_type_is_string(self):
        """Panelist.income_band_id must be str (DB schema uses varchar, not int)."""
        from src.data.panelist_generator import Panelist

        field_types = {f.name: f.type for f in fields(Panelist)}
        assert field_types["income_band_id"] is str or field_types["income_band_id"] == "str", (
            f"Panelist.income_band_id type is {field_types['income_band_id']}, "
            f"but DB schema uses varchar(20). Must be str."
        )

    def test_unit2_income_band_values_match_db_seed(self):
        """Unit 2 must generate income band IDs matching DB seed ('band_1'..'band_6')."""
        from src.data.panelist_generator import generate_panelists

        db_income_band_ids = parse_income_band_ids_from_seed_sql()
        panelists = generate_panelists(100, seed=42)
        unit2_income_band_ids = {str(p.income_band_id) for p in panelists}

        # Check that generated values are valid DB IDs
        invalid_ids = unit2_income_band_ids - db_income_band_ids
        assert not invalid_ids, (
            f"Unit 2 generates income band IDs not in DB seed.\n"
            f"  Generated: {sorted(unit2_income_band_ids)}\n"
            f"  DB seed:   {sorted(db_income_band_ids)}\n"
            f"  Invalid:   {sorted(invalid_ids)}"
        )

    def test_unit2_channel_values_consistent(self):
        """Unit 2 CHANNELS list must use underscore format matching DB conventions."""
        from src.data.transaction_generator import CHANNELS

        # DB/YAML convention uses underscores, not hyphens
        hyphenated = [ch for ch in CHANNELS if "-" in ch]
        assert not hyphenated, (
            f"Unit 2 CHANNELS uses hyphens instead of underscores: {hyphenated}\n"
            f"DB convention uses underscores (e.g., 'in_store' not 'in-store')"
        )


# =============================================================================
# Category 2: Cross-Language Dimension Compatibility — Unit 3 YAML vs DB Seed
# =============================================================================


class TestUnit3YamlDimensionAlignment:
    """Verify Unit 3 YAML dimension configs match DB seed data."""

    def test_unit3_yaml_generation_ids_match_db_seed(self):
        """Unit 3 generations.yaml IDs must match DB seed generation IDs."""
        db_generation_ids = parse_generation_ids_from_seed_sql()
        yaml_generation_ids = set(parse_yaml_dimension_ids("generations"))

        # YAML must at minimum contain all DB seed IDs
        missing_from_yaml = db_generation_ids - yaml_generation_ids
        assert not missing_from_yaml, (
            f"DB seed generation IDs missing from Unit 3 YAML.\n"
            f"  DB seed:       {sorted(db_generation_ids)}\n"
            f"  YAML has:      {sorted(yaml_generation_ids)}\n"
            f"  Missing:       {sorted(missing_from_yaml)}"
        )

        # YAML should not have IDs that don't exist in DB
        extra_in_yaml = yaml_generation_ids - db_generation_ids
        assert not extra_in_yaml, (
            f"Unit 3 YAML has generation IDs not in DB seed.\n"
            f"  DB seed:       {sorted(db_generation_ids)}\n"
            f"  YAML has:      {sorted(yaml_generation_ids)}\n"
            f"  Extra in YAML: {sorted(extra_in_yaml)}"
        )

    def test_unit3_yaml_income_band_ids_match_db_seed(self):
        """Unit 3 income-bands.yaml IDs must match DB seed income band IDs."""
        db_income_band_ids = parse_income_band_ids_from_seed_sql()
        yaml_income_band_ids = set(parse_yaml_dimension_ids("income-bands"))

        assert yaml_income_band_ids == db_income_band_ids, (
            f"Unit 3 YAML income band IDs don't match DB seed.\n"
            f"  DB seed:  {sorted(db_income_band_ids)}\n"
            f"  YAML has: {sorted(yaml_income_band_ids)}"
        )

    def test_unit3_yaml_income_band_count_matches_db_seed(self):
        """Unit 3 must have same number of income bands as DB seed (6)."""
        db_income_band_ids = parse_income_band_ids_from_seed_sql()
        yaml_income_band_ids = parse_yaml_dimension_ids("income-bands")

        assert len(yaml_income_band_ids) == len(db_income_band_ids), (
            f"Income band count mismatch: YAML has {len(yaml_income_band_ids)}, "
            f"DB seed has {len(db_income_band_ids)}.\n"
            f"  DB seed:  {sorted(db_income_band_ids)}\n"
            f"  YAML has: {sorted(yaml_income_band_ids)}"
        )


# =============================================================================
# Category 3: Import Resolution — Unit 2 Modules
# =============================================================================


class TestUnit2ImportResolution:
    """Verify Unit 2 data modules import without errors."""

    def test_panelist_generator_imports(self):
        """Panelist and generate_panelists must be importable."""
        from src.data.panelist_generator import Panelist, generate_panelists

        assert Panelist is not None
        assert generate_panelists is not None

    def test_transaction_generator_imports(self):
        """Transaction dataclass must be importable."""
        from src.data.transaction_generator import Transaction

        assert Transaction is not None

    def test_distributions_module_imports(self):
        """distributions module must be importable."""
        from src.data.distributions import generate_transaction_amount, sample_income_band

        assert generate_transaction_amount is not None
        assert sample_income_band is not None

    def test_seasonal_patterns_module_imports(self):
        """seasonal_patterns module must be importable."""
        from src.data.seasonal_patterns import apply_seasonal_adjustment

        assert apply_seasonal_adjustment is not None

    def test_validation_module_imports(self):
        """validation module must be importable."""
        from src.data.validation import generate_validation_report

        assert generate_validation_report is not None


# =============================================================================
# Category 4: Function Signature Tests
# =============================================================================


class TestUnit2FunctionSignatures:
    """Verify Unit 2 exported functions have expected signatures."""

    def test_generate_panelists_accepts_count_and_seed(self):
        """generate_panelists must accept count (int) and seed (int) parameters."""
        from src.data.panelist_generator import generate_panelists

        sig = inspect.signature(generate_panelists)
        params = list(sig.parameters.keys())
        assert "count" in params, f"Missing 'count' parameter. Found: {params}"
        assert "seed" in params, f"Missing 'seed' parameter. Found: {params}"

    def test_panelist_has_db_required_fields(self):
        """Panelist dataclass must have all fields matching DB panelists table columns."""
        from src.data.panelist_generator import Panelist

        field_names = {f.name for f in fields(Panelist)}
        required_fields = {
            "id",
            "income_band_id",
            "generation_id",
            "geography_id",
            "panel_start_date",
            "panel_weight",
        }
        missing = required_fields - field_names
        assert not missing, (
            f"Panelist dataclass missing DB-required fields: {sorted(missing)}\n"
            f"Has: {sorted(field_names)}"
        )

    def test_transaction_has_db_required_fields(self):
        """Transaction dataclass must have all fields matching DB transactions table columns."""
        from src.data.transaction_generator import Transaction

        field_names = {f.name for f in fields(Transaction)}
        required_fields = {
            "id",
            "panelist_id",
            "brand_id",
            "category_id",
            "geography_id",
            "generation_id",
            "income_band_id",
            "transaction_timestamp",
            "transaction_amount",
            "card_type",
            "payment_network",
            "channel",
            "day_of_week",
            "hour_of_day",
        }
        missing = required_fields - field_names
        assert not missing, (
            f"Transaction dataclass missing DB-required fields: {sorted(missing)}\n"
            f"Has: {sorted(field_names)}"
        )

    def test_generate_panelists_returns_list(self):
        """generate_panelists must return a list of Panelist objects."""
        from src.data.panelist_generator import Panelist, generate_panelists

        result = generate_panelists(5, seed=42)
        assert isinstance(result, list), f"Expected list, got {type(result)}"
        assert len(result) == 5
        assert all(isinstance(p, Panelist) for p in result)
