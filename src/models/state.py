"""
Agent state models for LangGraph workflow.

This module defines the state structure that flows through the research workflow.
All nodes in the graph read from and write to this shared state.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, List, Optional, TypedDict, Dict
from langchain_core.messages import BaseMessage


class SearchIterationData(TypedDict, total=False):
    """
    Data structure for tracking a single search iteration.
    
    This captures all relevant information about one search cycle,
    including queries executed, sources found, and any errors.
    """
    
    goal: str  # Purpose of this search iteration
    queries: List[str]  # Search queries executed
    model_used: Optional[str]  # LLM model used for search
    new_entities: List[str]  # New entities discovered
    sources_found: int  # Total number of sources found
    sources: List[Dict[str, str]]  # List of {url, title} dicts
    errors: List[str]  # Any errors encountered


class AgentState(TypedDict):
    """
    Complete state maintained throughout the agent workflow.
    
    This state is passed between LangGraph nodes and tracks all
    information discovered during the research process.
    
    The state is divided into logical sections:
    - Session Info: Basic session metadata
    - Research Progress: Current search depth and query tracking
    - Search Strategy: Pending queries to execute
    - Control Flow: Workflow control flags
    - Metrics: Performance and progress metrics
    - Audit Trail: Historical data for reporting
    - Search Results: Accumulated search findings
    - Reflection: Analysis and insights from each iteration
    - Entity Tracking: Discovered entities and relationships
    - Risk Assessment: Categorized findings
    - Messages: LangGraph message history
    """
    
    # ========== Session Info ==========
    session_id: str  # Unique session identifier
    subject: str  # Research subject name
    subject_context: Optional[str]  # Additional subject context
    
    # ========== Research Progress ==========
    current_depth: int  # Current search depth (0-indexed)
    max_depth: int  # Maximum search depth allowed
    queries_executed: List[str]  # All queries executed so far
    
    # ========== Search Strategy ==========
    pending_queries: List[str]  # Queries queued for execution
    
    # ========== Control Flow ==========
    should_continue: bool  # Whether to continue research
    termination_reason: Optional[str]  # Reason for termination
    
    # ========== Metrics ==========
    start_time: datetime  # Session start timestamp
    search_count: int  # Total searches executed
    extraction_count: int  # Total extractions performed
    error_count: int  # Total errors encountered
    iteration_count: int  # Total graph iterations (safety limit)
    
    # ========== Audit Trail ==========
    search_iterations: List[SearchIterationData]  # Per-iteration audit data
    
    # ========== Search Results Memory ==========
    search_memory: List[Dict[str, Any]]  # All search results for analysis
    
    # ========== Reflection & Analysis ==========
    reflection_memory: List[Dict[str, Any]]  # Reflection outputs per iteration
    
    # ========== Entity Tracking ==========
    discovered_entities: Dict[str, Any]  # Merged entities (LLM-managed)
    entity_graph: Dict[str, Any]  # Graph structure: {"nodes": [...], "edges": [...]}
    
    # ========== Risk Assessment ==========
    risk_indicators: Dict[str, List[str]]  # Categorized: red_flags, neutral, positive
    
    # ========== Messages (LangGraph) ==========
    messages: List[BaseMessage]  # LangGraph message history

