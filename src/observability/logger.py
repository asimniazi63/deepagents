"""
This module provides a structured JSON logging system for tracking
all agent operations, LLM calls, errors, state transitions, and compliance events.
"""

import json
import functools
import inspect
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, Optional

from ..config.settings import settings


class DetailedLogger:
    """
    Comprehensive logger for debugging and monitoring all agent operations.
    
    Logs:
    - Node entry/exit
    - State changes
    - LLM inputs/outputs
    - Errors and exceptions
    - Timing information
    """
    
    def __init__(self, session_id: str):
        """
        Initialize the detailed logger.
        
        Args:
            session_id: Current session ID (used for log file naming)
        """
        self.session_id = session_id
        self.log_dir = Path(settings.log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.log_dir / f"{session_id}.jsonl"
        
    def log(self, event: str, data: Dict[str, Any]) -> None:
        """
        Write a structured log entry.
        
        All log entries include timestamp, session_id, and event type.
        Additional data is merged into the entry.
        
        Args:
            event: Event type/name
            data: Event data dictionary
        """
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "session_id": self.session_id,
            "event": event,
            **data
        }
        
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry, default=str) + '\n')
        except Exception as e:
            # Fallback to console if file writing fails
            print(f"⚠️  Logging error: {e}")
    
    def log_node_entry(self, node_name: str, state: Dict[str, Any]) -> None:
        """
        Log entry into a graph node.
        
        Creates a safe snapshot of state (removing large objects)
        and logs both to file and console.
        
        Args:
            node_name: Name of the node
            state: Current state snapshot
        """
        # Create safe state snapshot (remove large objects)
        safe_state = self._create_safe_state_snapshot(state)
        
        self.log("node_entry", {
            "node": node_name,
            "state_snapshot": safe_state
        })
        
        self._print_node_entry(node_name, state)
    
    def _create_safe_state_snapshot(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a safe state snapshot for logging (excludes large objects).
        
        Args:
            state: Full state dictionary
            
        Returns:
            Sanitized state dictionary with counts instead of lists
        """
        return {
            "subject": state.get("subject"),
            "current_depth": state.get("current_depth"),
            "max_depth": state.get("max_depth"),
            "search_count": state.get("search_count"),
            "extraction_count": state.get("extraction_count"),
            "error_count": state.get("error_count"),
            "entities_count": len(state.get("discovered_entities", {})),
            "pending_queries_count": len(state.get("pending_queries", [])),
            "queries_executed_count": len(state.get("queries_executed", [])),
            "should_continue": state.get("should_continue"),
        }
    
    def _print_node_entry(self, node_name: str, state: Dict[str, Any]) -> None:
        """Print node entry to console."""
        print(f"{'='*80}")
        print(f"NODE: {node_name}")
        print(f"  Depth: {state.get('current_depth')}/{state.get('max_depth')}")
        print(f"  Entities: {len(state.get('discovered_entities', {}))}")
        print(f"  Pending Queries: {len(state.get('pending_queries', []))}")
        print(f"{'='*80}")
    
    def log_node_exit(self, node_name: str, state: Dict[str, Any], duration_ms: float) -> None:
        """
        Log exit from a graph node.
        
        Args:
            node_name: Name of the node
            state: Updated state after node execution
            duration_ms: Node execution time in milliseconds
        """
        # Create safe state snapshot
        safe_state = self._create_safe_state_snapshot(state)
        safe_state["termination_reason"] = state.get("termination_reason")
        
        self.log("node_exit", {
            "node": node_name,
            "state_snapshot": safe_state,
            "duration_ms": duration_ms
        })
        
        print(f"EXIT {node_name}: {duration_ms:.2f}ms\n")
    
    def log_llm_call(
        self,
        operation: str,
        model: str,
        input_data: Any,
        output_data: Any,
        duration_ms: float,
        tokens: Optional[Dict[str, int]] = None,
        cost_usd: Optional[float] = None
    ) -> None:
        """Log an LLM API call.
        
        Args:
            operation: What the LLM was doing (e.g., "query_generation", "entity_extraction")
            model: Model name
            input_data: Input to the LLM (prompt, messages, etc.)
            output_data: Output from the LLM
            duration_ms: Call duration in milliseconds
            tokens: Token usage info
            cost_usd: Estimated cost
        """
        self.log("llm_call", {
            "operation": operation,
            "model": model,
            "input": self._truncate_for_log(input_data, max_chars=2000),
            "output": self._truncate_for_log(output_data, max_chars=5000),
            "duration_ms": duration_ms,
            "tokens": tokens or {},
            "cost_usd": cost_usd or 0.0
        })
        
        print(f"  LLM CALL: {operation}")
        print(f"    Model: {model}")
        print(f"    Duration: {duration_ms:.2f}ms")
        if tokens:
            print(f"    Tokens: {tokens}")
        print(f"    Input (truncated): {self._truncate_for_display(input_data, 200)}")
        print(f"    Output (truncated): {self._truncate_for_display(output_data, 500)}")
    
    def log_search_queries(self, queries: list, context: str) -> None:
        """Log generated search queries.
        
        Args:
            queries: List of search queries
            context: Context for the queries
        """
        self.log("search_queries_generated", {
            "queries": queries,
            "context": context,
            "count": len(queries)
        })
        
        print(f"🔍  SEARCH QUERIES ({len(queries)}):")
        for i, q in enumerate(queries, 1):
            print(f"    {i}. {q} ✏️")
    
    def log_search_results(self, query: str, results_count: int, sources: list) -> None:
        """Log search results.
        
        Args:
            query: Search query
            results_count: Number of results
            sources: List of source URLs
        """
        self.log("search_results", {
            "query": query,
            "results_count": results_count,
            "sources": sources[:10]  # First 10 sources
        })
        
        print(f"✅  SEARCH RESULTS for '{query[:60]}...':")
        print(f"    📝 Found {results_count} results")
        print(f"    🔗 Sources: {sources[:3]}")
    
    def log_entities_extracted(self, entities: list, facts: list) -> None:
        """Log extracted entities and facts.
        
        Args:
            entities: List of entities
            facts: List of facts
        """
        entity_summary = [
            {"name": e.name, "type": e.entity_type, "role": e.role}
            for e in entities[:10]
        ]
        fact_summary = [
            {"claim": f.claim[:100], "confidence": f.confidence}
            for f in facts[:10]
        ]
        
        self.log("entities_extracted", {
            "entities_count": len(entities),
            "facts_count": len(facts),
            "entities_sample": entity_summary,
            "facts_sample": fact_summary
        })
        
        print(f"  ENTITIES EXTRACTED: {len(entities)}")
        for e in entities[:5]:
            print(f"    - {e.name} ({e.entity_type})")
        print(f"  FACTS EXTRACTED: {len(facts)}")
        for f in facts[:3]:
            print(f"    - {f.claim[:80]}...")
    
    def log_risk_assessment(self, risk_assessment: Any) -> None:
        """Log risk assessment results.
        
        Args:
            risk_assessment: Risk assessment object
        """
        if risk_assessment:
            self.log("risk_assessment", {
                "overall_level": risk_assessment.overall_level,
                "overall_score": risk_assessment.overall_score,
                "red_flags_count": len(risk_assessment.red_flags),
                "red_flags": [
                    {
                        "category": rf.category,
                        "severity": rf.severity,
                        "title": rf.title
                    }
                    for rf in risk_assessment.red_flags[:10]
                ]
            })
            
            print(f"  RISK ASSESSMENT:")
            print(f"    Level: {risk_assessment.overall_level}")
            print(f"    Score: {risk_assessment.overall_score}")
            print(f"    Red Flags: {len(risk_assessment.red_flags)}")
    
    def log_info(self, message: str, data: Optional[Dict[str, Any]] = None) -> None:
        """Log an informational message.
        
        Args:
            message: Info message
            data: Optional additional data
        """
        # Get caller information
        frame = inspect.currentframe()
        caller_frame = frame.f_back
        filename = caller_frame.f_code.co_filename
        line_number = caller_frame.f_lineno
        
        log_data = {
            "message": message,
            "file": filename,
            "line": line_number
        }
        if data:
            log_data.update(data)
        
        self.log("info", log_data)
        print(f"  INFO [{filename.split('/')[-1]}:{line_number}]: {message}")
    
    def log_warning(self, message: str, data: Optional[Dict[str, Any]] = None) -> None:
        """Log a warning message.
        
        Args:
            message: Warning message
            data: Optional additional data
        """
        # Get caller information
        frame = inspect.currentframe()
        caller_frame = frame.f_back
        filename = caller_frame.f_code.co_filename
        line_number = caller_frame.f_lineno
        
        log_data = {
            "message": message,
            "file": filename,
            "line": line_number
        }
        if data:
            log_data.update(data)
        
        self.log("warning", log_data)
        print(f"  ⚠️  WARNING [{filename.split('/')[-1]}:{line_number}]: {message}")
    
    def log_error(self, operation: str, error: Exception, context: Dict[str, Any]) -> None:
        """Log an error.
        
        Args:
            operation: What was being done when the error occurred
            error: The exception
            context: Additional context
        """
        # Get caller information
        frame = inspect.currentframe()
        caller_frame = frame.f_back
        filename = caller_frame.f_code.co_filename
        line_number = caller_frame.f_lineno
        
        self.log("error", {
            "operation": operation,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context,
            "file": filename,
            "line": line_number
        })
        
        print(f"  ❌ ERROR [{filename.split('/')[-1]}:{line_number}] in {operation}: {type(error).__name__}: {error}")
    
    def log_report_generated(self, report: Any) -> None:
        """Log report generation.
        
        Args:
            report: Generated research report
        """
        if report:
            self.log("report_generated", {
                "subject": report.subject.name if hasattr(report, 'subject') else "unknown",
                "risk_level": report.risk_assessment.overall_level if hasattr(report, 'risk_assessment') else "unknown",
                "confidence": report.overall_confidence if hasattr(report, 'overall_confidence') else 0,
                "searches": report.search_queries_count if hasattr(report, 'search_queries_count') else 0,
                "sources": report.total_sources_consulted if hasattr(report, 'total_sources_consulted') else 0,
                "processing_time": report.processing_time_seconds if hasattr(report, 'processing_time_seconds') else 0
            })
            
            print(f"  REPORT GENERATED:")
            print(f"    Subject: {report.subject.name if hasattr(report, 'subject') else 'unknown'}")
            print(f"    Risk: {report.risk_assessment.overall_level if hasattr(report, 'risk_assessment') else 'unknown'}")
        else:
            self.log("report_generation_failed", {})
            print(f"  REPORT GENERATION FAILED")
    
    def _truncate_for_log(self, data: Any, max_chars: int = 1000) -> Any:
        """Truncate data for logging.
        
        Args:
            data: Data to truncate
            max_chars: Maximum characters
            
        Returns:
            Truncated data
        """
        if isinstance(data, str):
            return data[:max_chars] + "..." if len(data) > max_chars else data
        elif isinstance(data, dict):
            return {k: self._truncate_for_log(v, max_chars // 2) for k, v in list(data.items())[:10]}
        elif isinstance(data, list):
            return [self._truncate_for_log(item, max_chars // 4) for item in data[:10]]
        else:
            s = str(data)
            return s[:max_chars] + "..." if len(s) > max_chars else s
    
    def _truncate_for_display(self, data: Any, max_chars: int = 200) -> str:
        """Truncate data for console display.
        
        Args:
            data: Data to truncate
            max_chars: Maximum characters
            
        Returns:
            Truncated string
        """
        s = str(data)
        return s[:max_chars] + "..." if len(s) > max_chars else s


def log_node_execution(func: Callable) -> Callable:
    """Decorator to log node execution.
    
    Args:
        func: Node function to wrap
        
    Returns:
        Wrapped function
    """
    @functools.wraps(func)
    async def wrapper(state: Dict[str, Any]) -> Dict[str, Any]:
        session_id = state.get("session_id", "unknown")
        logger = DetailedLogger(session_id)
        node_name = func.__name__
        
        # Log entry
        start_time = datetime.utcnow()
        logger.log_node_entry(node_name, state)
        
        try:
            # Execute node
            result = await func(state)
            
            # Log exit
            duration = (datetime.utcnow() - start_time).total_seconds() * 1000
            logger.log_node_exit(node_name, result, duration)
            
            return result
            
        except Exception as e:
            # Log error
            duration = (datetime.utcnow() - start_time).total_seconds() * 1000
            logger.log_error(node_name, e, {"state_keys": list(state.keys())})
            logger.log_node_exit(node_name, state, duration)
            raise
    
    return wrapper

