"""
OpenAI service for web search and structured output using the Agents SDK.

This module provides a high-level interface to OpenAI's Agents SDK,
supporting:
- Web search with structured output
- Search query generation
- Entity connection mapping
- Automatic token tracking and logging
"""

import time
from typing import List, Optional

from agents import Agent, ModelSettings, Runner, RunConfig, WebSearchTool, AgentOutputSchema
from openai.types.responses.web_search_tool_param import UserLocation
from openai.types.shared.reasoning import Reasoning

from ...config.settings import settings
from ...models.search_result import (
    WebSearchOutput,
    WebSearchSource,
    SearchQueriesList,
    ConnectionMappingOutput,
)
from ...observability.logger import DetailedLogger
from ...prompts import (
    build_web_search_instructions,
    build_query_generation_instructions,
    build_query_generation_prompt,
)
from ...utils.helpers import extract_tokens


class OpenAIService:
    """Service for interacting with OpenAI models using the Agents SDK."""
    
    def __init__(
        self, 
        api_key: Optional[str] = None, 
        session_id: Optional[str] = None,
        operation: str = "web_search"
    ):
        """Initialize the OpenAI service.
        
        Args:
            api_key: OpenAI API key (defaults to settings)
            session_id: Session ID for logging
            operation: Operation name for loading model config from YAML
                      Options: 'web_search', 'synthesis', 'entity_merge', 'graph_merge', 'connection_mapping'
        """        
        self.session_id = session_id
        self.operation = operation
        
        # Load model configuration from YAML
        self.config = settings.get_model_config(operation)
        self.model = self.config.get("model")
        self.verbosity = self.config.get("verbosity", "medium")
        
        # Lazy import to avoid circular dependency
        self._logger = DetailedLogger(self.session_id)
    
    async def web_search(self, query: str, context: Optional[str] = None) -> WebSearchOutput:
        """Execute web search using OpenAI Agents SDK with structured output.
        
        Args:
            query: Search query
            context: Additional context for the search
            
        Returns:
            WebSearchOutput with findings and sources
        """
        # Get web search specific config
        web_config = settings.get_model_config("web_search")
        
        agent = Agent(
            name="DueDiligenceResearcher",
            model=self.model,
            instructions=build_web_search_instructions(context, include_context=True),
            tools=[WebSearchTool(
                search_context_size=web_config.get("context_size", "low"),
                user_location=UserLocation(
                    type="approximate"
                )
            )],
            # output_type=AgentOutputSchema(WebSearchOutput, strict_json_schema=False),
            output_type=WebSearchOutput,
            model_settings=ModelSettings(verbosity=self.verbosity),
        )
        
        start_time = time.time()
        result = await Runner.run(agent, query, run_config=RunConfig(tracing_disabled=True))
        extracted_tokens = await extract_tokens(result)
        duration_ms = (time.time() - start_time) * 1000
        
        output: WebSearchOutput = result.final_output
        

        
        # Convert structured output sources to Source objects
        sources = [WebSearchSource(url=src.url, title=src.title) for src in output.sources]
        
        self._logger.log_llm_call(
            operation="web_search",
            model=self.model,
            input_data={"query": query, "context": context},
            output_data={
                "search_result": output.search_result,
                "search_result_length": len(output.search_result),
                "sources_count": len(sources)
            },
            duration_ms=duration_ms,
            tokens=extracted_tokens
        )
        
        if not output.search_result:
            print(f"⚠️  Warning: Incomplete output for query: {query}")
            self._logger.log_warning(f"Incomplete output for query: {query}")

        
        return output
    
    async def generate_search_queries(
        self,
        subject: str,
        context: Optional[str] = None,
        discovered_info: Optional[List[str]] = None,
        depth: int = 0,
        strategic_context: Optional[str] = None
    ) -> SearchQueriesList:
        """Generate search queries using OpenAI Agents SDK with structured output.
        
        Args:
            subject: Research subject
            context: Additional context
            discovered_info: Previously discovered information
            depth: Current search depth
            strategic_context: Strategic context from analysis
            
        Returns:
            SearchQueriesList with list of search queries
        """
        
        print("########################################################")
        print(f"Building query generation agent with model: {self.model}")
        print("########################################################")
        
        agent = Agent(
            name="QueryStrategist",
            model=self.model,
            instructions=build_query_generation_instructions(settings.max_queries_per_depth),
            output_type=SearchQueriesList,
            # model_settings=ModelSettings(reasoning=Reasoning(effort="low"), verbosity="low"),
            model_settings=ModelSettings(verbosity=self.verbosity),
        )
        
        try:
            start_time = time.time()
            user_prompt = build_query_generation_prompt(
                subject=subject,
                context=context,
                depth=depth,
                strategic_context=strategic_context,
                discovered_info=discovered_info
            )
            result = await Runner.run(agent, user_prompt, run_config=RunConfig(tracing_disabled=True))
            extracted_tokens = await extract_tokens(result)
            duration_ms = (time.time() - start_time) * 1000
            output: SearchQueriesList = result.final_output

            log_tokens = {
                "prompt": extracted_tokens.get("input_tokens", 0),
                "completion": extracted_tokens.get("output_tokens", 0),
                "total": extracted_tokens.get("total_tokens", 0),
                "cached": extracted_tokens.get("cached_tokens", 0),
                "reasoning": extracted_tokens.get("reasoning_tokens", 0),
            }
            
            self._logger.log_llm_call(
                operation="query_generation",
                model=self.model,
                input_data={"subject": subject, "depth": depth, "context": context},
                output_data={"queries": output.queries},
                duration_ms=duration_ms,
                tokens=log_tokens
            )
            
            return output
            
        except Exception as e:
            raise ValueError(f"Query generation failed: {str(e)}")
    
    async def map_entity_connections(
        self,
        discovered_entities: dict,
        reflection_memory: List[dict],
        existing_graph: dict
    ) -> ConnectionMappingOutput:
        """
        Map connections between entities using OpenAI Agents SDK.
        
        Args:
            discovered_entities: Dictionary of discovered entities
            reflection_memory: List of all reflection outputs
            existing_graph: Current entity graph structure
            
        Returns:
            ConnectionMappingOutput with nodes, edges, and patterns
        """
        # Build comprehensive context for connection mapping
        context = self._build_connection_context(
            discovered_entities,
            reflection_memory,
            existing_graph
        )
        
        instructions = """You are an expert intelligence analyst specializing in entity relationship mapping.

Your task is to analyze discovered entities and relationships to build a comprehensive entity graph.

You must:
1. Create graph nodes for all entities (persons, organizations, events, locations)
2. Create graph edges representing relationships between entities
3. Identify patterns in the connections (e.g., overlapping relationships, timing patterns)
4. Flag suspicious patterns automatically (conflicts of interest, hidden relationships, timing anomalies)
5. Assess key entities based on centrality to investigation (importance scoring with reasoning)

For graph structure:
- Each node needs: id, name, type, attributes
- Each edge needs: source, target, relationship, confidence, attributes
- Node IDs should be lowercase, no spaces (e.g., "sam_bankman_fried")
- Relationships should be descriptive (e.g., "founded_and_controlled", "romantic_and_professional")

For pattern detection:
- Look for conflicts of interest (dual roles, related party transactions)
- Identify timing patterns (coordinated actions, suspicious timing)
- Flag hidden or undisclosed relationships
- Note discrepancies between stated and actual relationships

For entity importance:
- Consider: connection count, involvement in red flags, centrality to subject
- Score 0-1 with clear reasoning"""
        
        # Get connection mapping config
        conn_config = settings.get_model_config("connection_mapping")
        
        agent = Agent(
            name="ConnectionMapper",
            model=conn_config.get("model"),
            instructions=instructions,
            output_type=AgentOutputSchema(ConnectionMappingOutput, strict_json_schema=False),
            model_settings=ModelSettings(verbosity=conn_config.get("verbosity", "medium")),
        )
        
        start_time = time.time()
        result = await Runner.run(agent, context, run_config=RunConfig(tracing_disabled=True))
        extracted_tokens = await extract_tokens(result)
        duration_ms = (time.time() - start_time) * 1000
        
        output: ConnectionMappingOutput = result.final_output
        
        self._logger.log_llm_call(
            operation="connection_mapping",
            model=conn_config.get("model"),
            input_data={"entities_count": len(discovered_entities), "existing_nodes": len(existing_graph.get("nodes", []))},
            output_data={
                "new_nodes": len(output.new_nodes),
                "new_edges": len(output.new_edges),
                "patterns": len(output.patterns_identified),
                "suspicious_patterns": len(output.suspicious_patterns)
            },
            duration_ms=duration_ms,
            tokens=extracted_tokens
        )
        
        return output
    
    def _build_connection_context(
        self,
        discovered_entities: dict,
        reflection_memory: List[dict],
        existing_graph: dict
    ) -> str:
        """Build context prompt for connection mapping."""
        context = "# Entity Relationship Mapping Task\n\n"
        
        # Add discovered entities
        context += "## Discovered Entities\n"
        for entity_name, entity_data in discovered_entities.items():
            context += f"- {entity_name}: {entity_data}\n"
        
        # Add relationships from all reflections
        context += "\n## Discovered Relationships\n"
        for i, reflection in enumerate(reflection_memory):
            relationships = reflection.get("new_relationships", [])
            if relationships:
                context += f"\nIteration {i}:\n"
                for rel in relationships:
                    context += f"- {rel}\n"
        
        # Add existing graph context
        if existing_graph.get("nodes"):
            context += f"\n## Existing Graph\n"
            context += f"Current nodes: {len(existing_graph.get('nodes', []))}\n"
            context += f"Current edges: {len(existing_graph.get('edges', []))}\n"
        
        # Add red flags for suspicious pattern detection
        context += "\n## Known Red Flags\n"
        for reflection in reflection_memory:
            red_flags = reflection.get("red_flags", [])
            for rf in red_flags:
                finding = rf.get("finding") if isinstance(rf, dict) else rf
                context += f"- {finding}\n"
        
        context += "\n## Your Task\n"
        context += "Analyze all entities and relationships to create/update the entity graph. "
        context += "Identify patterns and flag suspicious connections. "
        context += "Assess importance of key entities.\n"
        
        return context

