"""FR-2.1: Tool Definition Pydantic Models.

This module defines the Pydantic models for the Tool Registry & RAG Retrieval system.

FR Requirements:
- The system SHALL maintain a registry of 12-15 core data retrieval tools
- Tool definitions SHALL include: id, name, description, capabilities,
  dimensions (required and optional), example queries, output schema, and aliases
- Tool definitions SHALL be stored as embeddings for semantic retrieval

Models:
    ToolParameter: Parameter definition for tool inputs
    OutputField: Field definition for output schema
    ToolOutputSchema: Output schema definition
    ToolDefinition: Complete tool definition with all metadata
    RetrievedTool: Tool retrieved from semantic search with similarity score
"""

from typing import Any, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class ToolParameter(BaseModel):
    """Parameter definition for tool inputs.

    Attributes:
        name: Parameter name identifier.
        type: Parameter type (string, integer, number, boolean, array).
        description: Human-readable description of the parameter.
        required: Whether the parameter is required.
        default: Default value for optional parameters.
    """

    model_config = ConfigDict(from_attributes=True)

    name: str = Field(..., description="Parameter name identifier")
    type: str = Field(..., description="Parameter type (string, integer, number, boolean, array)")
    description: str = Field(..., description="Human-readable description of the parameter")
    required: bool = Field(default=False, description="Whether the parameter is required")
    default: Optional[Any] = Field(default=None, description="Default value for optional parameters")


class OutputField(BaseModel):
    """Field definition for output schema.

    Attributes:
        name: Field name identifier.
        type: Field type (string, integer, number, boolean, array, object).
        description: Human-readable description of the field.
    """

    model_config = ConfigDict(from_attributes=True)

    name: str = Field(..., description="Field name identifier")
    type: str = Field(..., description="Field type (string, integer, number, boolean, array, object)")
    description: str = Field(..., description="Human-readable description of the field")


class ToolOutputSchema(BaseModel):
    """Output schema definition for tool responses.

    Attributes:
        format: Output format (json, csv, table).
        description: Human-readable description of the output.
        fields: Optional list of output field definitions.
    """

    model_config = ConfigDict(from_attributes=True)

    format: str = Field(..., description="Output format (json, csv, table)")
    description: str = Field(..., description="Human-readable description of the output")
    fields: Optional[List[OutputField]] = Field(default=None, description="Output field definitions")


class ToolDefinition(BaseModel):
    """Complete tool definition with all metadata.

    FR-2.1 Requirements:
    - id: Unique identifier for the tool
    - name: Human-readable name
    - description: Detailed description of what the tool does
    - capabilities: List of capability descriptions
    - required_dimensions: List of required dimension names
    - optional_dimensions: List of optional dimension names
    - parameters: List of ToolParameter definitions
    - output_schema: ToolOutputSchema definition
    - example_queries: List of example query strings
    - aliases: List of alternative names for semantic matching
    - version: Semantic version string

    Attributes:
        id: Unique identifier for the tool.
        name: Human-readable name.
        description: Detailed description of what the tool does.
        capabilities: List of capability descriptions.
        required_dimensions: List of required dimension names.
        optional_dimensions: List of optional dimension names.
        parameters: List of input parameter definitions.
        output_schema: Output schema definition.
        example_queries: List of example query strings.
        aliases: List of alternative names for semantic matching.
        version: Semantic version string.
    """

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., min_length=1, description="Unique identifier for the tool")
    name: str = Field(..., description="Human-readable name")
    description: str = Field(..., description="Detailed description of what the tool does")
    capabilities: List[str] = Field(..., description="List of capability descriptions")
    required_dimensions: List[str] = Field(..., description="List of required dimension names")
    optional_dimensions: List[str] = Field(..., description="List of optional dimension names")
    parameters: List[ToolParameter] = Field(..., description="List of input parameter definitions")
    output_schema: ToolOutputSchema = Field(..., description="Output schema definition")
    example_queries: List[str] = Field(..., description="List of example query strings")
    aliases: List[str] = Field(..., description="List of alternative names for semantic matching")
    version: str = Field(..., description="Semantic version string")


class RetrievedTool(BaseModel):
    """Tool retrieved from semantic search with similarity score.

    Used to return tool search results with relevance metrics.

    Attributes:
        tool_id: ID of the retrieved tool.
        tool_definition: Complete tool definition.
        similarity: Similarity score from semantic search (0-1).
        rank: Ranking position (1-based).
    """

    model_config = ConfigDict(from_attributes=True)

    tool_id: str = Field(..., description="ID of the retrieved tool")
    tool_definition: ToolDefinition = Field(..., description="Complete tool definition")
    similarity: float = Field(..., ge=0.0, le=1.0, description="Similarity score from semantic search (0-1)")
    rank: int = Field(..., ge=1, description="Ranking position (1-based)")
