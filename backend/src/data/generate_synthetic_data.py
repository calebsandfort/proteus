"""Synthetic data generation orchestrator.

Seeds reference tables (geography, categories, brands) then generates panelists
and transactions using the Unit 2 generator modules.

Usage:
    cd backend
    uv run python -m src.data.generate_synthetic_data

Environment variables (can be set in .env):
    DATABASE_URL     PostgreSQL connection string
    PANELIST_COUNT   Number of panelists to generate (default: 10000)
    SEED             Random seed for reproducibility (default: 42)
    START_DATE       Transaction start date YYYY-MM-DD (default: 2024-01-01)
    END_DATE         Transaction end date YYYY-MM-DD (default: 2025-12-31)
    BATCH_SIZE       Panelist batch insert size (default: 1000)
    TXN_BATCH_SIZE   Transaction batch insert size (default: 5000)
"""

import os
import sys
from datetime import date, datetime
from typing import Dict, List

import psycopg
from dotenv import load_dotenv

from src.data.panelist_generator import generate_panelists
from src.data.transaction_generator import generate_transactions_for_panelist
from src.data.validation import generate_validation_report

load_dotenv()

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/proteus")
PANELIST_COUNT = int(os.getenv("PANELIST_COUNT", "10000"))
SEED = int(os.getenv("SEED", "42"))
START_DATE = date.fromisoformat(os.getenv("START_DATE", "2024-01-01"))
END_DATE = date.fromisoformat(os.getenv("END_DATE", "2025-12-31"))
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "1000"))
TXN_BATCH_SIZE = int(os.getenv("TXN_BATCH_SIZE", "5000"))

# ---------------------------------------------------------------------------
# Reference seed data
# ---------------------------------------------------------------------------

# 4 geographic regions matching panelist_generator.DEFAULT_GEOGRAPHY_DISTRIBUTION IDs 1-4
GEOGRAPHY_SEED = [
    {"id": 1, "state_code": "NE", "state_name": "Northeast Region", "urban_class": "region"},
    {"id": 2, "state_code": "MW", "state_name": "Midwest Region",   "urban_class": "region"},
    {"id": 3, "state_code": "SO", "state_name": "South Region",     "urban_class": "region"},
    {"id": 4, "state_code": "WE", "state_name": "West Region",      "urban_class": "region"},
]

# Categories keyed by their canonical name (matches seasonal_patterns.py constants)
CATEGORY_SEED = [
    {"level1": "retail",           "level2": "General Merchandise", "level3": ""},
    {"level1": "grocery",          "level2": "Food & Beverage",     "level3": ""},
    {"level1": "dining",           "level2": "Food & Beverage",     "level3": "Sit-Down"},
    {"level1": "apparel",          "level2": "Clothing",            "level3": ""},
    {"level1": "healthcare",       "level2": "Health & Wellness",   "level3": ""},
    {"level1": "travel",           "level2": "Hospitality",         "level3": ""},
    {"level1": "home_improvement", "level2": "Home & Garden",       "level3": ""},
    {"level1": "school",           "level2": "Education",           "level3": "Supplies"},
    {"level1": "fast_food",        "level2": "Food & Beverage",     "level3": "Quick Service"},
]

# Brands: tier must match CATEGORY_PARAMS keys in distributions.py
# category_name maps each brand to one of the category level1 values above
BRAND_SEED = [
    # retail
    {"name": "Walmart",          "tier": "walmart",   "archetype": "mass_market",   "category_name": "retail"},
    {"name": "Target",           "tier": "mid_tier",  "archetype": "mass_market",   "category_name": "retail"},
    {"name": "Dollar Tree",      "tier": "value",     "archetype": "discount",      "category_name": "retail"},
    {"name": "Dollar General",   "tier": "value",     "archetype": "discount",      "category_name": "retail"},
    {"name": "Costco",           "tier": "mid_tier",  "archetype": "warehouse",     "category_name": "retail"},
    # grocery
    {"name": "Kroger",           "tier": "essential", "archetype": "supermarket",   "category_name": "grocery"},
    {"name": "Safeway",          "tier": "essential", "archetype": "supermarket",   "category_name": "grocery"},
    {"name": "Whole Foods",      "tier": "premium",   "archetype": "natural_foods", "category_name": "grocery"},
    {"name": "Trader Joe's",     "tier": "mid_tier",  "archetype": "specialty",     "category_name": "grocery"},
    # dining
    {"name": "Olive Garden",     "tier": "dining",    "archetype": "casual_dining", "category_name": "dining"},
    {"name": "Cheesecake Factory","tier": "dining",   "archetype": "casual_dining", "category_name": "dining"},
    {"name": "Texas Roadhouse",  "tier": "dining",    "archetype": "casual_dining", "category_name": "dining"},
    # fast food
    {"name": "McDonald's",       "tier": "fast_food", "archetype": "qsr",           "category_name": "fast_food"},
    {"name": "Starbucks",        "tier": "fast_food", "archetype": "qsr",           "category_name": "fast_food"},
    {"name": "Chick-fil-A",      "tier": "fast_food", "archetype": "qsr",           "category_name": "fast_food"},
    {"name": "Chipotle",         "tier": "fast_food", "archetype": "fast_casual",   "category_name": "fast_food"},
    # apparel
    {"name": "Gap",              "tier": "mid_tier",  "archetype": "specialty",     "category_name": "apparel"},
    {"name": "H&M",              "tier": "value",     "archetype": "fast_fashion",  "category_name": "apparel"},
    {"name": "Nordstrom",        "tier": "premium",   "archetype": "department",    "category_name": "apparel"},
    {"name": "Neiman Marcus",    "tier": "luxury",    "archetype": "luxury_dept",   "category_name": "apparel"},
    {"name": "Louis Vuitton",    "tier": "luxury",    "archetype": "luxury_brand",  "category_name": "apparel"},
    # healthcare
    {"name": "CVS",              "tier": "essential", "archetype": "pharmacy",      "category_name": "healthcare"},
    {"name": "Walgreens",        "tier": "essential", "archetype": "pharmacy",      "category_name": "healthcare"},
    # travel
    {"name": "Marriott",         "tier": "premium",   "archetype": "hotel_chain",   "category_name": "travel"},
    {"name": "Hilton",           "tier": "mid_tier",  "archetype": "hotel_chain",   "category_name": "travel"},
    # home improvement
    {"name": "Home Depot",       "tier": "mid_tier",  "archetype": "home_improvement", "category_name": "home_improvement"},
    {"name": "Lowe's",           "tier": "mid_tier",  "archetype": "home_improvement", "category_name": "home_improvement"},
    # school / electronics
    {"name": "Staples",          "tier": "mid_tier",  "archetype": "office_supply", "category_name": "school"},
    {"name": "Best Buy",         "tier": "mid_tier",  "archetype": "electronics",   "category_name": "school"},
]


# ---------------------------------------------------------------------------
# Seeding helpers
# ---------------------------------------------------------------------------

def _seed_geography(cur: psycopg.Cursor) -> None:
    cur.execute("SELECT COUNT(*) FROM geography")
    if cur.fetchone()[0] > 0:
        print("  geography: already seeded, skipping")
        return
    cur.executemany(
        """
        INSERT INTO geography (id, state_code, state_name, urban_class)
        VALUES (%(id)s, %(state_code)s, %(state_name)s, %(urban_class)s)
        ON CONFLICT (id) DO NOTHING
        """,
        GEOGRAPHY_SEED,
    )
    print(f"  geography: inserted {len(GEOGRAPHY_SEED)} rows")


def _seed_categories(cur: psycopg.Cursor) -> Dict[str, int]:
    """Seed categories and return {level1: id} mapping."""
    cur.execute("SELECT COUNT(*) FROM categories")
    if cur.fetchone()[0] == 0:
        cur.executemany(
            """
            INSERT INTO categories (level1, level2, level3)
            VALUES (%(level1)s, %(level2)s, %(level3)s)
            """,
            CATEGORY_SEED,
        )
        print(f"  categories: inserted {len(CATEGORY_SEED)} rows")
    else:
        print("  categories: already seeded, skipping")

    cur.execute("SELECT id, level1 FROM categories")
    return {row[1]: row[0] for row in cur.fetchall()}


def _seed_brands(cur: psycopg.Cursor, category_map: Dict[str, int]) -> List[Dict]:
    """Seed brands and return list of brand dicts with id + category_id."""
    cur.execute("SELECT COUNT(*) FROM brands")
    if cur.fetchone()[0] == 0:
        for brand in BRAND_SEED:
            cur.execute(
                """
                INSERT INTO brands (name, tier, archetype)
                VALUES (%s, %s, %s)
                RETURNING id
                """,
                (brand["name"], brand["tier"], brand["archetype"]),
            )
            brand["id"] = cur.fetchone()[0]
        print(f"  brands: inserted {len(BRAND_SEED)} rows")
    else:
        print("  brands: already seeded, skipping")
        cur.execute("SELECT id, name, tier, archetype FROM brands")
        rows = cur.fetchall()
        # Match existing DB rows back to BRAND_SEED to get category_name
        name_to_category = {b["name"]: b["category_name"] for b in BRAND_SEED}
        for row in rows:
            brand_id, name, tier, archetype = row
            # Find matching seed entry or fall back to "retail"
            category_name = name_to_category.get(name, "retail")
            BRAND_SEED.append({
                "id": brand_id,
                "name": name,
                "tier": tier,
                "archetype": archetype,
                "category_name": category_name,
            })
        # Remove original seed entries (they lack "id")
        return [b for b in BRAND_SEED if "id" in b]

    return BRAND_SEED


def _build_brand_list(brands: List[Dict], category_map: Dict[str, int]) -> List[Dict]:
    """Convert brand seed entries to dicts compatible with transaction_generator."""
    result = []
    for brand in brands:
        cat_name = brand.get("category_name", "retail")
        cat_id = category_map.get(cat_name, category_map.get("retail", 1))
        result.append({
            "id": brand["id"],
            "brand_id": brand["id"],
            "tier": brand["tier"],
            "brand_tier": brand["tier"],
            "category_id": cat_id,
            "category": cat_id,
            "name": brand["name"],
        })
    return result


def _build_category_list(category_map: Dict[str, int]) -> List[Dict]:
    """Build category list with category_name key for transaction_generator."""
    return [{"id": cat_id, "category_id": cat_id, "category_name": cat_name}
            for cat_name, cat_id in category_map.items()]


def _build_geography_lookup() -> Dict[int, str]:
    return {
        1: "Northeast",
        2: "Midwest",
        3: "South",
        4: "West",
    }


# ---------------------------------------------------------------------------
# Insertion helpers
# ---------------------------------------------------------------------------

def _insert_panelists(cur: psycopg.Cursor, panelists: list) -> None:
    rows = [
        (
            p.id,
            p.income_band_id,
            p.generation_id,
            p.geography_id,
            p.panel_start_date,
            float(p.panel_weight),
        )
        for p in panelists
    ]
    cur.executemany(
        """
        INSERT INTO panelists (id, income_band_id, generation_id, geography_id,
                               panel_start_date, panel_weight)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (id) DO NOTHING
        """,
        rows,
    )


def _insert_transactions(cur: psycopg.Cursor, transactions: list) -> None:
    rows = [
        (
            t.id,
            t.transaction_timestamp,
            t.panelist_id,
            t.brand_id,
            t.category_id,
            t.geography_id,
            t.generation_id,
            t.income_band_id,
            t.transaction_amount,
            t.card_type,
            t.payment_network,
            t.channel,
            t.day_of_week,
            t.hour_of_day,
        )
        for t in transactions
    ]
    cur.executemany(
        """
        INSERT INTO transactions (
            id, transaction_timestamp, panelist_id, brand_id, category_id,
            geography_id, generation_id, income_band_id, transaction_amount,
            card_type, payment_network, channel, day_of_week, hour_of_day
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (id) DO NOTHING
        """,
        rows,
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print("=" * 60)
    print("Proteus Synthetic Data Generator")
    print("=" * 60)
    print(f"  Panelists   : {PANELIST_COUNT:,}")
    print(f"  Date range  : {START_DATE} → {END_DATE}")
    print(f"  Seed        : {SEED}")
    print(f"  Database    : {DATABASE_URL}")
    print()

    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            # --- Seed reference tables ---
            print("[1/4] Seeding reference tables...")
            _seed_geography(cur)
            category_map = _seed_categories(cur)
            brand_list_raw = _seed_brands(cur, category_map)
            conn.commit()

        brand_list = _build_brand_list(brand_list_raw, category_map)
        category_list = _build_category_list(category_map)
        geography_lookup = _build_geography_lookup()

        print(f"       {len(brand_list)} brands, {len(category_list)} categories, "
              f"{len(geography_lookup)} geographies loaded\n")

        # --- Generate panelists ---
        print(f"[2/4] Generating {PANELIST_COUNT:,} panelists...")
        panelists = generate_panelists(count=PANELIST_COUNT, seed=SEED)
        print(f"       Generated {len(panelists):,} panelists")

        # --- Insert panelists in batches ---
        print(f"[3/4] Inserting panelists (batch size {BATCH_SIZE:,})...")
        with conn.cursor() as cur:
            for i in range(0, len(panelists), BATCH_SIZE):
                batch = panelists[i:i + BATCH_SIZE]
                _insert_panelists(cur, batch)
                print(f"       {min(i + BATCH_SIZE, len(panelists)):>8,} / {len(panelists):,}", end="\r")
        conn.commit()
        print(f"       {len(panelists):,} panelists committed          ")

        # --- Generate and insert transactions ---
        print(f"[4/4] Generating and inserting transactions...")
        total_txns = 0
        txn_buffer: list = []
        sample_txns: list = []  # keep first 50k for validation

        with conn.cursor() as cur:
            for idx, panelist in enumerate(panelists):
                txns = list(generate_transactions_for_panelist(
                    panelist=panelist,
                    start_date=START_DATE,
                    end_date=END_DATE,
                    brands=brand_list,
                    categories=category_list,
                    geography_lookup=geography_lookup,
                    seed=SEED + idx,  # unique seed per panelist
                ))
                txn_buffer.extend(txns)
                total_txns += len(txns)

                if len(sample_txns) < 50_000:
                    sample_txns.extend(txns)

                if len(txn_buffer) >= TXN_BATCH_SIZE:
                    _insert_transactions(cur, txn_buffer)
                    txn_buffer = []
                    conn.commit()

                if (idx + 1) % 500 == 0 or idx + 1 == len(panelists):
                    print(f"       Panelist {idx + 1:>8,}/{len(panelists):,}  "
                          f"txns so far: {total_txns:>10,}", end="\r")

            # flush remaining
            if txn_buffer:
                _insert_transactions(cur, txn_buffer)
            conn.commit()

        print(f"\n       {total_txns:,} transactions committed          ")

    # --- Validation report ---
    print("\n[Validation] Running data quality checks on sample...")
    report = generate_validation_report(sample_txns)
    print(f"  Overall pass     : {report.overall_pass}")
    for metric_name, result in vars(report).items():
        if metric_name == "overall_pass":
            continue
        status = "PASS" if getattr(result, "passed", None) else "FAIL"
        value  = getattr(result, "value",  "n/a")
        target = getattr(result, "target", "")
        print(f"  {metric_name:<30} {status}  value={value}  target={target}")

    print()
    print("Done.")
    sys.exit(0 if report.overall_pass else 1)


if __name__ == "__main__":
    main()
