"""Query generation node for LangGraph workflow using Claude."""

from ...models.state import AgentState
from ...services.search.query_generator import QueryGenerator
from ...observability.logger import log_node_execution, DetailedLogger

@log_node_execution
async def generate_search_queries(state: AgentState) -> AgentState:
    """
    Generate search queries using Claude based on reflection analysis.
    
    For Depth 0 (initial):
    - Generates broad queries covering biographical, professional, financial, legal aspects
    
    For Depth > 0 (refinement):
    - Uses reflection memory to guide query generation
    - Prioritizes red flags and high-severity issues
    - Targets newly discovered entities
    - Fills identified information gaps
    - Avoids repeating previous queries
    
    Args:
        state: Current agent state
        
    Returns:
        Updated agent state with pending queries
    """
    session_id = state.get("session_id", "unknown")
    logger = DetailedLogger(session_id)
    
    query_generator = QueryGenerator(session_id=session_id)
    current_depth = state.get("current_depth", 0)
    
    try:
        if current_depth == 0:
            # Initial broad queries
            logger.log_info("Generating initial queries", {
                "subject": state["subject"],
                "depth": current_depth
            })
                        
            queries = await query_generator.generate_initial_queries(
                subject=state["subject"],
                context=state.get("subject_context")
            )
            
        else:
            # Refined queries based on reflection
            logger.log_info("Generating refined queries from reflection", {
                "depth": current_depth,
                "reflections_count": len(state.get("reflection_memory", [])),
                "entities_count": len(state.get("discovered_entities", {})),
                "red_flags_count": len(state.get("risk_indicators", {}).get("red_flags", []))
            })
            
            queries = await query_generator.generate_refined_queries(
                subject=state["subject"],
                reflection_memory=state.get("reflection_memory", []),
                queries_executed=state.get("queries_executed", []),
                discovered_entities=state.get("discovered_entities", {}),
                current_depth=current_depth
            )
        
        # Log generated queries
        logger.log_info(f"Generated {len(queries)} queries for depth {current_depth}", {
            "queries": queries
        })
        
        # Update state
        state["pending_queries"] = queries
        
        # Increment iteration counter for safety
        state["iteration_count"] = state.get("iteration_count", 0) + 1
        
    except Exception as e:
        logger.log_error("generate_search_queries", e, {"depth": current_depth})
        state["error_count"] = state.get("error_count", 0) + 1
        state["pending_queries"] = []
    
    return state