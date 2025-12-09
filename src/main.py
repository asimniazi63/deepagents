"""
Main entry point for the Deep Research Agent.

This module provides the main DeepResearchAgent class and CLI interface
for conducting comprehensive due diligence research.
"""

import asyncio
import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

from langfuse.langchain import CallbackHandler

from .config.settings import settings
from .models.state import AgentState
from .agents.graph import research_graph
from .utils.helpers import generate_session_id, format_duration
from .observability.logger import DetailedLogger

class DeepResearchAgent:
    """
    Main agent class for conducting deep research investigations.
    
    This class orchestrates the entire research workflow using LangGraph,
    manages observability through audit logging, and optionally integrates
    with LangFuse for tracing.
    """
    
    def __init__(self):
        """
        Initialize the deep research agent.
        
        Sets up:
        - LangGraph workflow
        - LangFuse tracing (if configured)
        """
        self.graph = research_graph
        self.langfuse_handler = self._initialize_langfuse()
    
    def _initialize_langfuse(self) -> Optional[CallbackHandler]:
        """
        Initialize LangFuse callback handler if credentials are configured.
        
        Returns:
            CallbackHandler if successful, None otherwise
        """
        if not (settings.langfuse_public_key and settings.langfuse_secret_key):
            return None
        
        try:
            # Initialize LangFuse client
            # get_client(
            #     public_key=settings.langfuse_public_key
            # )
            return CallbackHandler()
        except Exception as e:
            print(f"⚠️  Warning: Could not initialize LangFuse: {e}")
            return None
    
    async def research(
        self,
        subject: str,
        context: Optional[str] = None,
        max_depth: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Conduct deep research on a subject.
        
        This is the main entry point for research operations. It:
        1. Initializes the session
        2. Executes the LangGraph workflow
        3. Generates the final report
        4. Logs all operations for audit
        
        Args:
            subject: Name of person or entity to research (required)
            context: Additional context about the subject
            max_depth: Maximum search depth (defaults to config value)
            
        Returns:
            Dictionary containing:
            - session_id: Unique session identifier
            - success: Boolean indicating if research completed successfully
            - report: Final research report (if successful)
            - duration: Human-readable duration string
            - metrics: Research metrics (queries, sources, entities, depth)
            - error: Error message (if failed)
        """
        # Validate input
        if not subject or not subject.strip():
            return {
                "success": False,
                "error": "Subject name is required and cannot be empty"
            }
        
        # Generate session ID
        session_id = generate_session_id()
        
        # Initialize state (minimal - initialize node will set defaults)
        initial_state: AgentState = {
            "session_id": session_id,
            "subject": subject,
            "subject_context": context,
            "max_depth": max_depth or settings.max_search_depth,
        }
        
        # Initialize logger for this session
        logger = DetailedLogger(session_id)
        logger.log("session_start", {
            "subject": subject,
            "max_depth": initial_state["max_depth"],
            "max_queries_per_depth": settings.max_queries_per_depth,
        })
        
        # Log to console
        print(f"\n{'='*80}")
        print(f"🔍 Deep Research AI Agent")
        print(f"{'='*80}")
        print(f"Subject: {subject}")
        print(f"Session ID: {session_id}")
        print(f"Max depth: {initial_state['max_depth']}")
        print(f"{'='*80}\n")
        
        # Execute the graph
        try:
            # Configure graph execution
            config = self._build_execution_config()
            
            # Run the research workflow
            final_state = await self.graph.ainvoke(initial_state, config=config)
            
            # Extract report
            report = final_state.get("final_report")
            
            # Calculate duration
            duration = format_duration(
                (datetime.utcnow() - final_state["start_time"]).total_seconds()
            )
            
            # Log session complete
            logger.log("session_complete", {
                "subject": subject,
                "duration": duration,
                "total_queries": len(final_state.get("queries_executed", [])),
                "risk_level": report.get("risk_level", "UNKNOWN") if report else "UNKNOWN",
                "termination_reason": final_state.get("termination_reason")
            })
            
            # Print summary
            print(f"\n{'='*80}")
            print(f"✅ Research Complete")
            print(f"{'='*80}")
            print(f"Duration: {duration}")
            print(f"Total Queries: {len(final_state.get('queries_executed', []))}")
            print(f"Total Sources: {sum(s.get('sources_found', 0) for s in final_state.get('search_iterations', []))}")
            print(f"Total Entities: {len(final_state.get('discovered_entities', {}))}")
            if report:
                print(f"Risk Level: {report.get('risk_level', 'UNKNOWN')}")
                print(f"Red Flags: {len(report.get('red_flags', []))}")
                print(f"Report saved: {settings.reports_dir}/{session_id}_report.json")
            print(f"{'='*80}\n")
            
            return {
                "session_id": session_id,
                "success": True,
                "report": report,
                "duration": duration,
                "metrics": {
                    "queries": len(final_state.get("queries_executed", [])),
                    "sources": sum(s.get("sources_found", 0) for s in final_state.get("search_iterations", [])),
                    "entities": len(final_state.get("discovered_entities", {})),
                    "depth": final_state.get("current_depth", 0)
                }
            }
                
        except Exception as e:
            error_msg = f"Error during research: {e}"
            print(f"❌ {error_msg}")
            logger.log("session_error", {
                "subject": subject,
                "error_type": type(e).__name__,
                "error_message": str(e)
            })
            return {
                "session_id": session_id,
                "success": False,
                "error": str(e)
            }
    
    def _build_execution_config(self) -> Dict[str, Any]:
        """
        Build configuration for graph execution.
        
        Returns:
            Configuration dictionary for LangGraph
        """
        config = {
            "recursion_limit": 100,  # Allow up to 100 node executions
            "max_concurrency": 10
        }
        
        # Add LangFuse callback if available
        if self.langfuse_handler:
            config["callbacks"] = [self.langfuse_handler]
        
        return config
    
    def _save_report(self, report, session_id: str) -> Path:
        """Save report to file."""
        reports_dir = settings.reports_dir
        reports_dir.mkdir(parents=True, exist_ok=True)
        
        # Save as JSON
        report_file = reports_dir / f"{session_id}_report.json"
        
        with open(report_file, 'w') as f:
            json.dump(report.model_dump(), f, indent=2, default=str)
        
        return report_file


async def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Deep Research AI Agent for Enhanced Due Diligence"
    )
    parser.add_argument(
        "subject",
        help="Name of person or entity to research"
    )
    parser.add_argument(
        "-c", "--context",
        help="Additional context about the subject",
        default=None
    )
    parser.add_argument(
        "-d", "--max-depth",
        help="Maximum search depth",
        type=int,
        default=None
    )
    
    args = parser.parse_args()
    
    # Create agent
    agent = DeepResearchAgent()
    
    # Run research
    result = await agent.research(
        subject=args.subject,
        context=args.context,
        max_depth=args.max_depth
    )
    
    # Return appropriate exit code
    return 0 if result["success"] else 1


if __name__ == "__main__":
    import sys
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

