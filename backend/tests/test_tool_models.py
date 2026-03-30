"""Tests for FR-2.1: Tool Definition Pydantic Models.

This module tests the ToolDefinition, ToolParameter, ToolOutputSchema,
and RetrievedTool models for the Tool Registry & RAG Retrieval system.

FR Requirements:
- The system SHALL maintain a registry of 12-15 core data retrieval tools
- Tool definitions SHALL include: id, name, description, capabilities,
  dimensions (required and optional), example queries, output schema, and aliases
- Tool definitions SHALL be stored as embeddings for semantic retrieval
"""

import pytest
from typing import List, Optional


class TestFr21ToolParameter:
    """FR-2.1: ToolParameter model structure."""

    def test_fr_2_1_tool_parameter_creation(self) -> None:
        """ToolParameter can be created with required fields."""
        from src.api.models.tool import ToolParameter

        param = ToolParameter(
            name="category",
            type="string",
            description="The spending category to analyze",
            required=True
        )

        assert param.name == "category"
        assert param.type == "string"
        assert param.description == "The spending category to analyze"
        assert param.required is True
        assert param.default is None

    def test_fr_2_1_tool_parameter_optional_with_default(self) -> None:
        """ToolParameter can have default value when optional."""
        from src.api.models.tool import ToolParameter

        param = ToolParameter(
            name="limit",
            type="integer",
            description="Maximum number of results",
            required=False,
            default=100
        )

        assert param.required is False
        assert param.default == 100

    def test_fr_2_1_tool_parameter_types(self) -> None:
        """ToolParameter supports common parameter types."""
        from src.api.models.tool import ToolParameter

        # String parameter
        str_param = ToolParameter(name="brand", type="string", description="Brand name", required=True)
        assert str_param.type == "string"

        # Integer parameter
        int_param = ToolParameter(name="limit", type="integer", description="Limit", required=False, default=10)
        assert int_param.type == "integer"

        # Number parameter
        num_param = ToolParameter(name="threshold", type="number", description="Threshold", required=False, default=0.5)
        assert num_param.type == "number"

        # Boolean parameter
        bool_param = ToolParameter(name="include_total", type="boolean", description="Include total", required=False, default=True)
        assert bool_param.type == "boolean"

        # Array parameter
        arr_param = ToolParameter(name="brands", type="array", description="Brand list", required=False)
        assert arr_param.type == "array"


class TestFr21ToolOutputSchema:
    """FR-2.1: ToolOutputSchema model structure."""

    def test_fr_2_1_tool_output_schema_creation(self) -> None:
        """ToolOutputSchema can be created with required fields."""
        from src.api.models.tool import ToolOutputSchema

        schema = ToolOutputSchema(
            format="json",
            description="Returns market share data by brand"
        )

        assert schema.format == "json"
        assert schema.description == "Returns market share data by brand"
        assert schema.fields is None

    def test_fr_2_1_tool_output_schema_with_fields(self) -> None:
        """ToolOutputSchema can define output fields."""
        from src.api.models.tool import ToolOutputSchema, OutputField

        schema = ToolOutputSchema(
            format="json",
            description="Returns time series data",
            fields=[
                OutputField(name="date", type="string", description="Date of the data point"),
                OutputField(name="value", type="number", description="Metric value"),
                OutputField(name="brand", type="string", description="Brand name")
            ]
        )

        assert len(schema.fields) == 3
        assert schema.fields[0].name == "date"
        assert schema.fields[1].name == "value"
        assert schema.fields[2].name == "brand"


class TestFr21ToolDefinition:
    """FR-2.1: ToolDefinition model structure."""

    def test_fr_2_1_tool_definition_creation_complete(self) -> None:
        """ToolDefinition can be created with all required fields."""
        from src.api.models.tool import (
            ToolDefinition,
            ToolParameter,
            ToolOutputSchema,
            OutputField,
        )

        tool = ToolDefinition(
            id="market_share_trend",
            name="Market Share Trend",
            description="Analyzes market share trends over time for brands within a category",
            capabilities=[
                "Calculates brand-level market share percentages",
                "Tracks trend direction over specified time periods",
                "Compares performance across multiple brands"
            ],
            required_dimensions=["category", "time_period"],
            optional_dimensions=["region", "panelist_segment"],
            parameters=[
                ToolParameter(
                    name="category",
                    type="string",
                    description="Product category to analyze",
                    required=True
                ),
                ToolParameter(
                    name="time_period",
                    type="string",
                    description="Time period for analysis (e.g., 'Q1 2024')",
                    required=True
                ),
                ToolParameter(
                    name="region",
                    type="string",
                    description="Geographic region (optional)",
                    required=False,
                    default="national"
                )
            ],
            output_schema=ToolOutputSchema(
                format="json",
                description="Returns market share trends",
                fields=[
                    OutputField(name="brand", type="string", description="Brand name"),
                    OutputField(name="share", type="number", description="Market share percentage"),
                    OutputField(name="trend", type="string", description="Trend direction (up/down/stable)")
                ]
            ),
            example_queries=[
                "What is the market share trend for cereal brands?",
                "How has Coca-Cola's market share changed this year?",
                "Show me the top 5 beverage brands by market share"
            ],
            aliases=["market_share", "share_trend", "brand_share"],
            version="1.0.0"
        )

        assert tool.id == "market_share_trend"
        assert tool.name == "Market Share Trend"
        assert tool.description == "Analyzes market share trends over time for brands within a category"
        assert len(tool.capabilities) == 3
        assert "category" in tool.required_dimensions
        assert "region" in tool.optional_dimensions
        assert len(tool.parameters) == 3
        assert tool.output_schema.format == "json"
        assert len(tool.example_queries) == 3
        assert "market_share" in tool.aliases
        assert tool.version == "1.0.0"

    def test_fr_2_1_tool_definition_minimal(self) -> None:
        """ToolDefinition can be created with minimal required fields."""
        from src.api.models.tool import ToolDefinition, ToolOutputSchema

        tool = ToolDefinition(
            id="simple_tool",
            name="Simple Tool",
            description="A simple tool with minimal configuration",
            capabilities=["Does something"],
            required_dimensions=["category"],
            optional_dimensions=[],
            parameters=[],
            output_schema=ToolOutputSchema(format="json", description="Simple output"),
            example_queries=[],
            aliases=[],
            version="1.0.0"
        )

        assert tool.id == "simple_tool"
        assert tool.name == "Simple Tool"
        assert tool.optional_dimensions == []
        assert tool.parameters == []
        assert tool.example_queries == []
        assert tool.aliases == []

    def test_fr_2_1_tool_definition_required_fields(self) -> None:
        """ToolDefinition requires all specified fields."""
        from src.api.models.tool import ToolDefinition, ToolOutputSchema
        from pydantic import ValidationError

        # id is required - Pydantic raises ValidationError for missing required fields
        with pytest.raises(ValidationError):
            ToolDefinition(
                name="Test",
                description="Test",
                capabilities=[],
                required_dimensions=[],
                optional_dimensions=[],
                parameters=[],
                output_schema=ToolOutputSchema(format="json", description=""),
                example_queries=[],
                aliases=[],
                version="1.0.0"
            )

    def test_fr_2_1_tool_definition_dimension_lists(self) -> None:
        """ToolDefinition dimension lists work correctly."""
        from src.api.models.tool import ToolDefinition, ToolOutputSchema

        tool = ToolDefinition(
            id="dimension_test",
            name="Dimension Test",
            description="Test dimensions",
            capabilities=[],
            required_dimensions=["category", "time_period", "region"],
            optional_dimensions=["age_group", "income_bracket", "channel"],
            parameters=[],
            output_schema=ToolOutputSchema(format="json", description=""),
            example_queries=[],
            aliases=[],
            version="1.0.0"
        )

        assert len(tool.required_dimensions) == 3
        assert "category" in tool.required_dimensions
        assert len(tool.optional_dimensions) == 3
        assert "age_group" in tool.optional_dimensions


class TestFr21RetrievedTool:
    """FR-2.1: RetrievedTool model structure."""

    def test_fr_2_1_retrieved_tool_creation(self) -> None:
        """RetrievedTool can be created with all fields."""
        from src.api.models.tool import (
            RetrievedTool,
            ToolDefinition,
            ToolOutputSchema
        )

        tool_def = ToolDefinition(
            id="brand_comparison",
            name="Brand Comparison",
            description="Compare brands",
            capabilities=["Compare two or more brands"],
            required_dimensions=["category", "brands"],
            optional_dimensions=["time_period"],
            parameters=[],
            output_schema=ToolOutputSchema(format="json", description="Comparison results"),
            example_queries=["Compare Nike and Adidas"],
            aliases=["compare_brands"],
            version="1.0.0"
        )

        retrieved = RetrievedTool(
            tool_id="brand_comparison",
            tool_definition=tool_def,
            similarity=0.95,
            rank=1
        )

        assert retrieved.tool_id == "brand_comparison"
        assert retrieved.tool_definition.id == "brand_comparison"
        assert retrieved.similarity == 0.95
        assert retrieved.rank == 1

    def test_fr_2_1_retrieved_tool_with_different_similarities(self) -> None:
        """RetrievedTool handles different similarity scores."""
        from src.api.models.tool import (
            RetrievedTool,
            ToolDefinition,
            ToolOutputSchema
        )

        tool_def = ToolDefinition(
            id="yoy_growth",
            name="Year-over-Year Growth",
            description="Calculate YoY growth",
            capabilities=["Calculate growth rates"],
            required_dimensions=["category"],
            optional_dimensions=["region"],
            parameters=[],
            output_schema=ToolOutputSchema(format="json", description="Growth data"),
            example_queries=[],
            aliases=[],
            version="1.0.0"
        )

        # Perfect match
        retrieved_high = RetrievedTool(
            tool_id="yoy_growth",
            tool_definition=tool_def,
            similarity=1.0,
            rank=1
        )
        assert retrieved_high.similarity == 1.0

        # Partial match
        retrieved_low = RetrievedTool(
            tool_id="yoy_growth",
            tool_definition=tool_def,
            similarity=0.72,
            rank=5
        )
        assert retrieved_low.similarity == 0.72
        assert retrieved_low.rank == 5


class TestFr21Validation:
    """FR-2.1: Model validation tests."""

    def test_fr_2_1_tool_id_not_empty(self) -> None:
        """ToolDefinition id cannot be empty."""
        from src.api.models.tool import ToolDefinition, ToolOutputSchema
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            ToolDefinition(
                id="",
                name="Test",
                description="Test",
                capabilities=[],
                required_dimensions=[],
                optional_dimensions=[],
                parameters=[],
                output_schema=ToolOutputSchema(format="json", description=""),
                example_queries=[],
                aliases=[],
                version="1.0.0"
            )

    def test_fr_2_1_version_format(self) -> None:
        """ToolDefinition version follows semantic versioning."""
        from src.api.models.tool import ToolDefinition, ToolOutputSchema

        tool = ToolDefinition(
            id="version_test",
            name="Version Test",
            description="Test version field",
            capabilities=[],
            required_dimensions=[],
            optional_dimensions=[],
            parameters=[],
            output_schema=ToolOutputSchema(format="json", description=""),
            example_queries=[],
            aliases=[],
            version="2.1.3"
        )

        assert tool.version == "2.1.3"


class TestFr21CoreToolSet:
    """FR-2.1: Core tool set definitions (P0, P1, P2 tools)."""

    def test_fr_2_1_p0_market_share_trend(self) -> None:
        """P0 tool: market_share_trend can be created."""
        from src.api.models.tool import ToolDefinition, ToolOutputSchema

        tool = ToolDefinition(
            id="market_share_trend",
            name="Market Share Trend",
            description="Analyzes market share trends over time",
            capabilities=["Calculate brand market share", "Track trends", "Compare brands"],
            required_dimensions=["category", "time_period"],
            optional_dimensions=["region", "panelist_segment"],
            parameters=[],
            output_schema=ToolOutputSchema(format="json", description="Market share data"),
            example_queries=["Market share trend for beverages"],
            aliases=["market_share", "share_trend"],
            version="1.0.0"
        )

        assert tool.id == "market_share_trend"
        assert "market_share" in tool.aliases

    def test_fr_2_1_p0_brand_comparison(self) -> None:
        """P0 tool: brand_comparison can be created."""
        from src.api.models.tool import ToolDefinition, ToolOutputSchema

        tool = ToolDefinition(
            id="brand_comparison",
            name="Brand Comparison",
            description="Compare multiple brands",
            capabilities=["Compare brand metrics", "Show relative performance"],
            required_dimensions=["category", "brands"],
            optional_dimensions=["time_period", "region"],
            parameters=[],
            output_schema=ToolOutputSchema(format="json", description="Comparison results"),
            example_queries=["Compare Nike and Adidas sales"],
            aliases=["compare_brands", "brand_vs"],
            version="1.0.0"
        )

        assert tool.id == "brand_comparison"

    def test_fr_2_1_p0_yoy_growth_analysis(self) -> None:
        """P0 tool: yoy_growth_analysis can be created."""
        from src.api.models.tool import ToolDefinition, ToolOutputSchema

        tool = ToolDefinition(
            id="yoy_growth_analysis",
            name="Year-over-Year Growth Analysis",
            description="Calculate YoY growth metrics",
            capabilities=["Calculate YoY growth", "Compare periods", "Identify trends"],
            required_dimensions=["category"],
            optional_dimensions=["region", "brand"],
            parameters=[],
            output_schema=ToolOutputSchema(format="json", description="Growth metrics"),
            example_queries=["YoY growth for electronics"],
            aliases=["yoy_growth", "growth_analysis"],
            version="1.0.0"
        )

        assert tool.id == "yoy_growth_analysis"

    def test_fr_2_1_p0_same_store_sales(self) -> None:
        """P0 tool: same_store_sales can be created."""
        from src.api.models.tool import ToolDefinition, ToolOutputSchema

        tool = ToolDefinition(
            id="same_store_sales",
            name="Same Store Sales Analysis",
            description="Analyze sales at consistent store locations",
            capabilities=["Same store sales", "Location consistency", "Sales tracking"],
            required_dimensions=["time_period"],
            optional_dimensions=["region", "category"],
            parameters=[],
            output_schema=ToolOutputSchema(format="json", description="Same store sales data"),
            example_queries=["Same store sales growth Q1"],
            aliases=["SSS", "identical_store_sales"],
            version="1.0.0"
        )

        assert tool.id == "same_store_sales"

    def test_fr_2_1_p0_category_trends(self) -> None:
        """P0 tool: category_trends can be created."""
        from src.api.models.tool import ToolDefinition, ToolOutputSchema

        tool = ToolDefinition(
            id="category_trends",
            name="Category Trends",
            description="Analyze spending trends by category",
            capabilities=["Category analysis", "Trend identification", "Spend tracking"],
            required_dimensions=["category"],
            optional_dimensions=["time_period", "region"],
            parameters=[],
            output_schema=ToolOutputSchema(format="json", description="Category trends"),
            example_queries=["Grocery spending trends"],
            aliases=["category_trend", "category_analysis"],
            version="1.0.0"
        )

        assert tool.id == "category_trends"

    def test_fr_2_1_p0_wallet_share(self) -> None:
        """P0 tool: wallet_share can be created."""
        from src.api.models.tool import ToolDefinition, ToolOutputSchema

        tool = ToolDefinition(
            id="wallet_share",
            name="Wallet Share Analysis",
            description="Measure consumer wallet allocation",
            capabilities=["Wallet allocation", "Spend share", "Consumer behavior"],
            required_dimensions=["category"],
            optional_dimensions=["demographics", "time_period"],
            parameters=[],
            output_schema=ToolOutputSchema(format="json", description="Wallet share data"),
            example_queries=["Wallet share for groceries"],
            aliases=["wallet_allocation", "share_of_wallet"],
            version="1.0.0"
        )

        assert tool.id == "wallet_share"

    def test_fr_2_1_p1_cross_shopping_overlap(self) -> None:
        """P1 tool: cross_shopping_overlap can be created."""
        from src.api.models.tool import ToolDefinition, ToolOutputSchema

        tool = ToolDefinition(
            id="cross_shopping_overlap",
            name="Cross-Shopping Overlap",
            description="Analyze cross-shopping behavior",
            capabilities=["Cross-shopping analysis", "Overlap metrics", "Brand switching"],
            required_dimensions=["brands"],
            optional_dimensions=["category", "time_period"],
            parameters=[],
            output_schema=ToolOutputSchema(format="json", description="Overlap data"),
            example_queries=["Cross-shopping between brands"],
            aliases=["overlap", "cross_shopping"],
            version="1.0.0"
        )

        assert tool.id == "cross_shopping_overlap"

    def test_fr_2_1_p1_demographic_breakdown(self) -> None:
        """P1 tool: demographic_breakdown can be created."""
        from src.api.models.tool import ToolDefinition, ToolOutputSchema

        tool = ToolDefinition(
            id="demographic_breakdown",
            name="Demographic Breakdown",
            description="Break down data by demographics",
            capabilities=["Demographic analysis", "Age groups", "Income levels"],
            required_dimensions=["category"],
            optional_dimensions=["age_group", "income", "region"],
            parameters=[],
            output_schema=ToolOutputSchema(format="json", description="Demographic data"),
            example_queries=["Sales by age group"],
            aliases=["demographics", "age_breakdown"],
            version="1.0.0"
        )

        assert tool.id == "demographic_breakdown"

    def test_fr_2_1_p1_geographic_breakdown(self) -> None:
        """P1 tool: geographic_breakdown can be created."""
        from src.api.models.tool import ToolDefinition, ToolOutputSchema

        tool = ToolDefinition(
            id="geographic_breakdown",
            name="Geographic Breakdown",
            description="Break down data by geography",
            capabilities=["Geographic analysis", "Regional data", "Location insights"],
            required_dimensions=["region"],
            optional_dimensions=["category", "time_period"],
            parameters=[],
            output_schema=ToolOutputSchema(format="json", description="Geographic data"),
            example_queries=["Sales by region"],
            aliases=["geography", "region_breakdown"],
            version="1.0.0"
        )

        assert tool.id == "geographic_breakdown"

    def test_fr_2_1_p1_customer_retention(self) -> None:
        """P1 tool: customer_retention can be created."""
        from src.api.models.tool import ToolDefinition, ToolOutputSchema

        tool = ToolDefinition(
            id="customer_retention",
            name="Customer Retention Analysis",
            description="Analyze customer retention rates",
            capabilities=["Retention rates", "Customer loyalty", "Churn analysis"],
            required_dimensions=["brand"],
            optional_dimensions=["time_period", "segment"],
            parameters=[],
            output_schema=ToolOutputSchema(format="json", description="Retention data"),
            example_queries=["Customer retention for brands"],
            aliases=["retention", "loyalty"],
            version="1.0.0"
        )

        assert tool.id == "customer_retention"

    def test_fr_2_1_p2_top_n_rankings(self) -> None:
        """P2 tool: top_n_rankings can be created."""
        from src.api.models.tool import ToolDefinition, ToolOutputSchema

        tool = ToolDefinition(
            id="top_n_rankings",
            name="Top N Rankings",
            description="Get top N rankings",
            capabilities=["Rankings", "Top performers", "Leaderboard"],
            required_dimensions=["category"],
            optional_dimensions=["time_period", "region", "n"],
            parameters=[],
            output_schema=ToolOutputSchema(format="json", description="Rankings data"),
            example_queries=["Top 10 brands"],
            aliases=["rankings", "top_brands"],
            version="1.0.0"
        )

        assert tool.id == "top_n_rankings"

    def test_fr_2_1_p2_channel_analysis(self) -> None:
        """P2 tool: channel_analysis can be created."""
        from src.api.models.tool import ToolDefinition, ToolOutputSchema

        tool = ToolDefinition(
            id="channel_analysis",
            name="Channel Analysis",
            description="Analyze sales by channel",
            capabilities=["Channel metrics", "Channel performance", "Channel comparison"],
            required_dimensions=["channel"],
            optional_dimensions=["category", "time_period"],
            parameters=[],
            output_schema=ToolOutputSchema(format="json", description="Channel data"),
            example_queries=["Sales by channel"],
            aliases=["channel", "channel_performance"],
            version="1.0.0"
        )

        assert tool.id == "channel_analysis"

    def test_fr_2_1_p2_basket_analysis(self) -> None:
        """P2 tool: basket_analysis can be created."""
        from src.api.models.tool import ToolDefinition, ToolOutputSchema

        tool = ToolDefinition(
            id="basket_analysis",
            name="Basket Analysis",
            description="Analyze purchase baskets",
            capabilities=["Basket analysis", "Purchase patterns", "Item affinity"],
            required_dimensions=["category"],
            optional_dimensions=["time_period", "region"],
            parameters=[],
            output_schema=ToolOutputSchema(format="json", description="Basket data"),
            example_queries=["Common purchase patterns"],
            aliases=["basket", "affinity"],
            version="1.0.0"
        )

        assert tool.id == "basket_analysis"

    def test_fr_2_1_p2_promotional_sensitivity(self) -> None:
        """P2 tool: promotional_sensitivity can be created."""
        from src.api.models.tool import ToolDefinition, ToolOutputSchema

        tool = ToolDefinition(
            id="promotional_sensitivity",
            name="Promotional Sensitivity",
            description="Analyze promotional impact",
            capabilities=["Promo analysis", "Price elasticity", "Discount impact"],
            required_dimensions=["brand"],
            optional_dimensions=["category", "time_period"],
            parameters=[],
            output_schema=ToolOutputSchema(format="json", description="Promo data"),
            example_queries=["Promotional impact on sales"],
            aliases=["promo_sensitivity", "price_elasticity"],
            version="1.0.0"
        )

        assert tool.id == "promotional_sensitivity"


class TestFr21ModelImports:
    """FR-2.1: Verify all models can be imported."""

    def test_fr_2_1_import_tool_definition(self) -> None:
        """ToolDefinition can be imported."""
        from src.api.models.tool import ToolDefinition
        assert ToolDefinition is not None

    def test_fr_2_1_import_tool_parameter(self) -> None:
        """ToolParameter can be imported."""
        from src.api.models.tool import ToolParameter
        assert ToolParameter is not None

    def test_fr_2_1_import_tool_output_schema(self) -> None:
        """ToolOutputSchema can be imported."""
        from src.api.models.tool import ToolOutputSchema
        assert ToolOutputSchema is not None

    def test_fr_2_1_import_retrieved_tool(self) -> None:
        """RetrievedTool can be imported."""
        from src.api.models.tool import RetrievedTool
        assert RetrievedTool is not None

    def test_fr_2_1_import_output_field(self) -> None:
        """OutputField can be imported."""
        from src.api.models.tool import OutputField
        assert OutputField is not None

    def test_fr_2_1_import_all_from_module(self) -> None:
        """All models can be imported from module."""
        from src.api.models.tool import (
            ToolDefinition,
            ToolParameter,
            ToolOutputSchema,
            RetrievedTool,
            OutputField
        )
        assert ToolDefinition is not None
        assert ToolParameter is not None
        assert ToolOutputSchema is not None
        assert RetrievedTool is not None
        assert OutputField is not None
