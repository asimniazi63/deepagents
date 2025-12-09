"""Research-specific utility functions for entity merging, graph operations, and stagnation detection."""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
from agents import Agent, ModelSettings, Runner, RunConfig, AgentOutputSchema

from ..config.settings import settings

logger = logging.getLogger(__name__)


async def retry_agent_execution(
    agent_func,
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    *args,
    **kwargs
):
    """
    Retry wrapper for agent execution with exponential backoff.
    
    Args:
        agent_func: The async function to execute (should return a Runner.run result)
        max_retries: Maximum number of retry attempts (default: 3)
        initial_delay: Initial delay between retries in seconds (default: 1.0)
        backoff_factor: Exponential backoff multiplier (default: 2.0)
        *args, **kwargs: Arguments to pass to agent_func
        
    Returns:
        The result from agent_func
        
    Raises:
        The last exception encountered if all retries fail
    """
    last_exception = None
    delay = initial_delay
    
    for attempt in range(max_retries):
        try:
            result = await agent_func(*args, **kwargs)
            if attempt > 0:
                logger.info(f"Agent execution succeeded on attempt {attempt + 1}")
            return result
            
        except Exception as e:
            last_exception = e
            logger.warning(
                f"Agent execution failed (attempt {attempt + 1}/{max_retries}): {str(e)}"
            )
            
            # Don't sleep after the last attempt
            if attempt < max_retries - 1:
                logger.info(f"Retrying in {delay:.1f} seconds...")
                await asyncio.sleep(delay)
                delay *= backoff_factor
    
    # All retries exhausted
    logger.error(f"Agent execution failed after {max_retries} attempts")
    raise last_exception


class EntityMergeOutput(BaseModel):
    """Output schema for entity merging."""
    merged_entities: Dict[str, Any] = Field(
        description="Merged entity dictionary with deduplicated entries. Keys are entity names, values contain metadata."
    )
    entities_extracted: List[str] = Field(
        description="List of entity names extracted from the analysis summary"
    )


async def merge_entities_with_llm(
    existing_entities: Dict[str, Any],
    analysis_summary: str,
    session_id: str
) -> Dict[str, Any]:
    """
    Extract entities from analysis text and merge with existing using OpenAI.
    
    Two-step process:
    1. Extract entities from analysis_summary text
    2. Merge with existing entities, handling deduplication
    
    Args:
        existing_entities: Current entity dictionary
        analysis_summary: Text from Claude's reflection containing entities
        session_id: Session ID for logging
        
    Returns:
        Updated entity dictionary with merged entries
    """
    if not analysis_summary:
        return existing_entities or {}
    
    instructions = """You are an entity extraction and deduplication expert.

Your task:
1. Extract all entities from the analysis summary (persons, organizations, events, locations)
2. Merge them with existing entities, handling duplicates intelligently

Entity matching rules:
- "John Smith" = "J. Smith" (name variations)
- "FTX" = "FTX Exchange" (abbreviations)
- "Sam Bankman-Fried" = "SBF" (nicknames)
- If uncertain (confidence < 0.7), treat as separate entity

For merged entities:
- Keep most complete name
- Increment mention count
- Preserve all metadata

Return:
- merged_entities: Complete entity dictionary (existing + new, deduplicated)
- entities_extracted: List of entity names found in analysis summary"""
    
    prompt = f"""# Entity Extraction and Merging

## Existing Entities
{existing_entities if existing_entities else "None"}

## Analysis Summary (extract entities from this text)
{analysis_summary}

Extract all entities from the analysis summary and merge with existing entities."""
    
    # Get entity merge config from YAML
    entity_config = settings.get_model_config("entity_merge")
    
    # Get retry settings from OpenAI defaults
    openai_defaults = settings.yaml_config.get("openai_defaults", {})
    max_retries = openai_defaults.get("max_retries", 3)
    
    agent = Agent(
        name="EntityMerger",
        model=entity_config.get("model"),
        instructions=instructions,
        output_type=AgentOutputSchema(EntityMergeOutput, strict_json_schema=False),
        model_settings=ModelSettings(verbosity=entity_config.get("verbosity", "medium")),
    )
    
    # Execute with retry logic
    async def run_entity_merge():
        return await Runner.run(agent, prompt, run_config=RunConfig(tracing_disabled=True))
    
    result = await retry_agent_execution(
        run_entity_merge,
        max_retries=max_retries,
        initial_delay=1.0,  # Standard delay
        backoff_factor=2.0  # Standard exponential backoff
    )
    output: EntityMergeOutput = result.final_output
    
    return output.merged_entities if output.merged_entities else existing_entities


class GraphMergeOutput(BaseModel):
    """Output schema for graph merging."""
    merged_graph: Dict[str, Any] = Field(
        description="Merged graph with deduplicated nodes and edges. Structure: {'nodes': [...], 'edges': [...]}"
    )
    nodes_added: int = Field(description="Number of new nodes added")
    edges_added: int = Field(description="Number of new edges added")
    nodes_merged: int = Field(description="Number of nodes merged with existing")


async def merge_graph_with_llm(
    existing_graph: Dict[str, Any],
    new_nodes: List[Dict[str, Any]],
    new_edges: List[Dict[str, Any]],
    session_id: str
) -> Dict[str, Any]:
    """
    Merge new graph nodes and edges with existing graph using OpenAI.
    
    Handles node deduplication and edge consolidation using LLM reasoning.
    
    Args:
        existing_graph: Current graph structure {"nodes": [...], "edges": [...]}
        new_nodes: New nodes to add
        new_edges: New edges to add
        session_id: Session ID for logging
        
    Returns:
        Updated graph structure with deduplicated nodes and edges
    """
    # Initialize empty graph if needed
    if not existing_graph:
        existing_graph = {"nodes": [], "edges": []}
    
    if not new_nodes and not new_edges:
        return existing_graph
    
    # Validate existing graph structure
    if "nodes" not in existing_graph:
        existing_graph["nodes"] = []
    if "edges" not in existing_graph:
        existing_graph["edges"] = []
    
    instructions = """You are a graph deduplication expert. Merge new nodes and edges into existing graph.

Node deduplication rules:
1. Match by 'id' field (case-insensitive, normalized)
2. "sam_bankman_fried" = "sbf" = "Sam-Bankman-Fried" (same entity)
3. For duplicates: merge attributes, keep most complete info
4. Increment relationship count for matched nodes

Edge deduplication rules:
1. Match by source + target + relationship (all three must match)
2. For duplicates: keep edge with higher confidence
3. Ensure all edge source/target IDs exist in nodes list

Return the merged graph in the 'merged_graph' field as:
{
  "merged_graph": {"nodes": [...], "edges": [...]},
  "nodes_added": <count of new nodes added>,
  "edges_added": <count of new edges added>,
  "nodes_merged": <count of nodes merged with existing>
}"""
    
    prompt = f"""# Graph Merging Task

## Existing Graph
Nodes: {len(existing_graph.get('nodes', []))}
Edges: {len(existing_graph.get('edges', []))}
{existing_graph}

## New Nodes to Add
{new_nodes}

## New Edges to Add
{new_edges}

Merge new nodes and edges into existing graph, handling duplicates intelligently."""
    
    # Get graph merge config from YAML
    graph_config = settings.get_model_config("graph_merge")
    
    # Get retry settings from OpenAI defaults
    openai_defaults = settings.yaml_config.get("openai_defaults", {})
    max_retries = openai_defaults.get("max_retries", 3)
    
    agent = Agent(
        name="GraphMerger",
        model=graph_config.get("model"),
        instructions=instructions,
        output_type=AgentOutputSchema(GraphMergeOutput, strict_json_schema=False),
        model_settings=ModelSettings(verbosity=graph_config.get("verbosity", "medium")),
    )
    
    # Execute with retry logic
    async def run_graph_merge():
        return await Runner.run(agent, prompt, run_config=RunConfig(tracing_disabled=True))
    
    result = await retry_agent_execution(
        run_graph_merge,
        max_retries=max_retries,
        initial_delay=1.0,  # Standard delay
        backoff_factor=2.0  # Standard exponential backoff
    )
    output: GraphMergeOutput = result.final_output
    
    return output.merged_graph if output.merged_graph else existing_graph


def check_stagnation(
    reflection_memory: List[Dict[str, Any]],
    n_iterations: Optional[int] = None
) -> bool:
    """
    Check if research has stagnated (no significant progress in last N iterations).
    
    Stagnation indicators:
    - Analysis mentions "no new entities" or "no significant findings"
    - Very short analysis summaries (< 200 chars)
    - Repeated similar findings across iterations
    
    Args:
        reflection_memory: List of reflection outputs
        n_iterations: Number of iterations to check (defaults to settings value)
        
    Returns:
        True if stagnated, False otherwise
    """
    if n_iterations is None:
        n_iterations = settings.stagnation_check_iterations
    
    # Validate inputs
    if not reflection_memory or n_iterations <= 0:
        return False
    
    # Need at least N reflections to check
    if len(reflection_memory) < n_iterations:
        return False
    
    # Check last N reflections for significant findings
    recent_reflections = reflection_memory[-n_iterations:]
    
    # Define stagnation indicators
    stagnation_indicators = [
        "no new entities",
        "no significant findings", 
        "limited new information",
        "no new information",
        "entities discovered: none",
        "entities discovered:\nnone",
        "nothing new discovered"
    ]
    
    stagnant_count = 0
    for reflection in recent_reflections:
        analysis = reflection.get("analysis_summary", "").lower()
        
        # Check for stagnation indicators
        has_indicator = any(indicator in analysis for indicator in stagnation_indicators)
        is_too_short = len(analysis) < 200  # Very short analysis suggests little found
        
        if has_indicator or is_too_short:
            stagnant_count += 1
    
    # If majority of recent iterations show stagnation, return True
    return stagnant_count >= n_iterations

