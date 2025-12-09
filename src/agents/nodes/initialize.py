"""Initialization node for LangGraph workflow."""

import uuid
from datetime import datetime
from typing import Dict, Any

from ...models.state import AgentState
from ...config.settings import settings
from ...observability.logger import log_node_execution, DetailedLogger


@log_node_execution
async def initialize_session(state: AgentState) -> AgentState:
    """
    Initialize a new research session with default values.
    
    Sets up all state fields including new reflection and entity tracking fields.
    
    Args:
        state: Initial agent state (must contain subject, may contain session_id and config)
        
    Returns:
        Fully initialized agent state ready for research workflow
    """
    # Validate required fields
    if not state.get("subject"):
        raise ValueError("State must contain 'subject' field")
    
    # Generate session ID if not provided
    session_id = state.get("session_id") or str(uuid.uuid4())
    
    logger = DetailedLogger(session_id)
    logger.log_info("Initializing research session", {
        "subject": state["subject"],
        "session_id": session_id
    })
    
    # Set default values for all state fields
    defaults = {
        # Session info
        "session_id": session_id,
        "start_time": datetime.utcnow(),
        
        # Research progress
        "current_depth": 0,
        "max_depth": state.get("max_depth", settings.max_search_depth),
        "queries_executed": [],
        "pending_queries": [],
        
        # Control flow
        "should_continue": True,
        "termination_reason": None,
        
        # Metrics
        "search_count": 0,
        "extraction_count": 0,
        "error_count": 0,
        "iteration_count": 0,
        
        # Memory and audit
        "search_iterations": [],
        "search_memory": [],
        "messages": [],
        
        # NEW: Reflection and entity tracking
        "reflection_memory": [],
        "discovered_entities": {},
        "entity_graph": {"nodes": [], "edges": []},
        
        # NEW: Risk assessment
        "risk_indicators": {
            "red_flags": [],
            "neutral": [],
            "positive": []
        },
    }
    
    # Apply defaults (don't override if already set)
    for key, value in defaults.items():
        if key not in state:
            state[key] = value
    
    logger.log_info("Session initialized successfully", {
        "session_id": session_id,
        "subject": state["subject"],
        "max_depth": state["max_depth"],
        "stagnation_check_iterations": settings.stagnation_check_iterations
    })
    
    return state

