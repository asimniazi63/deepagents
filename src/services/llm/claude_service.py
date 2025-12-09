"""
Claude service for risk analysis and structured extraction.

This module provides a high-level interface to Claude (Anthropic)
for analysis tasks that benefit from Claude's reasoning capabilities:
- Reflection and analysis
- Query generation and refinement
- Structured data extraction
"""

import time
from typing import Optional, Type, Dict, Any

from anthropic import AsyncAnthropic
from langchain_anthropic import ChatAnthropic
from pydantic import BaseModel

from ...config.settings import settings
from ...observability.logger import DetailedLogger


class ClaudeService:
    """Service for interacting with Claude for analysis tasks."""
    
    def __init__(
        self, 
        api_key: Optional[str] = None, 
        session_id: Optional[str] = None,
        operation: str = "analysis"
    ):
        """Initialize the Claude service.
        
        Args:
            api_key: Anthropic API key (defaults to settings)
            session_id: Session ID for logging
            operation: Operation name for loading model config from YAML
                      Options: 'query_generation', 'analysis'
        """
        self.client = AsyncAnthropic(api_key=api_key or settings.anthropic_api_key)
        self.session_id = session_id
        self.operation = operation
        
        # Load model configuration from YAML
        self.config = settings.get_model_config(operation)
        self.model = self.config.get("model")
        self.temperature = self.config.get("temperature", 0.1)
        self.max_tokens = self.config.get("max_tokens", 16384)
        self.max_retries = self.config.get("max_retries", 2)
        self.timeout = self.config.get("timeout", 300)  # Default 5 minutes (in seconds)
        
        # Initialize logger if session_id is provided
        self._logger = DetailedLogger(session_id) if session_id else None
    
    async def extract_structured(
        self,
        text: str,
            schema: Type[BaseModel],
            instruction: Optional[str] = None,
            system_prompt: Optional[str] = None
    ) -> BaseModel:
        """
        Extract structured data from text using Claude's structured outputs.
        
        Args:
            text: Text to extract from
            schema: Pydantic model schema to extract into
            instruction: Optional additional instructions
            system_prompt: Optional system prompt (defaults to extraction instructions)
            
        Returns:
            Instance of schema filled with extracted data
        """
        start_time = time.time()
        model = ChatAnthropic(
            model=self.model,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            max_retries=self.max_retries,
            timeout=self.timeout,
        )
        
        messages = [
            ("system", system_prompt),
            ("human", text + "\n\n" + (instruction or "")),
        ]
                
        try:
            structured_model = model.with_structured_output(schema, method="json_schema")
            result: schema = structured_model.invoke(messages)
            duration_ms = (time.time() - start_time) * 1000
        except Exception as e:
            if self._logger:
                self._logger.log_error("extract_structured", e, {
                    "schema": schema.__name__,
                    "text_length": len(text),
                    "operation": self.operation
                })
            raise e

        # Log LLM call if logger is available
        if self._logger:
            self._logger.log_llm_call(
                operation=f"extract_structured_{self.operation}",
                model=self.model,
                input_data={"text": text, "schema": schema, "instruction": instruction, "system_prompt": system_prompt},
                output_data=result.model_dump(),
                duration_ms=duration_ms,
            )
        return result.model_dump()
