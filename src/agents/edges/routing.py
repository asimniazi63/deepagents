"""Routing logic for LangGraph conditional edges."""

from ...models.state import AgentState
from ...config.settings import settings
from ...utils.research_utils import check_stagnation
from ...observability.logger import DetailedLogger


def should_continue_research(state: AgentState) -> str:
    """
    Determine next action based on current state and reflection analysis.
    
    This implements the search strategy by deciding whether to:
    - continue_search: Generate more queries and continue searching
    - finalize: Stop research, map connections, and synthesize report
    
    Decision criteria (checked in order):
    1. Max depth reached → finalize (map connections then synthesize)
    2. Reflection recommends stop → finalize (map connections then synthesize)
    3. Stagnation detected (no new entities in N iterations) → finalize
    4. Otherwise → continue_search
    
    Note: Depth is incremented in the analyze_and_reflect node BEFORE this routing
    function is called. This ensures depth is correct when checking limits.
    Example: max_depth=3 → iterations run at depths 0, 1, 2 (total 3 iterations).
    
    The "finalize" route always goes through map_connections before synthesis to
    ensure entity graph is populated with nodes and edges from all discovered entities.
    
    Args:
        state: Current agent state
        
    Returns:
        Next node name ("continue_search", "finalize")
    """
    session_id = state.get("session_id", "unknown")
    logger = DetailedLogger(session_id)
    
    current_depth = state.get("current_depth", 0)
    max_depth = state.get("max_depth", settings.max_search_depth)
    
    # 1. Check hard limit: max depth
    # Note: Depth was already incremented in analyze_and_reflect node
    # With max_depth=3, we get iterations at depth 0, 1, 2 (total 3 iterations)
    if current_depth >= max_depth:
        logger.log_info("Routing decision: FINALIZE (max depth reached)", {
            "current_depth": current_depth,
            "max_depth": max_depth
        })
        state["termination_reason"] = "max_depth_reached"
        return "finalize"
    
    # 2. Check reflection decision
    reflection_memory = state.get("reflection_memory", [])
    if reflection_memory:
        latest_reflection = reflection_memory[-1]
        should_continue = latest_reflection.get("should_continue", True)
        
        if not should_continue:
            logger.log_info("Routing decision: FINALIZE (reflection recommended stop)", {
                "reasoning": latest_reflection.get("reasoning", "No reasoning provided")
            })
            state["termination_reason"] = "reflection_recommended_stop"
            return "finalize"
    
    # 3. Check stagnation (no new entities in last N iterations)
    if check_stagnation(reflection_memory, settings.stagnation_check_iterations):
        logger.log_info("Routing decision: FINALIZE (stagnation detected)", {
            "stagnation_iterations": settings.stagnation_check_iterations,
            "current_depth": state["current_depth"]
        })
        state["termination_reason"] = "stagnation_detected"
        return "finalize"
    
    # 4. Continue searching
    logger.log_info("Routing decision: CONTINUE_SEARCH", {
        "current_depth": current_depth,
        "next_iteration": current_depth
    })
    
    return "continue_search"


def has_new_queries(state: AgentState) -> str:
    """
    Check if query refinement produced new queries to execute.
    
    This routing function is called after refine_queries node to determine
    whether to execute the refined queries or proceed to synthesis.
    
    Args:
        state: Current agent state
        
    Returns:
        Next node name ("search_more", "synthesize")
    """
    logger = DetailedLogger(state.get("session_id", "unknown"))
    
    pending_queries = state.get("pending_queries", [])
    
    if pending_queries:
        logger.log_info("Routing decision: SEARCH_MORE", {
            "pending_queries_count": len(pending_queries)
        })
        return "search_more"
    else:
        logger.log_info("Routing decision: SYNTHESIZE (no new queries)")
        state["termination_reason"] = "no_additional_queries"
        return "synthesize"

