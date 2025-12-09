"""
Research data models for search and aggregation.

This module defines Pydantic models for:
- Web search operations and results
- Query generation
- Reflection and analysis outputs
- Connection mapping and entity graphs
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


# ============================================================================
# Web Search Models
# ============================================================================

class WebSearchSource(BaseModel):
    """Source found during web search (for LLM structured output)."""
    url: str = Field(description="URL of the source")
    title: str = Field(description="Title or publisher name")

class WebSearchOutput(BaseModel):
    """Structured output schema for web search LLM responses."""
    query: str = Field(description="The search query executed")
    search_result: str = Field(
        description="All the search results by keeping the key information verbatim as it is"
    )
    sources: List[WebSearchSource] = Field(description="All sources used with URLs and titles")

class SearchQueriesList(BaseModel):
    """Structured output schema for search query generation."""
    queries: List[str] = Field(
        description="Targeted search queries prioritized by value and relevance"
    )


# ============================================================================
# Reflection & Analysis Models
# ============================================================================

class ReflectionOutput(BaseModel):
    """
    Reflection output from Claude analysis.
    
    This model captures the AI's analysis of search results,
    including discovered entities, risk assessment, and strategic
    recommendations for next steps.
    """
    
    # Analysis Summary (Structured Text)
    analysis_summary: str = Field(
        description="""Comprehensive analysis in structured text format with sections:
        
## Key Findings
- List of new facts discovered

## Entities Discovered
- List of persons, organizations, events, locations

## Relationships
- Format: (subject) --relation--> (object)
- Example: (Sam Bankman-Fried) --founded--> (FTX)

## Risk Assessment
RED FLAGS:
- [SEVERITY] Description of red flag
NEUTRAL:
- Neutral factual findings
POSITIVE:
- Positive indicators

## Gaps
Identified: List of information gaps
Searched: Gaps we attempted to fill
Unfillable: Gaps with no data found

## Source Credibility
- Notes on source quality and reliability
"""
    )
    
    # Decision Making
    should_continue: bool = Field(description="Whether to continue research")
    reasoning: str = Field(description="Reasoning for continue/stop decision")
    
    # Query Strategy (Textual)
    query_strategy: str = Field(
        description="Textual description of priority topics and suggested search angles for next iteration"
    )


# ============================================================================
# Connection Mapping Models
# ============================================================================

class GraphNode(BaseModel):
    """Entity node for graph representation."""
    id: str = Field(description="Unique identifier for the entity")
    name: str = Field(description="Entity name")
    type: str = Field(description="Entity type: person, organization, event, location, etc.")
    attributes: Dict[str, Any] = Field(
        default_factory=dict,
        description="Flexible attributes for entity-specific data"
    )

class GraphEdge(BaseModel):
    """Relationship edge for graph representation."""
    source: str = Field(description="Source entity ID")
    target: str = Field(description="Target entity ID")
    relationship: str = Field(description="Relationship type (free-form)")
    confidence: float = Field(description="Confidence in this relationship (0-1)")
    attributes: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional relationship metadata (timeframe, type, etc.)"
    )

class KeyEntity(BaseModel):
    """Key entity with importance assessment."""
    entity: str = Field(description="Entity name")
    importance_score: float = Field(description="Importance to investigation (0-1)")
    reason: str = Field(description="Reasoning for importance")

class ConnectionMappingOutput(BaseModel):
    """Output from connection mapping analysis (OpenAI)."""
    
    # Graph Updates
    new_nodes: List[GraphNode] = Field(
        default_factory=list,
        description="New entities to add to graph"
    )
    new_edges: List[GraphEdge] = Field(
        default_factory=list,
        description="New relationships to add to graph"
    )
    
    # Pattern Detection
    patterns_identified: List[str] = Field(
        default_factory=list,
        description="Patterns found in connections (free-form descriptions)"
    )
    suspicious_patterns: List[str] = Field(
        default_factory=list,
        description="Auto-flagged concerning patterns"
    )
    
    # Entity Importance (LLM-based assessment)
    key_entities: List[KeyEntity] = Field(
        default_factory=list,
        description="Important entities with reasoning"
    )


# ============================================================================
# Report Synthesis Models
# ============================================================================

class RedFlag(BaseModel):
    """Individual red flag with severity and detail."""
    severity: str = Field(description="Severity level: CRITICAL, HIGH, MEDIUM, LOW")
    detail: str = Field(description="Detailed description of the red flag")


class DueDiligenceReport(BaseModel):
    """Comprehensive due diligence report schema."""
    
    executive_summary: str = Field(description="High-level overview of key findings and risk assessment")
    risk_level: str = Field(description="Overall risk level: CRITICAL, HIGH, MEDIUM, LOW")
    key_findings: List[str] = Field(description="Top 5-10 most important findings")
    
    # Detailed sections
    biographical_overview: str = Field(description="Personal background, education, family")
    professional_history: str = Field(description="Employment history, roles, career progression")
    financial_analysis: str = Field(description="Assets, investments, transactions, net worth")
    legal_regulatory: str = Field(description="Lawsuits, investigations, compliance issues")
    behavioral_patterns: str = Field(description="Decision-making patterns, associations, conduct")
    
    # Risk assessment
    red_flags: List[RedFlag] = Field(description="Critical red flags with severity and details")
    neutral_facts: List[str] = Field(description="Neutral factual findings")
    positive_indicators: List[str] = Field(description="Positive achievements and indicators")
    
    # Entity analysis
    key_relationships: List[str] = Field(description="Most important entity relationships")
    suspicious_connections: List[str] = Field(description="Concerning patterns or connections")
    
    # Evidence and sources
    source_summary: str = Field(description="Summary of source quality and credibility")
    evidence_strength: str = Field(description="Assessment of evidence quality")
    
    # Gaps and limitations
    information_gaps: List[str] = Field(description="Remaining unknowns or unclear areas")
    research_limitations: str = Field(description="Constraints on research completeness")
    
    # Recommendations
    recommendations: List[str] = Field(description="Recommended actions or further investigation")
