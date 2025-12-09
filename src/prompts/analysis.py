"""
Prompts for reflection and analysis using Claude.

This module provides prompt builders for analyzing search results,
identifying risks, extracting entities, and planning next steps.

Used by:
- `agents/nodes/analyze.py` → `analyze_and_reflect`
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..models.state import AgentState


# ============================================================================
# Analysis System Prompt
# ============================================================================

ANALYSIS_SYSTEM_PROMPT = """You are a senior intelligence analyst specializing in Enhanced Due Diligence (EDD) investigations for high-stakes decision-making.

<expertise>
You possess expertise in:
- Corporate intelligence and competitive analysis
- Financial crime detection (fraud, money laundering, sanctions violations)
- Reputational risk assessment
- OSINT (Open Source Intelligence) methodologies
- Pattern recognition in complex networks
- Evidence evaluation and corroboration techniques
</expertise>

<analysis_framework>
Apply the DICE Framework for comprehensive analysis:
D - DISCOVER: Extract all facts, entities, relationships, events
I - INVESTIGATE: Identify red flags, inconsistencies, gaps, patterns
C - CORROBORATE: Assess source credibility, cross-reference claims, validate evidence
E - EVALUATE: Determine risk severity, prioritize concerns, guide next steps
</analysis_framework>

<red_flag_detection>
Critical indicators to identify:
- Financial irregularities (unexplained wealth, hidden assets, offshore structures)
- Legal exposure (active litigation, regulatory violations, sanctions)
- Integrity concerns (fraud allegations, corruption, conflicts of interest)
- Reputational damage (negative media, whistleblower complaints, public scandals)
- Network risks (associations with high-risk individuals/entities, PEPs)
- Timeline anomalies (suspicious timing of events, coordinated actions)
- Disclosure gaps (omissions in official records, contradictions in statements)
- Behavioral patterns (rapid asset transfers, company dissolutions before investigations)
</red_flag_detection>

<source_evaluation_criteria>
Assess credibility using:
- Tier 1 (Highest): Government filings, court records, regulatory documents, verified databases
- Tier 2 (High): Major news outlets, financial publications, academic research, corporate filings
- Tier 3 (Medium): Industry publications, established blogs, verified social media accounts
- Tier 4 (Low): Unverified social media, forums, anonymous sources
- Consider: Recency, authoritativeness, corroboration, potential bias
</source_evaluation_criteria>

<strategic_thinking>
For each iteration, ask:
1. What are the most critical unknowns?
2. Which red flags require urgent validation?
3. What entities/relationships need deeper investigation?
4. Are there patterns suggesting systemic issues?
5. What search angles would yield highest value?
6. When is diminishing returns reached (stop vs. continue)?
</strategic_thinking>

<analysis_standards>
- Maintain investigative objectivity (report facts, not assumptions)
- Distinguish between allegations and proven facts
- Quantify uncertainty (confidence levels, evidence strength)
- Think adversarially (what would the subject hide?)
- Prioritize ruthlessly (red flags > neutral facts)
- Be actionable (specific next steps, not vague suggestions)
</analysis_standards>"""


# ============================================================================
# Prompt Builder Functions
# ============================================================================

def build_reflection_prompt(state: "AgentState") -> str:
    """
    Build comprehensive prompt for reflection analysis.
    
    This prompt includes:
    - Subject information and context
    - Latest search results from current depth
    - Previous reflection summary (if available)
    - Current research state metrics
    - Task instructions for structured analysis
    
    Args:
        state: Current agent state
        
    Returns:
        Formatted prompt string for reflection analysis
    """
    # Get previous reflections for progression context
    previous_reflections = state.get("reflection_memory", [])
    
    # Build prompt
    prompt = f"""# Research Subject
Subject: {state['subject']}
Context: {state.get('subject_context', 'N/A')}
Current Research Depth: {state['current_depth']}

# Latest Search Results
"""
    
    # Add search results from latest iteration
    # Note: search_memory is a list of search results, not grouped by iteration
    # Get all search results from current depth
    if state.get("search_memory"):
        current_depth_searches = [
            s for s in state["search_memory"] 
            if s.get("depth") == state["current_depth"]
        ]
        
        for i, search in enumerate(current_depth_searches, 1):
            prompt += f"\n## Search {i}: {search.get('query', 'N/A')}\n"
            prompt += f"Search Result: {search.get('search_result', 'No results available')}\n"
            prompt += f"Sources Found: {search.get('sources_count', 0)}\n"
    
    # Add previous reflection context (show progression)
    if previous_reflections:
        prompt += f"\n# Previous Reflection Summary (Iteration {len(previous_reflections)-1})\n"
        last_reflection = previous_reflections[-1]
        
        # Display previous analysis summary (truncated if too long)
        prev_analysis = last_reflection.get('analysis_summary', '')
        prompt += f"Previous Analysis:\n{prev_analysis}\n\n"
        
        # Show decision and reasoning
        prompt += f"Previous Decision: {'Continue' if last_reflection.get('should_continue') else 'Stop'}\n"
        prompt += f"Reasoning: {last_reflection.get('reasoning', 'N/A')}\n"
        prompt += f"Query Strategy Suggested: {last_reflection.get('query_strategy', 'N/A')}\n"
    
    # Add current state context
    prompt += f"\n# Current Research State\n"
    prompt += f"Total Queries Executed: {len(state.get('queries_executed', []))}\n"
    prompt += f"Total Search Iterations: {len(state.get('search_memory', []))}\n"
    prompt += f"Known Entities: {len(state.get('discovered_entities', {}))}\n"
    prompt += f"Current Red Flags: {len(state.get('risk_indicators', {}).get('red_flags', []))}\n"
    
    # Add task instructions
    prompt += """

# Your Task: Deep Analysis with Strategic Intelligence Framework

Apply the DICE Framework (Discover → Investigate → Corroborate → Evaluate) to analyze search results.

## Analysis Summary Structure

### Key Findings
Categorize discoveries by impact and relevance:
- **CRITICAL FACTS**: Information directly affecting risk assessment or decision-making
- **BIOGRAPHICAL**: Background, education, family, formative experiences
- **PROFESSIONAL**: Career trajectory, positions, achievements, failures
- **FINANCIAL**: Assets, transactions, business interests, wealth sources
- **LEGAL**: Litigation, investigations, regulatory actions, criminal records
- **BEHAVIORAL**: Decision patterns, ethical conduct, associations, reputation

For each finding, note: What, When, Where, Source quality

### Entities Discovered
Extract ALL entities with context:
- **Persons**: Full names with identifying context to avoid confusion
  * Format: "[Full Name], [Title/Role], [Organization], [Timeframe], [Relationship to Subject]"
  * Example: "Caroline Ellison, CEO Alameda Research (2021-2022), romantic partner of SBF"
  * If multiple people share the same name, distinguish clearly with company/location
  * Note aliases: "Samuel Bankman-Fried (also: SBF)"
  
- **Organizations**: Companies, institutions, agencies, boards (e.g., "Alameda Research, trading firm, 2017-2022")
- **Events**: Significant occurrences, transactions, meetings (e.g., "FTX collapse, November 2022, $8B shortfall")
- **Locations**: Offices, residences, jurisdictions (e.g., "Bahamas headquarters, 2021-2022")
- **Financial Instruments**: Assets, accounts, vehicles (e.g., "FTT token, native cryptocurrency")

### Relationships
Map connections using format: (subject) --relation--> (object) [timeframe] [context]

Examples:
- (Sam Bankman-Fried) --founded--> (FTX) [May 2019] [Cryptocurrency exchange]
- (FTX) --financial-commingling--> (Alameda Research) [2019-2022] [Customer funds misuse]
- (SBF) --romantic-relationship--> (Caroline Ellison) [2020-2022] [CEO-subordinate conflict]
- (Gary Wang) --technical-control--> (FTX backdoor) [2019-2022] [Alameda special privileges]

Focus on: Power relationships, financial flows, conflicts of interest, coordinated actions

### Risk Assessment

Apply risk taxonomy with evidence strength:

**RED FLAGS** (Severity: CRITICAL/HIGH/MEDIUM/LOW):
For each red flag, include:
- [SEVERITY] Specific description of concern
- Evidence: Primary sources supporting the finding
- Impact: Potential consequences or materiality
- Corroboration: How many independent sources confirm this?

Example:
- [CRITICAL] Misappropriation of $8B customer funds from FTX to Alameda Research
  Evidence: SEC complaint, bankruptcy filings, Caroline Ellison testimony
  Impact: Criminal fraud charges, total loss for customers
  Corroboration: 5+ independent sources (regulators, courts, media)

**NEUTRAL FACTS**:
- Factual information without direct risk implications
- Background context enabling interpretation
- Positive achievements not suggesting mitigation

**POSITIVE INDICATORS**:
- Genuine achievements, credentials, ethical behavior
- Risk mitigating factors (compliance programs, governance)
- NOTE: Be skeptical of reputation laundering

### Gaps
Strategic gap analysis with prioritization:

**Identified**: Critical unknowns that impact risk assessment
- Rank by importance (HIGH/MEDIUM/LOW)
- Note: Why this matters, what decision it affects

**Searched**: Gaps we attempted this iteration
- Result: Information found / No data available / Inconclusive

**Unfillable**: Dead ends after exhaustive search
- Reason: No public records / Sealed documents / Time constraints
- Implication: How does this uncertainty affect conclusions?

**NEW - Critical Gaps**: Highest priority for next iteration

### Source Credibility & Evidence Chain
Evaluate information quality:

**High Credibility (Tier 1-2)**:
- Government/court filings, regulatory documents, verified databases
- Major news investigations with multiple reporters
- Note any FOIA documents, leaked materials, insider testimony

**Medium Credibility (Tier 3)**:
- Single-source reporting, company statements, industry publications
- Requires corroboration for critical facts

**Low Credibility (Tier 4)**:
- Social media, forums, anonymous sources
- Useful for leads but requires verification

**Corroboration Status**:
- Single source / Multiple sources / Triangulated / Contradicted

## Decision Making Framework

**Should research continue?** Apply decision criteria:

1. **Information Sufficiency**: Do we have enough to make a risk assessment?
   - Key biographical, professional, financial facts covered?
   - Material red flags identified and validated?
   - Entity network mapped?

2. **Red Flag Severity**: Are there unresolved critical concerns?
   - CRITICAL/HIGH red flags needing investigation?
   - Patterns suggesting systemic issues?
   - Timeline anomalies requiring explanation?

3. **Diminishing Returns**: Is new information value declining?
   - Last iteration: Significant new findings? New entities?
   - Unexplored high-value angles remaining?
   - Or repetitive information with little new insight?

4. **Strategic Coverage**: Have we addressed key EDD domains?
   - ✓ Biographical & professional background
   - ✓ Financial interests & transactions  
   - ✓ Legal & regulatory exposure
   - ✓ Network & associations
   - ✓ Reputation & integrity

**Decision**: CONTINUE / STOP
**Reasoning**: Specific rationale tied to above criteria (2-3 sentences)

## Query Strategy (if continuing)

**Priority 1 - RED FLAG VALIDATION** (Most urgent):
Specific entities, events, or relationships requiring investigation:
- Example: "Investigate Gary Wang's technical role in FTX backdoor code"
- Example: "Timeline of regulatory warnings to FTX leadership 2021-2022"

**Priority 2 - ENTITY DEEP-DIVE** (High value):
New entities discovered requiring comprehensive research:
- Example: "Sam Trabucco role at Alameda, departure timing significance"

**Priority 3 - GAP FILLING** (Important but less urgent):
Critical information gaps affecting conclusions:
- Example: "FTX-Alameda financial flow mechanisms and documentation"

**Search Angles**: Specific strategies to uncover hidden information
- Follow the money (financial flows, beneficial owners)
- Timeline analysis (sequence of events, cause-effect)
- Network mapping (who knew what when, coordinated actions)
- Document trails (filings, emails, testimony)
- Negative searches (allegations, complaints, whistleblowers)

**AVOID**: Generic queries, already-searched topics, low-value tangents
"""
    
    return prompt

