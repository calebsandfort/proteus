"""Prompt management for LangGraph agent (FR-8.7)."""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml
from pydantic import BaseModel


class PromptVersion(BaseModel):
    """Versioned prompt template with metadata.

    Attributes:
        version: Semantic version string (e.g., "v1.0.0")
        template_name: Human-readable name for the prompt
        template_content: Template string with {variable} placeholders
        variables: List of variable names used in the template
        created_at: Timestamp when version was created
        created_by: User or system that created this version
        changelog: Optional description of changes in this version
    """

    version: str
    template_name: str
    template_content: str
    variables: List[str]
    created_at: datetime
    created_by: str
    changelog: Optional[str] = None


class PromptManager:
    """Manages versioned prompt templates with YAML storage.

    FR-8.7: Prompt templates are versioned and stored in configuration,
    each API request logs the prompt version used for reproducibility.

    Attributes:
        prompt_dir: Directory containing YAML prompt files
        prompts: Internal dict mapping prompt_name -> {version -> PromptVersion}
    """

    def __init__(self, prompt_dir: str = "./config/prompts", prompts: Optional[Dict[str, Dict[str, PromptVersion]]] = None):
        """Initialize PromptManager.

        Args:
            prompt_dir: Path to directory containing prompt YAML files.
                If directory exists, prompts will be loaded from YAML.
            prompts: Optional dict for dependency injection (testing).
                If provided, used instead of loading from prompt_dir.
        """
        self.prompt_dir = prompt_dir
        if prompts is not None:
            self.prompts = prompts
        else:
            self.prompts = self._load_prompts(prompt_dir)

    def _load_prompts(self, prompt_dir: str) -> Dict[str, Dict[str, PromptVersion]]:
        """Load prompts from YAML files in the given directory.

        Args:
            prompt_dir: Directory path containing prompt YAML files

        Returns:
            Dict mapping prompt_name to dict of version -> PromptVersion
        """
        prompts: Dict[str, Dict[str, PromptVersion]] = {}
        dir_path = Path(prompt_dir)

        if not dir_path.exists():
            return prompts

        for yaml_file in dir_path.glob("*.yaml"):
            with open(yaml_file, "r") as f:
                data = yaml.safe_load(f)

            if not data or "prompts" not in data:
                continue

            for prompt_name, versions in data["prompts"].items():
                if prompt_name not in prompts:
                    prompts[prompt_name] = {}

                for version_str, version_data in versions.items():
                    # Parse created_at string to datetime if needed
                    created_at = version_data.get("created_at")
                    if isinstance(created_at, str):
                        created_at = datetime.fromisoformat(created_at)

                    prompts[prompt_name][version_str] = PromptVersion(
                        version=version_data["version"],
                        template_name=version_data["template_name"],
                        template_content=version_data["template_content"],
                        variables=version_data["variables"],
                        created_at=created_at,
                        created_by=version_data["created_by"],
                        changelog=version_data.get("changelog"),
                    )

        return prompts

    def get_prompt(self, name: str, version: str = "latest") -> str:
        """Retrieve prompt template content by name and version.

        Args:
            name: Prompt template name
            version: Version string or "latest" (default)

        Returns:
            The template content string

        Raises:
            ValueError: If prompt name or version not found
        """
        if name not in self.prompts:
            raise ValueError(f"Prompt {name} version {version} not found")

        if version == "latest":
            version = self._get_latest_version(name)

        if version not in self.prompts[name]:
            raise ValueError(f"Prompt {name} version {version} not found")

        return self.prompts[name][version].template_content

    def _get_latest_version(self, name: str) -> str:
        """Get the latest version string for a prompt.

        Args:
            name: Prompt template name

        Returns:
            Version string of the latest version

        Raises:
            ValueError: If prompt not found or has no versions
        """
        if name not in self.prompts or not self.prompts[name]:
            raise ValueError(f"Prompt {name} has no versions")

        # Sort versions by semantic version (v1.0.0 < v1.1.0 < v2.0.0)
        versions = sorted(
            self.prompts[name].keys(),
            key=lambda v: tuple(int(x) for x in v.lstrip("v").split(".")),
        )
        return versions[-1]

    def render_prompt(self, name: str, variables: Dict[str, Any]) -> Tuple[str, PromptVersion]:
        """Render a prompt template with the given variables.

        Args:
            name: Prompt template name
            variables: Dict of variable names to values for template rendering

        Returns:
            Tuple of (rendered_prompt_string, PromptVersion_metadata)

        Raises:
            ValueError: If prompt not found
        """
        version = self._get_latest_version(name)
        prompt_version = self.prompts[name][version]
        rendered = prompt_version.template_content.format(**variables)
        return rendered, prompt_version


# Default system prompt (kept for backward compatibility)
SYSTEM_PROMPT = """You are a helpful AI assistant. You provide clear, concise, \
and accurate responses. If you don't know something, say so rather than making \
things up."""


# FR-2.6: Planner Node Prompt (GLM-4-Air model)
PLANNER_PROMPT = """You are a query planner for a consumer analytics system using GLM-4-Air model.

Given the user's query and retrieved tools, determine:
1. Is this a single-tool or multi-tool query?
2. What tools are needed and in what order?
3. Are there any dependencies between dimension extractions?

Query: {query}
Retrieved Tools: {retrieved_tools}
Extracted Dimensions: {extracted_dimensions}

Respond with a JSON object:
{{
  "is_multi_tool": true/false,
  "tools": [
    {{
      "tool_id": "tool_id",
      "order": 0,
      "parameters": {{"param": "value"}},
      "depends_on": [],
      "can_parallelize": true/false
    }}
  ],
  "dimension_dependencies": {{"dimension": ["dependent_dimensions"]}},
  "estimated_latency_ms": number,
  "execution_mode": "parallel"/"sequential",
  "reasoning": "explanation"
}}

Rules:
- If same tool with different parameters, is_multi_tool=false (batch execution)
- Only multi_tool=true if different tools needed
- can_parallelize=true if tools have no dependencies
- Estimate latency: 200ms base + 100ms per tool + 50ms per dependency"""


# FR-2.4: Tool Selection Node Prompt (MiniMax-Text-01 model)
TOOL_SELECTION_PROMPT = """You are a tool selection specialist for a consumer analytics system using MiniMax-Text-01 model.

Given the user's query and retrieved candidate tools, select the best matching tool(s).
Consider:
1. How well the tool description matches the query intent
2. Whether required dimensions are present in the extracted dimensions
3. RAG similarity scores as reference (but override if LLM judgment differs)

Query: {query}
Retrieved Tools: {retrieved_tools}
Extracted Dimensions: {extracted_dimensions}
RAG Similarity Scores: {rag_scores}

Respond with a JSON object:
{{
  "selected_tools": ["tool_id1", "tool_id2"],
  "confidence": 0.0-1.0,
  "confidence_breakdown": {{
    "rag_similarity": 0.0-1.0,
    "llm_selection": 0.0-1.0,
    "dimension_match": 0.0-1.0
  }},
  "competing_candidates": ["tool_id"] (only if confidence 0.70-0.84),
  "reasoning": "explanation of why these tools were selected"
}}

Rules:
- Select 1-3 tools maximum
- If no tool is appropriate, return empty selected_tools and confidence 0.0
- Confidence <0.70 triggers HITL clarification
- Show competing_candidates when confidence is 0.70-0.84"""


# FR-3.1-3.7: Dimension Extraction Context Prompt
EXTRACTION_PROMPT = """You are a dimension extraction specialist for a consumer analytics system.

Extract the following dimensions from the user's query:
- brand: Retailer or brand names (Walmart, Target, Chipotle, etc.)
- merchant_category: Category of purchase (retail, grocery, dining, etc.)
- geography: US states or regions (CA, TX, NY, etc.)
- time_range: Time period (last quarter, Q3 2024, YTD, etc.)
- generation: Demographic generation (gen_z, millennial, gen_x, etc.)
- income_band: Income level (band_1 through band_6)
- card_type: Payment card type (credit, debit, prepaid, corporate)
- payment_network: Card network (visa, mastercard, amex, discover)
- channel: Purchase channel (online, in_store, mobile)
- day_of_week: Day(s) of week (monday, tuesday, etc.)

Query: {query}

Respond with a JSON object with arrays of found values for each dimension.
Only include dimensions that are explicitly mentioned or strongly implied."""
