"""IU-3 Dimension Enumeration API client.

Calls GET /api/dimensions/{dimension} on the ASP.NET Core Data API (IU-3)
to retrieve canonical dimension values and validate dimension inputs.
"""

from typing import Any, Dict, List

import httpx

from src.config import settings


class DimensionValue:
    """A dimension value returned by the IU-3 enumeration API.

    Attributes:
        id: Unique identifier for the dimension value.
        canonical_name: The canonical/normalized name.
        aliases: List of alternative names or spellings.
    """

    def __init__(self, id: str, canonical_name: str, aliases: List[str] = None):
        self.id = id
        self.canonical_name = canonical_name
        self.aliases = aliases or []

    def __repr__(self) -> str:
        return f"DimensionValue(id={self.id!r}, canonical_name={self.canonical_name!r})"


async def get_dimension_values(dimension: str) -> List[DimensionValue]:
    """Fetch dimension values from the IU-3 API.

    Calls: GET /api/dimensions/{dimension}

    Args:
        dimension: One of brands, categories, states, generations,
                   income-bands, channels, day-of-week, payment-networks.

    Returns:
        List of DimensionValue objects, or empty list if the API is unavailable.
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{settings.api_url}/api/dimensions/{dimension}")
            response.raise_for_status()
            payload = response.json()
            return [
                DimensionValue(
                    id=v["id"],
                    canonical_name=v["canonicalName"],
                    aliases=v.get("aliases", []),
                )
                for v in payload.get("values", [])
            ]
    except httpx.HTTPError:
        return []


async def validate_dimension_value(dimension: str, value: str) -> Dict[str, Any]:
    """Validate a dimension value against the IU-3 canonical enumeration.

    Fetches all values for the dimension and checks whether the given value
    matches a canonical name or any alias (case-insensitive).

    Args:
        dimension: Dimension type (brands, categories, states, etc.)
        value: Value to validate.

    Returns:
        Dict with keys:
            - valid: bool indicating if value is valid
            - canonical: str or None — the canonical name if valid
            - suggestions: list of up to 3 suggested corrections if invalid
    """
    values = await get_dimension_values(dimension)
    lower = value.lower()

    for dv in values:
        if dv.canonical_name.lower() == lower:
            return {"valid": True, "canonical": dv.canonical_name, "suggestions": []}
        if any(alias.lower() == lower for alias in dv.aliases):
            return {"valid": True, "canonical": dv.canonical_name, "suggestions": []}

    suggestions = [
        dv.canonical_name
        for dv in values
        if lower in dv.canonical_name.lower() or dv.canonical_name.lower() in lower
    ][:3]

    return {"valid": False, "canonical": None, "suggestions": suggestions}
