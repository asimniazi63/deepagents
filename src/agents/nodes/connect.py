"""Connection mapping node for LangGraph workflow."""

from ...models.state import AgentState
from ...services.llm.openai_service import OpenAIService
from ...observability.logger import log_node_execution, DetailedLogger
from ...utils.research_utils import merge_graph_with_llm


@log_node_execution
async def map_connections(state: AgentState) -> AgentState:
    """
    Map connections between entities using OpenAI for relationship analysis.
    
    This node:
    1. Analyzes all discovered entities and relationships
    2. Builds/updates entity graph (nodes + edges)
    3. Identifies patterns in connections
    4. Flags suspicious patterns automatically
    5. Assesses key entities by importance
    
    Args:
        state: Current agent state
        
    Returns:
        Updated agent state with connection mappings and graph
    """
    session_id = state.get("session_id", "unknown")
    logger = DetailedLogger(session_id)
    logger.log_info("Starting connection mapping analysis")
    
    # Validate we have entities to map
    if not state.get("discovered_entities"):
        logger.log_warning("No entities discovered yet, skipping connection mapping")
        return state
    
    # Initialize OpenAI service
    openai_service = OpenAIService(session_id=state["session_id"])
    
    # Execute connection mapping
    logger.log_info("Executing OpenAI connection mapping", {
        "entities_count": len(state.get("discovered_entities", {})),
        "existing_nodes": len(state.get("entity_graph", {}).get("nodes", []))
    })
    
    connection_output = await openai_service.map_entity_connections(
        discovered_entities=state.get("discovered_entities", {}),
        reflection_memory=state.get("reflection_memory", []),
        existing_graph=state.get("entity_graph", {"nodes": [], "edges": []})
    )
    
    logger.log_info("Connection mapping complete", {
        "new_nodes": len(connection_output.new_nodes),
        "new_edges": len(connection_output.new_edges),
        "patterns_found": len(connection_output.patterns_identified),
        "suspicious_patterns": len(connection_output.suspicious_patterns)
    })
    
    # Merge graph with LLM assistance
    logger.log_info("Merging graph with LLM deduplication")
    merged_graph = await merge_graph_with_llm(
        existing_graph=state.get("entity_graph", {"nodes": [], "edges": []}),
        new_nodes=[node.model_dump() for node in connection_output.new_nodes],
        new_edges=[edge.model_dump() for edge in connection_output.new_edges],
        session_id=state["session_id"]
    )
    
    # Update state with graph and patterns
    state["entity_graph"] = merged_graph
    
    # Add suspicious patterns to red flags
    state["risk_indicators"]["red_flags"].extend(connection_output.suspicious_patterns)
    
    # Store key entities for prioritization
    state["key_entities"] = [entity.model_dump() for entity in connection_output.key_entities]
    
    logger.log_info("Connection mapping integrated into state", {
        "total_nodes": len(merged_graph.get("nodes", [])),
        "total_edges": len(merged_graph.get("edges", [])),
        "key_entities": len(connection_output.key_entities)
    })
    
    return state
