"""LangGraph workflow definition for deep research agent."""

from langgraph.graph import StateGraph, END

from ..models.state import AgentState
from .nodes.initialize import initialize_session
from .nodes.web_search import execute_web_search
from .nodes.generate_queries import generate_search_queries
from .nodes.connect import map_connections
from .nodes.analyze import analyze_and_reflect
from .nodes.synthesize import synthesize_report
from .edges.routing import should_continue_research

def create_research_graph() -> StateGraph:
    """
    Create the LangGraph workflow for deep research.
    
    The workflow implements a streamlined search and analysis strategy:
    1. Initialize session - Set up state with defaults
    2. Generate initial queries - Create broad search queries
    3. Execute searches - Parallel web searches
    4. Analyze and reflect - Extract insights and assess progress
    5. Decision point - Continue or finalize based on:
       - Max depth reached
       - Reflection recommendation
       - Stagnation detection
    6. If continue: generate refined queries and loop back to step 3
    7. If finalize: map entity connections and synthesize final report
    
    The finalization path ensures entity graph is always populated before synthesis.
    
    Returns:
        Compiled StateGraph
    """
    # Create the graph with proper state type
    workflow = StateGraph(AgentState)
    
    # Add nodes in logical execution order
    _add_workflow_nodes(workflow)
    
    # Define edges between nodes
    _add_workflow_edges(workflow)
    
    # Set entry point
    workflow.set_entry_point("initialize")
    
    return workflow.compile()


def _add_workflow_nodes(workflow: StateGraph) -> None:
    """
    Add all workflow nodes to the graph.
    
    Args:
        workflow: StateGraph instance to add nodes to
    """
    workflow.add_node("initialize", initialize_session)
    workflow.add_node("generate_queries", generate_search_queries)
    workflow.add_node("execute_search", execute_web_search)
    workflow.add_node("analyze_and_reflect", analyze_and_reflect)
    workflow.add_node("map_connections", map_connections)
    workflow.add_node("synthesize_report", synthesize_report)


def _add_workflow_edges(workflow: StateGraph) -> None:
    """
    Add all edges (transitions) between nodes.
    
    Args:
        workflow: StateGraph instance to add edges to
    """
    # Linear flow from start through initial search
    workflow.add_edge("initialize", "generate_queries")
    workflow.add_edge("generate_queries", "execute_search")
    workflow.add_edge("execute_search", "analyze_and_reflect")
    
    # Conditional routing after analysis
    workflow.add_conditional_edges(
        "analyze_and_reflect",
        should_continue_research,
        {
            "continue_search": "generate_queries",  # Loop back for more searches
            "finalize": "map_connections",  # Map connections then synthesize
        }
    )
    
    # Connection mapping always leads to synthesis (when finalizing)
    workflow.add_edge("map_connections", "synthesize_report")
    
    # Report synthesis ends the workflow
    workflow.add_edge("synthesize_report", END)


# Create the compiled graph
research_graph = create_research_graph()

