"""Web search node for LangGraph workflow."""

from typing import List
import json
from ...models.state import AgentState, SearchIterationData
from ...models.search_result import WebSearchOutput
from ...services.search.web_search import SearchExecutor
from ...config.settings import settings
from ...observability.logger import log_node_execution, DetailedLogger


@log_node_execution
async def execute_web_search(state: AgentState) -> AgentState:
    """
    Execute web searches based on pending queries.
    
    Args:
        state: Current agent state
        
    Returns:
        Updated agent state with search results
    """
    session_id = state.get("session_id", "unknown")
    logger = DetailedLogger(session_id)
    search_executor = SearchExecutor(session_id=session_id)
    
    # Get pending queries
    queries = state.get("pending_queries", [])
    
    if not queries:
        logger.log_warning("No pending queries to execute")
        return state
    
    # Execute searches in parallel
    search_context = f"Due diligence investigation of {state['subject']}"
    current_depth = state.get("current_depth", 0)
    
    # Initialize search iteration data for audit trail
    web_search_config = settings.get_model_config("web_search")
    iteration_data: SearchIterationData = {
        "goal": f"Search iteration at depth {current_depth}",
        "queries": queries[:settings.max_queries_per_depth],
        "model_used": web_search_config.get("model"),
        "new_entities": [],
        "sources_found": 0,
        "errors": []
    }
    
    try:
        # Log search queries being executed
        logger.log_search_queries(queries[:settings.max_queries_per_depth], search_context)
        
        results: List[WebSearchOutput] = await search_executor.parallel_search(
            queries=queries[:settings.max_queries_per_depth],
            search_context=search_context,
            max_concurrent=state.get("max_concurrent_searches", 5)
        )
        
        # Count total sources found and build search memory
        total_sources = 0
        iteration_search_memories = []
        all_sources = []
        
        # Log search results and collect search memory
        for query, result in zip(queries[:settings.max_queries_per_depth], results):
            extracted_sources: List[str] = []
            sources_count = 0
            
            if result.sources:
                sources_count = len(result.sources)
                extracted_sources = [src.url for src in result.sources[:10]]
                # Collect all sources for iteration data
                all_sources.extend([
                    {"url": src.url, "title": src.title}
                    for src in result.sources
                ])
            
            total_sources += sources_count
            logger.log_search_results(query, sources_count, extracted_sources)
            
            # Collect search memory
            if result.search_result:
                iteration_search_memories.append({
                    "query": query,
                    "search_result": result.search_result or "",
                    "sources_count": sources_count,
                    "depth": current_depth
                })
            else:
                # LLM didn't provide search results (unexpected)
                logger.log("search_result_not_generated", {
                    "query": query,
                    "depth": current_depth,
                    "message": "LLM did not generate search result for this search"
                })
        
        # Update iteration data with sources found and sources list
        iteration_data["sources_found"] = total_sources
        iteration_data["sources"] = all_sources
        
        # Update search memory in state
        state["search_memory"].extend(iteration_search_memories)
        
        # Update query tracking
        state["queries_executed"].extend(queries[:settings.max_queries_per_depth])
        state["pending_queries"] = queries[settings.max_queries_per_depth:]  # Keep remaining queries
        
        # Update metrics
        state["search_count"] = state.get("search_count", 0) + len(results)
        
    except Exception as e:
        # Log error and continue
        logger.log_error("execute_web_search", e, {"queries": queries[:settings.max_queries_per_depth]})
        state["error_count"] = state.get("error_count", 0) + 1
        iteration_data["errors"].append(str(e))
    
    # Add search iteration to audit trail and store in state
    state["search_iterations"].append(iteration_data)
    
    # print("\n\n\n\n\n--------------------------------")
    # print("State after execute_web_search:")
    # import json
    # print(json.dumps(state, indent=2, default=str))
    # print("--------------------------------")
    
    # exit()
    
    return state



