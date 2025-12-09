"""Analysis node for LangGraph workflow."""

from ...models.state import AgentState
from ...models.search_result import ReflectionOutput
from ...services.llm.claude_service import ClaudeService
from ...observability.logger import log_node_execution, DetailedLogger
from ...utils.research_utils import merge_entities_with_llm
from ...prompts.analysis import build_reflection_prompt, ANALYSIS_SYSTEM_PROMPT


@log_node_execution
async def analyze_and_reflect(state: AgentState) -> AgentState:
    """
    Analyze and reflect on search results using Claude.
    
    This node:
    1. Compresses research findings into structured categories
    2. Assesses source credibility using LLM
    3. Extracts new entities and relationships
    4. Categorizes findings as red_flags/neutral/positive
    5. Performs gap analysis
    6. Calculates confidence score
    7. Decides whether to continue research
    8. Suggests priority topics and angles for next iteration
    
    Args:
        state: Current agent state
        
    Returns:
        Updated agent state with reflection results
    """
    session_id = state.get("session_id", "unknown")
    logger = DetailedLogger(session_id)
    logger.log_info("Starting reflection and analysis", {
        "current_depth": state.get("current_depth", 0),
        "search_iterations": len(state.get("search_memory", []))
    })
    
    # Validate required fields
    if not state.get("search_memory"):
        logger.log_warning("No search memory to analyze, skipping reflection")
        return state
    
    # Initialize Claude service for analysis
    claude = ClaudeService(session_id=state["session_id"], operation="analysis")
    
    # Build reflection prompt
    prompt = build_reflection_prompt(state)
    
    # Execute reflection analysis
    logger.log_info("Executing Claude reflection analysis")

    reflection_result = await claude.extract_structured(
        text=prompt,
        schema=ReflectionOutput,
        system_prompt=ANALYSIS_SYSTEM_PROMPT
    )
    
    logger.log_info("Reflection analysis complete", {
        "analysis_length": len(reflection_result.get("analysis_summary", "")),
        "should_continue": reflection_result.get("should_continue", False)
    })
    
    # Merge entities using OpenAI (handles entity extraction from text + deduplication)
    logger.log_info("Merging entities with OpenAI (extracts from analysis_summary)")
    merged_entities = await merge_entities_with_llm(
        existing_entities=state.get("discovered_entities", {}),
        analysis_summary=reflection_result.get("analysis_summary", ""),
        session_id=state["session_id"]
    )
    
    # Update state with reflection results
    state["reflection_memory"].append(reflection_result)
    state["discovered_entities"] = merged_entities
    
    # Update control flow based on reflection decision
    state["should_continue"] = reflection_result.get("should_continue", True)
    
    logger.log_info("Reflection complete", {
        "total_entities": len(merged_entities),
        "should_continue": state["should_continue"]
    })
    
    # Increment depth after completing current iteration
    # This ensures the next iteration uses the correct depth for query generation
    state["current_depth"] += 1
    logger.log_info("Depth incremented after analysis", {
        "new_depth": state["current_depth"]
    })
    
    return state