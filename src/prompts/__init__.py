"""Centralized LLM prompts used across the research agents.

Each logical prompt (or closely related prompt family) has its own module so
that:
- The full text lives in one place
- It is easy to see where the prompt is used
- Prompts can be iterated on without hunting through node/service code
"""

from .web_search import (
    build_web_search_instructions,
    build_query_generation_instructions,
    build_query_generation_prompt
)
from .synthesis import (
    build_synthesis_prompt,
    SYNTHESIS_INSTRUCTIONS,
)
from .analysis import (
    build_reflection_prompt,
    ANALYSIS_SYSTEM_PROMPT,
)
from .query_generation import (
    INITIAL_QUERY_SYSTEM_PROMPT,
    REFINED_QUERY_SYSTEM_PROMPT,
    build_initial_query_prompt,
    build_refined_query_prompt,
)

__all__ = [
    # Web search prompts
    "build_web_search_instructions",
    "build_query_generation_instructions",
    "build_query_generation_prompt",
    # Synthesis prompts
    "build_synthesis_prompt",
    "SYNTHESIS_INSTRUCTIONS",
    # Analysis prompts
    "build_reflection_prompt",
    "ANALYSIS_SYSTEM_PROMPT",
    # Query generation prompts
    "INITIAL_QUERY_SYSTEM_PROMPT",
    "REFINED_QUERY_SYSTEM_PROMPT",
    "build_initial_query_prompt",
    "build_refined_query_prompt",
]


