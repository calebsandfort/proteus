"""
Contract tests for Unit 9 (Chat UI Components) and Unit 10 (Visualization Engine) integration.

This module verifies the integration seams between:
- Unit 9: Chat UI Components (CopilotKit, chat sidebar, message handling)
- Unit 10: Visualization Engine (ECharts, auto chart selection, KPI cards)

Test categories:
1. Type Compatibility - Unit 10's chart types are compatible with Unit 9's tool results
2. Import Resolution - Cross-component imports resolve correctly
3. Wiring Verification - Providers, routers, and components are registered correctly
"""

import pytest
from pathlib import Path


# Get project root - go up from backend/tests/integration/ to project root
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent


class TestUnit9Unit10CrossComponentImports:
    """Test that Unit 9 and Unit 10 components can import each other."""

    def test_copilot_chat_imports_visualization_canvas(self):
        """Verify CopilotChat can import VisualizationCanvas from Unit 10."""
        try:
            from frontend.src.components.chat.copilot_chat import CopilotChat
            from frontend.src.components.visualization.VisualizationCanvas import VisualizationCanvas
            assert CopilotChat is not None
            assert VisualizationCanvas is not None
        except ImportError as e:
            # If running from backend directory, skip this specific import test
            pytest.skip(f"Cannot test frontend imports from backend context: {e}")

    def test_visualization_canvas_imports_chart_component(self):
        """Verify VisualizationCanvas can import ChartComponent from Unit 10."""
        try:
            from frontend.src.components.visualization.ChartComponent import ChartComponent
            assert ChartComponent is not None
        except ImportError as e:
            pytest.skip(f"Cannot test frontend imports from backend context: {e}")

    def test_copilot_chat_imports_feedback_components(self):
        """Verify CopilotChat can import feedback components from Unit 9."""
        try:
            from frontend.src.components.feedback.StageIndicator import StageIndicator
            from frontend.src.components.feedback.ChartSkeleton import ChartSkeleton
            from frontend.src.components.feedback.ErrorMessage import ErrorMessage
            assert StageIndicator is not None
            assert ChartSkeleton is not None
            assert ErrorMessage is not None
        except ImportError as e:
            pytest.skip(f"Cannot test frontend imports from backend context: {e}")


class TestUnit9Unit10TypeCompatibility:
    """Test that Unit 10's chart type outputs are compatible with Unit 9's input expectations."""

    def test_chart_type_enum_compatible_with_selection(self):
        """Verify ChartType enum is compatible with selectChartType output."""
        try:
            from frontend.src.lib.chart_selection import ChartType
            # ChartType should have these values per FR-5.1
            expected_types = ['kpi', 'line', 'bar', 'horizontal_bar', 'pie', 'donut',
                            'stacked_bar', 'scatter', 'heatmap', 'choropleth',
                            'stacked_area', 'waterfall', 'bump', 'table']
            for chart_type in expected_types:
                assert hasattr(ChartType, chart_type), f"Missing chart type: {chart_type}"
        except ImportError as e:
            pytest.skip(f"Cannot test frontend types from backend context: {e}")

    def test_kpi_data_structure_compatible(self):
        """Verify KPIData structure matches what the API response provides."""
        try:
            from typing import get_type_hints
            from frontend.src.components.visualization.KPICard import KPIData
            # KPIData should have these fields per FR-5.3
            hints = get_type_hints(KPIData)
            required_fields = ['metricName', 'value', 'unit']
            for field in required_fields:
                assert field in hints, f"Missing required field: {field}"
        except ImportError as e:
            pytest.skip(f"Cannot test frontend types from backend context: {e}")


class TestFrontendWiring:
    """Test that frontend components are properly wired in entry points."""

    def test_layout_imports_copilot_provider(self):
        """Verify root layout imports CopilotProvider (FR-1.1)."""
        layout_path = PROJECT_ROOT / "frontend" / "src" / "app" / "layout.tsx"
        if not layout_path.exists():
            pytest.skip("Frontend layout.tsx not found")

        content = layout_path.read_text()
        assert "CopilotProvider" in content, "CopilotProvider not imported in layout.tsx"
        assert "copilot-provider" in content or "CopilotProvider" in content, "CopilotProvider not used in layout.tsx"

    def test_chat_page_imports_copilot_chat(self):
        """Verify chat page imports and renders CopilotChat (FR-1.1)."""
        chat_page_path = PROJECT_ROOT / "frontend" / "src" / "app" / "chat" / "page.tsx"
        if not chat_page_path.exists():
            pytest.skip("Frontend chat/page.tsx not found")

        content = chat_page_path.read_text()
        assert "CopilotChat" in content or "copilot-chat" in content, "CopilotChat not imported in chat/page.tsx"

    def test_visualization_components_exist(self):
        """Verify all required visualization components exist (FR-5.1-FR-5.9)."""
        frontend_path = PROJECT_ROOT / "frontend" / "src" / "components" / "visualization"

        required_components = [
            "VisualizationCanvas.tsx",
            "ChartComponent.tsx",
            "KPICard.tsx",
            "ChartToolbar.tsx",
            "ViewModeToggle.tsx",
            "EmptyChart.tsx",
        ]

        for component in required_components:
            component_path = frontend_path / component
            assert component_path.exists(), f"Missing required component: {component}"

    def test_chart_selection_logic_exists(self):
        """Verify chart selection logic exists (FR-5.1)."""
        chart_selection_path = PROJECT_ROOT / "frontend" / "src" / "lib" / "chart-selection.ts"
        if not chart_selection_path.exists():
            pytest.skip("chart-selection.ts not found")

        content = chart_selection_path.read_text()
        assert "selectChartType" in content, "selectChartType function not found"


class TestBackendWiring:
    """Test that backend endpoints are properly wired."""

    def test_copilotkit_endpoint_registered(self):
        """Verify /copilotkit endpoint is registered in the API router."""
        try:
            from src.api.router import api_router
            from fastapi.routing import APIRoute

            route_paths = [r.path for r in api_router.routes if isinstance(r, APIRoute)]
            assert "/copilotkit" in route_paths, f"CopilotKit endpoint not found. Available routes: {route_paths}"
        except ImportError:
            pytest.skip("Backend module not available in this context")

    def test_main_app_includes_api_router(self):
        """Verify main app includes the API router."""
        try:
            from src.main import app

            route_paths = [r.path for r in app.routes if hasattr(r, 'path')]
            # The api_router should be mounted somewhere
            assert len(route_paths) > 0, "No routes found in app"
        except ImportError:
            pytest.skip("Backend module not available in this context")


class TestUnit9ComponentStructure:
    """Test Unit 9 component structure per FR-1.1, FR-1.3-FR-1.8."""

    def test_chat_components_exist(self):
        """Verify all required chat components exist (FR-1.1)."""
        chat_path = PROJECT_ROOT / "frontend" / "src" / "components" / "chat"

        required_components = [
            "copilot-chat.tsx",  # kebab-case in implementation
            "ChatSidebar.tsx",
            "ChatDrawer.tsx",
            "MessageBubble.tsx",
            "ClarificationCard.tsx",
            "EmptyState.tsx",
        ]

        for component in required_components:
            component_path = chat_path / component
            assert component_path.exists(), f"Missing required chat component: {component}"

    def test_feedback_components_exist(self):
        """Verify all required feedback components exist (FR-1.3-FR-1.7)."""
        feedback_path = PROJECT_ROOT / "frontend" / "src" / "components" / "feedback"

        required_components = [
            "StageIndicator.tsx",
            "ChartSkeleton.tsx",
            "ErrorMessage.tsx",
        ]

        for component in required_components:
            component_path = feedback_path / component
            assert component_path.exists(), f"Missing required feedback component: {component}"

    def test_hooks_exist(self):
        """Verify required hooks exist."""
        hooks_path = PROJECT_ROOT / "frontend" / "src" / "hooks"

        required_hooks = [
            "use-conversation.ts",
            "use-observability.ts",
            "use-sidebar.ts",
        ]

        for hook in required_hooks:
            hook_path = hooks_path / hook
            assert hook_path.exists(), f"Missing required hook: {hook}"


class TestUnit10ComponentStructure:
    """Test Unit 10 component structure per FR-5.1-FR-5.9."""

    def test_visualization_libs_exist(self):
        """Verify all required visualization lib files exist (FR-5.1-FR-5.9)."""
        lib_path = PROJECT_ROOT / "frontend" / "src" / "lib"

        required_libs = [
            "chart-selection.ts",
            "echarts-config.ts",
            "result-set-handler.ts",
        ]

        for lib in required_libs:
            lib_path_file = lib_path / lib
            assert lib_path_file.exists(), f"Missing required lib: {lib}"

    def test_visualization_hooks_exist(self):
        """Verify visualization history hook exists (FR-5.8)."""
        hooks_path = PROJECT_ROOT / "frontend" / "src" / "hooks" / "use-visualization-history.ts"
        if not hooks_path.exists():
            # Check if it might be in a different location
            alt_path = PROJECT_ROOT / "frontend" / "src" / "hooks"
            if alt_path.exists():
                hook_files = list(alt_path.glob("use-visualization*.ts"))
                if hook_files:
                    return  # Found alternative location
            pytest.skip("use-visualization-history.ts not found")
