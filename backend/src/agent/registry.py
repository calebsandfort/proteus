"""FR-2.1: Tool Registry.

This module provides the ToolRegistry class for the Tool Registry & RAG Retrieval system.

FR Requirements:
- The system SHALL maintain a registry of 12-15 core data retrieval tools
- Tool definitions SHALL be stored as embeddings for semantic retrieval
- Tools SHALL be addable, modifiable, or deprecated without pipeline changes

Interface Contract:
    class ToolRegistry:
        def register(self, tool: ToolDefinition) -> None
        def get(self, tool_id: str) -> Optional[ToolDefinition]
        def list_active(self) -> List[ToolDefinition]
        def search_by_embedding(self, query_embedding: np.ndarray, top_k: int = 8) -> List[RetrievedTool]

Dependencies:
    - backend/src/api/models/tool.py -- ToolDefinition, RetrievedTool
    - backend/src/api/openrouter.py -- OpenRouterClient, SIMILARITY_THRESHOLD
"""

from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import yaml

from src.api.models.tool import RetrievedTool, ToolDefinition
from src.api.openrouter import DEFAULT_TOP_K, SIMILARITY_THRESHOLD, OpenRouterClient


class _ToolEntry:
    """Internal storage model for a tool with its embedding."""

    def __init__(
        self,
        tool_definition: ToolDefinition,
        embedding: np.ndarray,
        is_active: bool = True,
    ) -> None:
        """Initialize a tool entry.

        Args:
            tool_definition: The tool definition.
            embedding: The embedding vector for the tool.
            is_active: Whether the tool is active (not deprecated).
        """
        self.tool_definition = tool_definition
        self.embedding = embedding
        self.is_active = is_active


class ToolRegistry:
    """Registry for managing tool definitions with semantic search.

    Maintains a collection of ToolDefinition objects with associated embeddings
    for semantic retrieval via cosine similarity search.

    Attributes:
        client: OpenRouterClient for generating embeddings.
        _tools: Internal dictionary mapping tool_id to _ToolEntry.
    """

    def __init__(
        self,
        tools_dir: Optional[Path] = None,
        openrouter_client: Optional[OpenRouterClient] = None,
    ) -> None:
        """Initialize the ToolRegistry.

        Args:
            tools_dir: Path to directory containing tool YAML definitions.
                Defaults to backend/src/config/tools/.
            openrouter_client: Optional OpenRouterClient instance.
                If not provided, creates a new one.
        """
        if tools_dir is None:
            # Default to backend/src/config/tools/
            tools_dir = Path(__file__).parent.parent / "config" / "tools"

        self._tools_dir = tools_dir
        self._tools: Dict[str, _ToolEntry] = {}

        if openrouter_client is None:
            self._client = OpenRouterClient()
        else:
            self._client = openrouter_client

        # Load tools from YAML files if directory exists
        self._load_tools_from_dir()

    def _load_tools_from_dir(self) -> None:
        """Load tool definitions from YAML files in the tools directory."""
        if not self._tools_dir.exists():
            return

        for yaml_file in self._tools_dir.glob("*.yaml"):
            self._load_tools_from_file(yaml_file)
        for yaml_file in self._tools_dir.glob("*.yml"):
            self._load_tools_from_file(yaml_file)

    def _load_tools_from_file(self, file_path: Path) -> None:
        """Load tool definitions from a single YAML file.

        Args:
            file_path: Path to the YAML file.
        """
        try:
            with open(file_path, "r") as f:
                data = yaml.safe_load(f)

            if data is None:
                return

            tools_data = data.get("tools", [])
            for tool_data in tools_data:
                tool_def = ToolDefinition(**tool_data)
                self.register(tool_def)
        except Exception:
            # Skip files that fail to load - they may be incomplete
            pass

    def register(self, tool: ToolDefinition) -> None:
        """Register a tool definition and generate its embedding.

        Args:
            tool: The tool definition to register.
        """
        # Generate embedding from tool description and metadata
        text_to_embed = self._tool_to_text(tool)
        embeddings = self._client.embed_texts([text_to_embed])

        if embeddings:
            embedding = embeddings[0]
        else:
            # Fallback to zero vector if embedding fails
            embedding = np.zeros(1536, dtype=np.float32)

        self._tools[tool.id] = _ToolEntry(
            tool_definition=tool,
            embedding=embedding,
            is_active=True,
        )

    def _tool_to_text(self, tool: ToolDefinition) -> str:
        """Convert a tool definition to text for embedding.

        Args:
            tool: The tool definition.

        Returns:
            A text string representing the tool for embedding.
        """
        parts = [
            tool.name,
            tool.description,
            f"Capabilities: {', '.join(tool.capabilities)}",
            f"Required dimensions: {', '.join(tool.required_dimensions)}",
            f"Optional dimensions: {', '.join(tool.optional_dimensions)}",
            f"Aliases: {', '.join(tool.aliases)}",
            f"Example queries: {', '.join(tool.example_queries)}",
        ]
        return " | ".join(parts)

    def get(self, tool_id: str) -> Optional[ToolDefinition]:
        """Retrieve a tool by its ID.

        Args:
            tool_id: The unique identifier of the tool.

        Returns:
            The ToolDefinition if found and active, None otherwise.
        """
        entry = self._tools.get(tool_id)
        if entry is None:
            return None
        if not entry.is_active:
            return None
        return entry.tool_definition

    def list_active(self) -> List[ToolDefinition]:
        """List all active tool definitions.

        Returns:
            List of all active ToolDefinition objects.
        """
        return [
            entry.tool_definition
            for entry in self._tools.values()
            if entry.is_active
        ]

    def search_by_embedding(
        self,
        query_embedding: np.ndarray,
        top_k: int = DEFAULT_TOP_K,
    ) -> List[RetrievedTool]:
        """Search for tools using semantic similarity.

        Args:
            query_embedding: The embedding vector to search with.
            top_k: Maximum number of results to return.

        Returns:
            List of RetrievedTool objects sorted by similarity descending,
            filtered to exclude results below SIMILARITY_THRESHOLD.
        """
        # Collect all candidates with their similarities first
        candidates: List[tuple[float, ToolDefinition]] = []

        for entry in self._tools.values():
            if not entry.is_active:
                continue

            similarity = self._cosine_similarity(query_embedding, entry.embedding)

            if similarity >= SIMILARITY_THRESHOLD:
                candidates.append((similarity, entry.tool_definition))

        # Sort by similarity descending
        candidates.sort(key=lambda x: x[0], reverse=True)

        # Build RetrievedTool list with proper ranks (rank starts at 1)
        results: List[RetrievedTool] = []
        for i, (similarity, tool_def) in enumerate(candidates[:top_k]):
            results.append(
                RetrievedTool(
                    tool_id=tool_def.id,
                    tool_definition=tool_def,
                    similarity=float(similarity),
                    rank=i + 1,  # Rank starts at 1
                )
            )

        return results

    @staticmethod
    def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors.

        Args:
            a: First vector.
            b: Second vector.

        Returns:
            Cosine similarity score between -1 and 1.
        """
        # Handle dimension mismatch by padding/truncating to match
        max_len = max(len(a), len(b))
        a_padded = np.pad(a, (0, max_len - len(a)), mode='constant', constant_values=0)
        b_padded = np.pad(b, (0, max_len - len(b)), mode='constant', constant_values=0)

        # Handle zero vectors
        norm_a = np.linalg.norm(a_padded)
        norm_b = np.linalg.norm(b_padded)

        if norm_a == 0 or norm_b == 0:
            return 0.0

        # Cosine similarity = dot(a, b) / (norm(a) * norm(b))
        dot_product = np.dot(a_padded, b_padded)
        return dot_product / (norm_a * norm_b)
