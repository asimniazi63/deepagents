"""
Configuration settings for the Deep Research Agent.

This module provides centralized configuration management using:
1. Environment variables and .env file (for secrets/API keys)
2. YAML configuration file (for model settings and non-sensitive configs)

This separation follows security best practices:
- Secrets in .env
- Configuration in YAML
"""

from pathlib import Path
from typing import Optional, Dict, Any
import os
import yaml

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def load_yaml_config(yaml_path: Path = Path("config/models.yaml")) -> Dict[str, Any]:
    """
    Load YAML configuration file.
    
    Args:
        yaml_path: Path to YAML config file
        
    Returns:
        Dictionary with configuration data
    """
    if not yaml_path.exists():
        raise FileNotFoundError(
            f"Configuration file not found: {yaml_path}\n"
            f"Please create config/models.yaml for model configurations."
        )
    
    with open(yaml_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


class Settings(BaseSettings):
    """
    Application settings loaded from:
    1. Environment variables and .env file (secrets/API keys)
    2. YAML configuration file (model settings)
    """
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        validate_assignment=True,
        extra="ignore",  # Ignore extra environment variables
    )
    
    # =========================================================================
    # SECRETS (from .env only)
    # =========================================================================
    openai_api_key: str
    anthropic_api_key: str
    langfuse_public_key: Optional[str] = None
    langfuse_secret_key: Optional[str] = None
    langfuse_host: str = "https://cloud.langfuse.com"
    
    # =========================================================================
    # MODEL CONFIGURATIONS (loaded from YAML)
    # =========================================================================
    # These will be populated from YAML after initialization
    yaml_config: Dict[str, Any] = {}
    
    # Agent Configuration (can override via env vars)
    max_search_depth: Optional[int] = None
    max_queries_per_depth: Optional[int] = None
    max_concurrent_searches: Optional[int] = None
    stagnation_check_iterations: Optional[int] = None
    
    # Logging (can override via env vars)
    log_level: Optional[str] = None
    log_dir: Optional[Path] = None
    reports_dir: Optional[Path] = None
    debug: Optional[bool] = None
    
    def __init__(self, **kwargs):
        """Initialize settings by loading .env and YAML config."""
        super().__init__(**kwargs)
        
        # Load YAML configuration
        self.yaml_config = load_yaml_config()
        
        # Apply YAML defaults if not set via environment variables
        self._apply_yaml_defaults()
    
    def _apply_yaml_defaults(self):
        """Apply YAML configuration as defaults if not set via env vars."""
        # Workflow settings
        workflow = self.yaml_config.get("workflow", {})
        if self.max_search_depth is None:
            self.max_search_depth = workflow.get("max_search_depth", 4)
        if self.max_queries_per_depth is None:
            self.max_queries_per_depth = workflow.get("max_queries_per_depth", 5)
        if self.max_concurrent_searches is None:
            self.max_concurrent_searches = workflow.get("max_concurrent_searches", 5)
        if self.stagnation_check_iterations is None:
            self.stagnation_check_iterations = workflow.get("stagnation_check_iterations", 2)
        
        # Logging settings
        logging = self.yaml_config.get("logging", {})
        if self.log_level is None:
            self.log_level = logging.get("level", "INFO")
        if self.log_dir is None:
            self.log_dir = Path(logging.get("log_dir", "logs"))
        if self.reports_dir is None:
            self.reports_dir = Path(logging.get("reports_dir", "reports"))
        if self.debug is None:
            self.debug = logging.get("debug", False)
    
    def get_model_config(self, operation: str) -> Dict[str, Any]:
        """
        Get model configuration for a specific operation.
        
        Args:
            operation: Operation name (e.g., 'query_generation', 'analysis', 'web_search')
            
        Returns:
            Dictionary with model configuration
            
        Example:
            >>> settings.get_model_config("query_generation")
            {
                "provider": "anthropic",
                "model": "claude-sonnet-4-20250514",
                "temperature": 0.3,
                "max_tokens": 4096,
                ...
            }
        """
        config = self.yaml_config.get(operation, {})
        if not config:
            raise ValueError(
                f"Model configuration for '{operation}' not found in YAML config.\n"
                f"Available operations: {list(self.yaml_config.keys())}"
            )
        return config
    
    @field_validator('max_search_depth')
    @classmethod
    def validate_max_depth(cls, v: Optional[int]) -> Optional[int]:
        """Validate max_search_depth is within reasonable bounds."""
        if v is None:
            return v
        if v < 1:
            raise ValueError("max_search_depth must be at least 1")
        if v > 10:
            raise ValueError("max_search_depth should not exceed 10 (performance concerns)")
        return v
    
    @field_validator('max_queries_per_depth')
    @classmethod
    def validate_max_queries(cls, v: Optional[int]) -> Optional[int]:
        """Validate max_queries_per_depth is within reasonable bounds."""
        if v is None:
            return v
        if v < 1:
            raise ValueError("max_queries_per_depth must be at least 1")
        if v > 20:
            raise ValueError("max_queries_per_depth should not exceed 20 (API rate limits)")
        return v
    
    @field_validator('max_concurrent_searches')
    @classmethod
    def validate_concurrent(cls, v: Optional[int]) -> Optional[int]:
        """Validate max_concurrent_searches is within reasonable bounds."""
        if v is None:
            return v
        if v < 1:
            raise ValueError("max_concurrent_searches must be at least 1")
        if v > 5:
            raise ValueError("max_concurrent_searches should not exceed 5 (API rate limits)")
        return v
    
    @field_validator('stagnation_check_iterations')
    @classmethod
    def validate_stagnation(cls, v: Optional[int]) -> Optional[int]:
        """Validate stagnation_check_iterations is within reasonable bounds."""
        if v is None:
            return v
        if v < 1:
            raise ValueError("stagnation_check_iterations must be at least 1")
        if v > 5:
            raise ValueError("stagnation_check_iterations should not exceed 5")
        return v
    
    def __repr__(self) -> str:
        """Hide sensitive data in logs."""
        return "Settings(**REDACTED**)"


# Global settings instance
settings = Settings()

os.environ["OPENAI_API_KEY"] = settings.openai_api_key
os.environ["ANTHROPIC_API_KEY"] = settings.anthropic_api_key
if settings.langfuse_public_key:
    os.environ["LANGFUSE_PUBLIC_KEY"] = settings.langfuse_public_key
if settings.langfuse_secret_key:
    os.environ["LANGFUSE_SECRET_KEY"] = settings.langfuse_secret_key
os.environ["LANGFUSE_HOST"] = settings.langfuse_host

# =============================================================================
# CONFIGURE DEFAULT OPENAI CLIENT FOR AGENTS SDK
# =============================================================================
# The Agents SDK supports setting a default AsyncOpenAI client that will be
# used by all Runner.run() calls. We configure it with proper timeouts from
# the openai_defaults section in config/models.yaml

import httpx
from openai import AsyncOpenAI
from agents import set_default_openai_client

# Get OpenAI defaults from config
_openai_defaults = settings.yaml_config.get("openai_defaults", {})
_timeout = _openai_defaults.get("timeout", 300)  # Default 5 minutes
_max_retries = _openai_defaults.get("max_retries", 3)  # Default 3 retries
_connect_timeout = _openai_defaults.get("connect_timeout", 60)  # Default 60s
_write_timeout = _openai_defaults.get("write_timeout", 30)  # Default 30s

# Configure AsyncOpenAI client with timeout and retry settings
# This client will be used by ALL OpenAI Agents SDK operations
default_openai_client = AsyncOpenAI(
    api_key=settings.openai_api_key,
    timeout=httpx.Timeout(
        timeout=float(_timeout),  # Overall timeout per request
        connect=float(_connect_timeout),   # Max time to establish connection
        read=float(_timeout),     # Max time waiting for response data
        write=float(_write_timeout)      # Max time for sending request
    ),
    max_retries=_max_retries  # Automatic retries for transient failures
)

# Set as default client for all Agents SDK calls (web_search, synthesis, 
# entity_merge, graph_merge, connection_mapping)
set_default_openai_client(default_openai_client)


# =============================================================================
# CONVENIENCE ACCESSORS FOR MODEL CONFIGS
# =============================================================================
# These provide backward compatibility and easy access to specific model configs

def get_query_generation_config() -> Dict[str, Any]:
    """Get query generation model configuration."""
    return settings.get_model_config("query_generation")


def get_analysis_config() -> Dict[str, Any]:
    """Get analysis model configuration."""
    return settings.get_model_config("analysis")


def get_web_search_config() -> Dict[str, Any]:
    """Get web search model configuration."""
    return settings.get_model_config("web_search")


def get_synthesis_config() -> Dict[str, Any]:
    """Get synthesis model configuration."""
    return settings.get_model_config("synthesis")


def get_entity_merge_config() -> Dict[str, Any]:
    """Get entity merge model configuration."""
    return settings.get_model_config("entity_merge")


def get_graph_merge_config() -> Dict[str, Any]:
    """Get graph merge model configuration."""
    return settings.get_model_config("graph_merge")


def get_connection_mapping_config() -> Dict[str, Any]:
    """Get connection mapping model configuration."""
    return settings.get_model_config("connection_mapping")