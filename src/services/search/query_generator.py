"""
Search query generation service using Claude for intelligent query refinement.

This module handles both initial and refined query generation:
- Initial queries: Broad coverage for baseline research
- Refined queries: Targeted queries based on reflection analysis
"""

from typing import List, Optional, Dict, Any

from ...config.settings import settings
from ...services.llm.claude_service import ClaudeService
from ...models.search_result import SearchQueriesList
from ...prompts.query_generation import (
    INITIAL_QUERY_SYSTEM_PROMPT,
    REFINED_QUERY_SYSTEM_PROMPT,
    build_initial_query_prompt,
    build_refined_query_prompt,
)


class QueryGenerator:
    """
    Generates search queries using Claude with reflection-based strategy.
    
    This class implements a two-phase query generation approach:
    1. Initial queries: Broad, comprehensive coverage
    2. Refined queries: Targeted, reflection-guided queries
    
    The query strategy evolves based on what has been discovered,
    prioritizing red flags and information gaps.
    """
    
    def __init__(self, session_id: Optional[str] = None):
        """
        Initialize the query generator.
        
        Args:
            session_id: Session ID for logging and tracking
        """
        self.claude = ClaudeService(session_id=session_id, operation="query_generation")
        self.session_id = session_id
        self.max_queries = settings.max_queries_per_depth
    
    async def generate_initial_queries(
        self,
        subject: str,
        context: Optional[str] = None
    ) -> List[str]:
        """
        Generate initial broad queries for depth 0 research.
        
        Uses Claude to generate comprehensive initial queries covering:
        - Biographical basics
        - Professional history
        - Financial information
        - Legal/regulatory issues
        - Behavioral patterns
        
        Args:
            subject: Research subject
            context: Additional context about subject
            
        Returns:
            List of initial search queries
        """
        prompt = build_initial_query_prompt(
            subject=subject,
            context=context,
            max_queries=self.max_queries
        )
        
        result = await self.claude.extract_structured(
            text=prompt,
            schema=SearchQueriesList,
            system_prompt=INITIAL_QUERY_SYSTEM_PROMPT
        )
        
        return result.get("queries", [f"{subject} background information"])
    
    async def generate_refined_queries(
        self,
        subject: str,
        reflection_memory: List[Dict[str, Any]],
        queries_executed: List[str],
        discovered_entities: Dict[str, Any],
        current_depth: int
    ) -> List[str]:
        """
        Generate refined queries based on reflection's query strategy.
        
        Uses latest reflection's query_strategy text to:
        - Prioritize red flag topics
        - Explore suggested angles
        - Target new entities
        - Avoid repeating previous queries
        
        Args:
            subject: Research subject
            reflection_memory: All reflection outputs
            queries_executed: Previously executed queries (for deduplication)
            discovered_entities: All discovered entities
            current_depth: Current search depth
            
        Returns:
            List of refined search queries
        """
        # Get latest reflection
        if not reflection_memory:
            # Fallback to initial queries
            return await self.generate_initial_queries(subject)
        
        latest_reflection = reflection_memory[-1]
        
        # Get query strategy from reflection
        query_strategy = latest_reflection.get("query_strategy", "")
        
        prompt = build_refined_query_prompt(
            subject=subject,
            query_strategy=query_strategy,
            queries_executed=queries_executed,
            discovered_entities_count=len(discovered_entities),
            current_depth=current_depth,
            max_queries=self.max_queries
        )
        
        result = await self.claude.extract_structured(
            text=prompt,
            schema=SearchQueriesList,
            system_prompt=REFINED_QUERY_SYSTEM_PROMPT
        )
        
        return result.get("queries", [])