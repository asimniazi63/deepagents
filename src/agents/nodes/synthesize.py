"""Synthesis node for LangGraph workflow using OpenAI."""

import json
from datetime import datetime

from agents import Agent, ModelSettings, Runner, RunConfig

from ...models.state import AgentState
from ...models.search_result import DueDiligenceReport
from ...config.settings import settings
from ...observability.logger import log_node_execution, DetailedLogger
from ...prompts.synthesis import build_synthesis_prompt, SYNTHESIS_INSTRUCTIONS


@log_node_execution
async def synthesize_report(state: AgentState) -> AgentState:
    """
    Synthesize comprehensive final report using OpenAI.
    
    Creates a detailed due diligence report with:
    - Executive summary and risk assessment
    - Detailed findings by category
    - Entity relationship analysis
    - Source and evidence evaluation
    - Recommendations
    
    Args:
        state: Current agent state
        
    Returns:
        Updated agent state with final_report
    """
    session_id = state.get("session_id", "unknown")
    logger = DetailedLogger(session_id)
    logger.log_info("Starting report synthesis")
    
    try:
        # Build synthesis prompt
        prompt = build_synthesis_prompt(state)
        
        # Get synthesis config from YAML
        synthesis_config = settings.get_model_config("synthesis")
        
        # Use OpenAI Agents SDK for report generation
        agent = Agent(
            name="ReportSynthesizer",
            model=synthesis_config.get("model"),
            instructions=SYNTHESIS_INSTRUCTIONS,
            output_type=DueDiligenceReport,
            model_settings=ModelSettings(verbosity=synthesis_config.get("verbosity", "medium")),
        )
        
        logger.log_info("Executing OpenAI report synthesis")
        result = await Runner.run(agent, prompt, run_config=RunConfig(tracing_disabled=True))
        
        report: DueDiligenceReport = result.final_output
        
        # Convert to dict and add metadata
        final_report = report.model_dump()
        
        # Add metadata
        start_time = state.get("start_time", datetime.utcnow())
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        final_report["metadata"] = {
            "subject": state["subject"],
            "session_id": state["session_id"],
            "research_depth": state["current_depth"],
            "total_queries": len(state.get("queries_executed", [])),
            "total_sources": sum(s.get("sources_found", 0) for s in state.get("search_iterations", [])),
            "confidence_score": state.get("confidence_score", 0.0),
            "processing_time_seconds": processing_time,
            "termination_reason": state.get("termination_reason"),
            "generated_at": datetime.utcnow().isoformat(),
            "models_used": {
                "search": settings.get_model_config("web_search").get("model"),
                "analysis": settings.get_model_config("analysis").get("model"),
                "synthesis": settings.get_model_config("synthesis").get("model")
            }
        }
        
        # Add entity graph
        final_report["entity_graph"] = state.get("entity_graph", {})
        
        # Store in state
        state["final_report"] = final_report
        
        logger.log_info("Report synthesis complete", {
            "risk_level": report.risk_level,
            "key_findings_count": len(report.key_findings),
            "red_flags_count": len(report.red_flags)
        })
        
        # Save report to file
        report_path = settings.reports_dir / f"{state['session_id']}_report.json"
        settings.reports_dir.mkdir(exist_ok=True)
        
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(final_report, f, indent=2, ensure_ascii=False)
        
        logger.log_info(f"Report saved to {report_path}")
        
        # Mark as complete
        state["should_continue"] = False
        if not state.get("termination_reason"):
            state["termination_reason"] = "report_synthesized"
        
    except Exception as e:
        logger.log_error("synthesize_report", e, {"state_keys": list(state.keys())})
        state["error_count"] = state.get("error_count", 0) + 1
        state["should_continue"] = False
        state["termination_reason"] = f"report_generation_error: {str(e)}"
        raise
    
    return state

