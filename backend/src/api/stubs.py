"""IU-3 Dimension Enumeration API stub.

This module provides the interface contract for dimension enumeration
from the ASP.NET Core Data API (IU-3). This stub will be replaced
by the actual IU-3 implementation.

Interface: get_dimension_values(dimension: str) -> List[DimensionValue]

IMPORTANT: This is a stub for interface development. When IU-3 is implemented,
replace these stubs with actual API calls to GET /api/dimensions/{dimension}
"""

from typing import Dict, List, Any


class DimensionValue:
    """Stub for dimension enumeration value.

    This class represents a dimension value from the IU-3 enumeration API.
    When IU-3 is implemented, this will be replaced with the actual API response model.

    Attributes:
        id: Unique identifier for the dimension value.
        canonical_name: The canonical/normalized name.
        aliases: List of alternative names or spellings.
    """

    def __init__(self, id: str, canonical_name: str, aliases: List[str] = None):
        """Initialize a DimensionValue.

        Args:
            id: Unique identifier for the dimension value.
            canonical_name: The canonical/normalized name.
            aliases: List of alternative names or spellings.
        """
        self.id = id
        self.canonical_name = canonical_name
        self.aliases = aliases or []

    def __repr__(self) -> str:
        return f"DimensionValue(id={self.id!r}, canonical_name={self.canonical_name!r})"


async def get_dimension_values(dimension: str) -> List[DimensionValue]:
    """Stub that returns dimension values from IU-3 API.

    When IU-3 is implemented, this will call: GET /api/dimensions/{dimension}

    Args:
        dimension: One of brand, category, geography, generation, income_band, etc.

    Returns:
        List of DimensionValue objects

    Note:
        This is a stub implementation. The actual IU-3 API will provide
        real dimension enumeration values with proper canonicalization.
    """
    # Return empty list - real implementation comes from IU-3
    return []


async def validate_dimension_value(dimension: str, value: str) -> Dict[str, Any]:
    """Validate a dimension value against IU-3 enumeration.

    Args:
        dimension: Dimension type (brand, category, geography, etc.)
        value: Value to validate

    Returns:
        Dict with keys:
            - valid: bool indicating if value is valid
            - canonical: str or None for canonical value
            - suggestions: list of suggested corrections

    Note:
        This is a stub implementation. The actual IU-3 API will validate
        values against the canonical enumeration and provide suggestions.
    """
    # Stub implementation - returns invalid for all inputs
    return {"valid": False, "canonical": None, "suggestions": []}
