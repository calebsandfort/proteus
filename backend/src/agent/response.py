"""FR-8.3: Response Generation Model with User-Configurable Models.

This module implements the ResponseSynthesizer for generating natural language
answers from tool execution results with user-configurable model selection.

FR Requirements:
- FR-8.3: Response Generation Model
  - Response generation stage SHALL be user-configurable
  - Users SHALL be able to select from six providers: OpenAI, Google, Anthropic, Kimi, MiniMax, GLM
  - Model selection SHALL be exposed in the UI as a settings control
  - Changes SHALL apply to subsequent queries within the session
  - If selected model does not support function calling, SHALL fall back to
    text-embedding-3-small for embedding + strongest available model for generation,
    with user warning

Architecture:
- ResponseSynthesizer: Main class for response generation
- ModelSelector: Handles model selection with fallback logic
- VisualizationRecommender: Determines visualization types based on data patterns
"""

from typing import Any, AsyncGenerator, Dict, List, Optional

from pydantic import BaseModel, Field

from src.api.openrouter import OpenRouterClient
from src.config import USER_CONFIGURABLE_MODELS, model_config


# ============================================================================
# FR-8.3: Response Synthesis Models
# ============================================================================


class VisualizationRecommendation(BaseModel):
    """Visualization recommendation for the response.

    Attributes:
        chart_type: Recommended chart type (bar, line, pie, table, etc.).
        title: Title for the visualization.
        dimensions: Dimension mapping for the chart.
        options: Additional chart options.
    """

    chart_type: str = Field(..., description="Chart type: bar, line, pie, table, etc.")
    title: str = Field(default="", description="Title for the visualization")
    dimensions: Dict[str, str] = Field(
        default_factory=dict,
        description="Dimension mapping: x, y, color, etc."
    )
    options: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional chart options"
    )


class SynthesisResult(BaseModel):
    """Result from response synthesis.

    Attributes:
        answer: Natural language answer to the user's query.
        visualizations: List of visualization recommendations.
        suggestions: Follow-up suggestions for the user.
        model_used: The model actually used for generation.
        used_fallback: Whether fallback was triggered.
        warning: Optional warning message (e.g., if fallback was used).
    """

    answer: str = Field(..., description="Natural language answer")
    visualizations: List[VisualizationRecommendation] = Field(
        default_factory=list,
        description="Visualization recommendations"
    )
    suggestions: List[str] = Field(
        default_factory=list,
        description="Follow-up suggestions"
    )
    model_used: str = Field(..., description="Model used for generation")
    used_fallback: bool = Field(default=False, description="Whether fallback was triggered")
    warning: Optional[str] = Field(default=None, description="Warning message if any")


class FallbackInfo(BaseModel):
    """Information about model fallback.

    Attributes:
        model: The model to use (original or fallback).
        used_fallback: Whether fallback was triggered.
        warning: Warning message if fallback was used.
    """

    model: str
    used_fallback: bool
    warning: Optional[str] = None


# ============================================================================
# FR-8.3: Model Selector with Fallback Logic
# ============================================================================


class ModelSelector:
    """Handles model selection with fallback logic.

    FR-8.3: If selected model does not support function calling, SHALL fall back to
    text-embedding-3-small for embedding + strongest available model for generation,
    with user warning.

    The strongest available model is determined by preferring models that support
    function calling, with a consistent ordering preference:
    1. openai/gpt-4o (preferred for consistency)
    2. google/gemini-2.0-flash (fast, reliable)
    3. anthropic/claude-3.5-sonnet (high quality)
    4. moonshot/kimi-k2
    5. google/gemini-2.5-pro
    """

    # Preferred order for fallback - models that support function calling
    FALLBACK_PREFERENCE = [
        "openai/gpt-4o",
        "google/gemini-2.0-flash",
        "anthropic/claude-3.5-sonnet",
        "moonshot/kimi-k2",
        "google/gemini-2.5-pro",
    ]

    def __init__(self, default_model: Optional[str] = None):
        """Initialize ModelSelector.

        Args:
            default_model: Default model to use. Defaults to model_config.response_generation.
        """
        self.default_model = default_model or model_config.response_generation

    def select_model(self, model_id: str) -> FallbackInfo:
        """Select model with fallback if needed.

        FR-8.3: If selected model does not support function calling,
        fall back to the strongest available model.

        Args:
            model_id: The model ID requested by the user.

        Returns:
            FallbackInfo with the model to use and fallback status.
        """
        # Check if model exists in USER_CONFIGURABLE_MODELS
        if model_id not in USER_CONFIGURABLE_MODELS:
            # Unknown model, use default with warning
            return FallbackInfo(
                model=self._get_strongest_available_model(),
                used_fallback=True,
                warning=f"Model '{model_id}' not found. Using fallback model."
            )

        # Check if model supports function calling
        model_info = USER_CONFIGURABLE_MODELS[model_id]
        if model_info.get("supports_function_calling", False):
            # Model supports function calling, use it directly
            return FallbackInfo(
                model=model_id,
                used_fallback=False,
                warning=None
            )

        # Model doesn't support function calling, trigger fallback
        fallback_model = self._get_strongest_available_model()
        return FallbackInfo(
            model=fallback_model,
            used_fallback=True,
            warning=(
                f"Model '{model_id}' does not support function calling. "
                f"Falling back to '{fallback_model}' for response generation."
            )
        )

    def _get_strongest_available_model(self) -> str:
        """Get the strongest available model that supports function calling.

        Returns:
            Model ID of the strongest available model.
        """
        for model_id in self.FALLBACK_PREFERENCE:
            if model_id in USER_CONFIGURABLE_MODELS:
                model_info = USER_CONFIGURABLE_MODELS[model_id]
                if model_info.get("supports_function_calling", False):
                    return model_id

        # Fallback to first available model with function calling support
        for model_id, model_info in USER_CONFIGURABLE_MODELS.items():
            if model_info.get("supports_function_calling", False):
                return model_id

        # Ultimate fallback - should not happen if config is correct
        return "openai/gpt-4o"


# ============================================================================
# FR-8.3: Visualization Recommender
# ============================================================================


class VisualizationRecommender:
    """Recommends visualization types based on data patterns and query.

    FR-8.3: Response generation SHALL include visualization decisions
    (chart type recommendations).

    The recommender analyzes:
    - Query keywords (category, trend, proportion, comparison)
    - Data structure (time series, categories, segments)
    - Data patterns (trends, distributions, comparisons)
    """

    # Query patterns for visualization type
    QUERY_PATTERNS = {
        "category": ["category", "breakdown", "by", "each", "segment"],
        "trend": ["trend", "over time", "history", "progress", "growth"],
        "proportion": ["proportion", "share", "percentage", "distribution", "mix"],
        "comparison": ["compare", "comparison", "vs", "versus", "difference"],
        "ranking": ["top", "ranking", "best", "worst", "leader"],
    }

    # Data structure to chart type mapping
    DATA_CHART_MAPPING = {
        "time_series": "line",
        "categories": "bar",
        "proportions": "pie",
        "segments": "pie",
        "comparisons": "bar",
        "rankings": "bar",
        "geography": "map",
    }

    def recommend(self, query: str, data: Dict[str, Any]) -> VisualizationRecommendation:
        """Recommend visualization based on query and data.

        Args:
            query: User's original query.
            data: Tool result data.

        Returns:
            VisualizationRecommendation with chart type and details.
        """
        query_lower = query.lower()

        # Determine visualization type from query
        viz_type = self._infer_from_query(query_lower)

        # If query doesn't specify, infer from data structure
        if viz_type is None:
            viz_type = self._infer_from_data(data)

        # Build recommendation
        recommendation = self._build_recommendation(viz_type, query_lower, data)

        return recommendation

    def _infer_from_query(self, query: str) -> Optional[str]:
        """Infer visualization type from query keywords.

        Args:
            query: Lowercased query string.

        Returns:
            Inferred visualization type or None.
        """
        # Check trend patterns first
        for pattern in self.QUERY_PATTERNS["trend"]:
            if pattern in query:
                return "line"

        # Check category patterns
        for pattern in self.QUERY_PATTERNS["category"]:
            if pattern in query:
                return "bar"

        # Check proportion patterns
        for pattern in self.QUERY_PATTERNS["proportion"]:
            if pattern in query:
                return "pie"

        # Check comparison patterns
        for pattern in self.QUERY_PATTERNS["comparison"]:
            if pattern in query:
                return "bar"

        # Check ranking patterns
        for pattern in self.QUERY_PATTERNS["ranking"]:
            if pattern in query:
                return "bar"

        return None

    def _infer_from_data(self, data: Dict[str, Any]) -> str:
        """Infer visualization type from data structure.

        Args:
            data: Tool result data.

        Returns:
            Inferred visualization type.
        """
        # Check for time series indicators
        time_keys = ["time_series", "time", "dates", "months", "years", "quarters"]
        for key in time_keys:
            if key in data or any(key in str(k).lower() for k in data.keys()):
                return "line"

        # Check for proportion indicators
        proportion_keys = ["proportion", "percentage", "share", "mix"]
        for key in proportion_keys:
            if key in data:
                return "pie"

        # Check for segment indicators
        segment_keys = ["segment", "group", "category"]
        has_values = any("value" in str(k).lower() or "amount" in str(k).lower() for k in data.keys())
        if any(key in data for key in segment_keys) and has_values:
            return "bar"

        # Default to bar chart
        return "bar"

    def _build_recommendation(
        self,
        chart_type: str,
        query: str,
        data: Dict[str, Any]
    ) -> VisualizationRecommendation:
        """Build complete visualization recommendation.

        Args:
            chart_type: The chart type to recommend.
            query: The original query (lowercase).
            data: The tool result data.

        Returns:
            Complete VisualizationRecommendation.
        """
        # Extract title from query
        title = self._extract_title(query)

        # Determine dimensions based on chart type
        dimensions = self._extract_dimensions(chart_type, data)

        # Build options based on chart type
        options = self._build_options(chart_type, data)

        return VisualizationRecommendation(
            chart_type=chart_type,
            title=title,
            dimensions=dimensions,
            options=options
        )

    def _extract_title(self, query: str) -> str:
        """Extract a title from the query.

        Args:
            query: Lowercased query string.

        Returns:
            Extracted title.
        """
        # Simple title extraction - capitalize first letters
        words = query.split()
        if words:
            # Skip common question words
            skip_words = {"show", "what", "how", "compare", "display", "give", "tell"}
            title_words = [w for w in words if w not in skip_words]
            if title_words:
                return " ".join(w.capitalize() for w in title_words[:6])

        return "Data Visualization"

    def _extract_dimensions(self, chart_type: str, data: Dict[str, Any]) -> Dict[str, str]:
        """Extract dimension mapping from data.

        Args:
            chart_type: The chart type.
            data: The tool result data.

        Returns:
            Dimension mapping for the chart.
        """
        if chart_type == "line":
            return {"x": "time", "y": "value"}
        elif chart_type == "bar":
            return {"x": "category", "y": "value"}
        elif chart_type == "pie":
            return {"label": "segment", "value": "percentage"}

        return {}

    def _build_options(self, chart_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Build additional chart options.

        Args:
            chart_type: The chart type.
            data: The tool result data.

        Returns:
            Additional chart options.
        """
        options: Dict[str, Any] = {}

        if chart_type == "line":
            options["show_points"] = True
            options["smooth"] = True
        elif chart_type == "bar":
            options["horizontal"] = False
        elif chart_type == "pie":
            options["show_labels"] = True
            options["show_percentage"] = True

        return options


# ============================================================================
# FR-8.3: Response Synthesizer
# ============================================================================


class ResponseSynthesizer:
    """Synthesizes natural language responses from tool execution results.

    FR-8.3: Response generation stage with user-configurable model selection.
    The synthesizer:
    - Takes tool execution results and user query
    - Generates natural language answer using LLM
    - Determines visualization recommendations
    - Streams response token-by-token via SSE

    Attributes:
        openrouter_client: OpenRouter client for LLM calls.
        model: Selected model ID for response generation.
        model_selector: Model selector with fallback logic.
        visualizer: Visualization recommender.
    """

    # System prompt for response synthesis
    SYNTHESIS_SYSTEM_PROMPT = """You are a data analyst providing insights from consumer analytics data.

Your task is to:
1. Explain the key findings from the tool execution results
2. Use clear, concise language appropriate for business users
3. Highlight significant patterns, trends, or anomalies
4. Provide actionable insights when possible
5. Include specific numbers and percentages when available

Format your response as a natural paragraph or bullet points, not raw JSON."""

    # User prompt template for synthesis
    SYNTHESIS_USER_PROMPT = """Based on the user's query and tool execution results, provide a natural language answer.

User Query: {query}

Tool Results:
{tool_results}

Please provide a clear, concise answer that:
- Directly addresses the user's question
- Summarizes the key findings
- Uses specific numbers and data points
- Notes any important patterns or trends"""

    # Suggestions prompt for follow-up suggestions
    SUGGESTIONS_PROMPT = """Based on the query and results, suggest 2-3 natural follow-up questions the user might ask.

Query: {query}
Results: {results}

Provide suggestions that explore related aspects or deepen the analysis."""

    def __init__(
        self,
        openrouter_client: OpenRouterClient,
        model: Optional[str] = None,
    ):
        """Initialize ResponseSynthesizer.

        Args:
            openrouter_client: OpenRouter client for LLM calls.
            model: Model ID to use. Defaults to model_config.response_generation.
        """
        self.openrouter_client = openrouter_client
        self.model = model or model_config.response_generation
        self.model_selector = ModelSelector(default_model=self.model)
        self.visualizer = VisualizationRecommender()

    async def synthesize(
        self,
        query: str,
        tool_results: Dict[str, Any],
    ) -> SynthesisResult:
        """Synthesize a natural language response from tool results.

        Args:
            query: The user's original query.
            tool_results: Dictionary of tool execution results keyed by tool_id.

        Returns:
            SynthesisResult with answer, visualizations, and suggestions.
        """
        # Select model with fallback logic
        fallback_info = self.model_selector.select_model(self.model)

        # Format tool results for the prompt
        formatted_results = self._format_tool_results(tool_results)

        # Build messages for LLM
        messages = [
            {"role": "system", "content": self.SYNTHESIS_SYSTEM_PROMPT},
            {"role": "user", "content": self.SYNTHESIS_USER_PROMPT.format(
                query=query,
                tool_results=formatted_results
            )},
        ]

        # Call LLM
        try:
            response = await self.openrouter_client.call_with_retry(
                model=fallback_info.model,
                messages=messages,
                temperature=0.3,
                max_tokens=2048,
            )

            # Extract content from response
            answer = self._extract_content(response)

            # Generate visualization recommendations
            visualizations = self._generate_visualizations(query, tool_results)

            # Generate suggestions
            suggestions = await self._generate_suggestions(query, tool_results, answer)

            return SynthesisResult(
                answer=answer,
                visualizations=visualizations,
                suggestions=suggestions,
                model_used=fallback_info.model,
                used_fallback=fallback_info.used_fallback,
                warning=fallback_info.warning,
            )

        except Exception as e:
            # Return error result
            return SynthesisResult(
                answer=f"I apologize, but I encountered an error while generating the response: {str(e)}",
                visualizations=[],
                suggestions=[],
                model_used=fallback_info.model,
                used_fallback=fallback_info.used_fallback,
                warning=fallback_info.warning,
            )

    async def stream_response(
        self,
        query: str,
        tool_results: Dict[str, Any],
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream response as SSE events.

        Args:
            query: The user's original query.
            tool_results: Dictionary of tool execution results.

        Yields:
            SSE event dicts with 'event' and 'data' keys.
        """
        # Select model with fallback logic
        fallback_info = self.model_selector.select_model(self.model)

        # Yield warning if fallback was used
        if fallback_info.warning:
            yield {
                "event": "warning",
                "data": {"message": fallback_info.warning}
            }

        # Format tool results
        formatted_results = self._format_tool_results(tool_results)

        # Build messages
        messages = [
            {"role": "system", "content": self.SYNTHESIS_SYSTEM_PROMPT},
            {"role": "user", "content": self.SYNTHESIS_USER_PROMPT.format(
                query=query,
                tool_results=formatted_results
            )},
        ]

        # Stream response tokens
        try:
            # For streaming, we simulate token-by-token by using the full response
            # In a production system, this would use OpenRouter's streaming API
            response = await self.openrouter_client.call_with_retry(
                model=fallback_info.model,
                messages=messages,
                temperature=0.3,
                max_tokens=2048,
            )

            answer = self._extract_content(response)

            # Stream tokens (simulated - in production would be real streaming)
            words = answer.split()
            for i, word in enumerate(words):
                yield {
                    "event": "stream",
                    "data": {"token": word, "index": i}
                }
                # In production: would yield actual streamed tokens

            # Yield visualizations
            visualizations = self._generate_visualizations(query, tool_results)
            for viz in visualizations:
                yield {
                    "event": "visualization",
                    "data": viz.model_dump()
                }

            # Yield suggestions
            suggestions = await self._generate_suggestions(query, tool_results, answer)
            for suggestion in suggestions:
                yield {
                    "event": "suggestion",
                    "data": {"text": suggestion}
                }

        except Exception as e:
            yield {
                "event": "error",
                "data": {"message": str(e)}
            }

        # Yield done
        yield {
            "event": "done",
            "data": {
                "model_used": fallback_info.model,
                "used_fallback": fallback_info.used_fallback,
            }
        }

    def _format_tool_results(self, tool_results: Dict[str, Any]) -> str:
        """Format tool results for the prompt.

        Args:
            tool_results: Raw tool results dictionary.

        Returns:
            Formatted string for the prompt.
        """
        if not tool_results:
            return "No data available."

        formatted_parts = []
        for tool_id, result in tool_results.items():
            formatted_parts.append(f"### {tool_id}")
            if isinstance(result, dict):
                for key, value in result.items():
                    formatted_parts.append(f"- {key}: {value}")
            else:
                formatted_parts.append(str(result))
            formatted_parts.append("")

        return "\n".join(formatted_parts)

    def _extract_content(self, response: Dict[str, Any]) -> str:
        """Extract content from LLM response.

        Args:
            response: Raw response from OpenRouter client.

        Returns:
            Extracted content string.
        """
        if isinstance(response, dict):
            if "content" in response:
                return response["content"]
            if "tool_calls" in response and response["tool_calls"]:
                # Extract from function call
                tool_call = response["tool_calls"][0]
                if "parsed" in tool_call and isinstance(tool_call["parsed"], dict):
                    return tool_call["parsed"].get("content", "")
                return str(tool_call)
        elif isinstance(response, str):
            return response

        return str(response)

    def _generate_visualizations(
        self,
        query: str,
        tool_results: Dict[str, Any]
    ) -> List[VisualizationRecommendation]:
        """Generate visualization recommendations.

        Args:
            query: User's original query.
            tool_results: Tool execution results.

        Returns:
            List of visualization recommendations.
        """
        visualizations = []

        for tool_id, result in tool_results.items():
            if isinstance(result, dict):
                recommendation = self.visualizer.recommend(
                    query=query,
                    data=result
                )
                visualizations.append(recommendation)

        return visualizations

    async def _generate_suggestions(
        self,
        query: str,
        tool_results: Dict[str, Any],
        answer: str,
    ) -> List[str]:
        """Generate follow-up suggestions.

        Args:
            query: User's original query.
            tool_results: Tool execution results.
            answer: Generated answer.

        Returns:
            List of suggestion strings.
        """
        messages = [
            {"role": "user", "content": self.SUGGESTIONS_PROMPT.format(
                query=query,
                results=answer[:500]  # Limit context
            )},
        ]

        try:
            response = await self.openrouter_client.call_with_retry(
                model=self.model_selector.select_model(self.model).model,
                messages=messages,
                temperature=0.5,
                max_tokens=512,
            )

            content = self._extract_content(response)

            # Parse suggestions (simple extraction)
            suggestions = []
            for line in content.split("\n"):
                line = line.strip()
                if line and (line.startswith("-") or line.startswith("*") or line[0].isdigit()):
                    # Clean up the line
                    cleaned = line.lstrip("-*0123456789. )").strip()
                    if cleaned:
                        suggestions.append(cleaned)

            # Limit to 3 suggestions
            return suggestions[:3]

        except Exception:
            # Return default suggestions on error
            return [
                "Try expanding the time range for more context",
                "Compare with a different segment or category",
                "Explore the underlying factors behind these numbers",
            ]


# ============================================================================
# Module Exports
# ============================================================================

__all__ = [
    "ResponseSynthesizer",
    "ModelSelector",
    "VisualizationRecommender",
    "VisualizationRecommendation",
    "SynthesisResult",
    "FallbackInfo",
]
