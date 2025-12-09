"""General helper utilities for formatting and session management."""

from datetime import datetime
from typing import Dict, Any


def format_duration(seconds: float) -> str:
    """Format duration in seconds to human-readable string.
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted string (e.g., "2m 34s")
    """
    if seconds < 60:
        return f"{seconds:.1f}s"
    
    minutes = int(seconds // 60)
    remaining_seconds = int(seconds % 60)
    
    if minutes < 60:
        return f"{minutes}m {remaining_seconds}s"
    
    hours = minutes // 60
    remaining_minutes = minutes % 60
    return f"{hours}h {remaining_minutes}m"


def truncate_text(text: str, max_length: int = 100) -> str:
    """Truncate text to maximum length.
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        
    Returns:
        Truncated text with ellipsis if needed
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - 3] + "..."


def generate_session_id() -> str:
    """
    Generate a unique session ID based on current timestamp.
    
    Format: sess_YYYYMMDD_HHMMSS
    
    Returns:
        Session ID string
    """
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    return f"sess_{timestamp}"


async def extract_tokens(response) -> Dict[str, int]:
    """
    Extract token usage information from OpenAI Agents SDK response.
    
    Args:
        response: Response object from OpenAI Agents SDK
        
    Returns:
        Dictionary with token usage counts:
        - input_tokens: Number of input tokens
        - output_tokens: Number of output tokens
        - total_tokens: Sum of input and output tokens
        - cached_tokens: Number of cached tokens
        - reasoning_tokens: Number of reasoning tokens (for o1/o3 models)
    """
    usage = response.context_wrapper.usage
    return {
        "input_tokens": usage.input_tokens,
        "output_tokens": usage.output_tokens,
        "total_tokens": usage.input_tokens + usage.output_tokens,
        "cached_tokens": usage.input_tokens_details.cached_tokens,
        "reasoning_tokens": usage.output_tokens_details.reasoning_tokens,
    }

