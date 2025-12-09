"""
Prompts for final report synthesis using OpenAI.

This module provides prompt builders for synthesizing comprehensive
due diligence reports from all collected research findings.

Used by:
- `agents/nodes/synthesize.py` → `synthesize_report`
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..models.state import AgentState


# ============================================================================
# Synthesis Instructions
# ============================================================================

SYNTHESIS_INSTRUCTIONS = """You are a senior intelligence analyst preparing Enhanced Due Diligence reports for executive decision-making and risk committees.

<report_context>
Your reports inform critical decisions:
- Investment/divestment (millions or billions at stake)
- Board appointments and executive hires
- Business partnerships and M&A transactions
- Litigation strategy and settlement negotiations
- Regulatory compliance and reporting obligations
- Reputational risk management
</report_context>

<report_quality_standards>
Your reports must be:
- **ACTIONABLE**: Clear risk rating, specific recommendations, decision support
- **EVIDENCE-BASED**: Every claim substantiated with sources, facts over speculation
- **COMPREHENSIVE**: All material risks identified, no critical gaps
- **PROFESSIONAL**: Formal tone, structured format, executive-ready
- **OBJECTIVE**: Impartial analysis, balanced view, acknowledge limitations
- **PRECISE**: Specific facts (dates, amounts, names), not vague generalities
- **RISK-FOCUSED**: Prioritize red flags and material concerns
- **DEFENSIBLE**: Can withstand scrutiny, litigation-ready
</report_quality_standards>

<analytical_framework>
Apply layered risk analysis:
1. **Strategic Risk**: Could impact major decisions or organizational objectives
2. **Financial Risk**: Direct financial loss, asset impairment, liability exposure
3. **Legal/Regulatory Risk**: Violations, sanctions, enforcement, litigation
4. **Reputational Risk**: Public scandals, media exposure, stakeholder concerns
5. **Operational Risk**: Business disruption, key person dependencies
6. **Integrity Risk**: Fraud, corruption, unethical conduct
</analytical_framework>

<synthesis_objectives>
Transform raw intelligence into actionable insight:
- Separate signal from noise (what matters vs. what doesn't)
- Connect dots (patterns across disparate findings)
- Assess materiality (which risks have real impact)
- Provide context (industry norms, benchmarks, precedents)
- Quantify where possible (probabilities, amounts, timelines)
- Recommend actions (mitigations, further investigation, decision points)
</synthesis_objectives>"""


# ============================================================================
# Prompt Builder Functions
# ============================================================================

def build_synthesis_prompt(state: "AgentState") -> str:
    """
    Build comprehensive prompt for report synthesis.
    
    This prompt includes:
    - Subject information and context
    - Research metrics and statistics
    - All reflection analysis summaries
    - Entity graph and relationships
    - Risk indicators summary
    - Source quality assessment
    - Task instructions
    
    Args:
        state: Current agent state with all research findings
        
    Returns:
        Formatted prompt string for report synthesis
    """
    # Gather all data
    reflection_memory = state.get("reflection_memory", [])
    entity_graph = state.get("entity_graph", {})
    risk_indicators = state.get("risk_indicators", {})
    search_iterations = state.get("search_iterations", [])
    
    prompt = f"""# Due Diligence Report Synthesis

## Subject Information
Subject: {state['subject']}
Context: {state.get('subject_context', 'N/A')}
Session ID: {state['session_id']}

## Research Metrics
Search Depth: {state['current_depth']} iterations
Total Queries: {len(state.get('queries_executed', []))}
Total Sources: {sum(s.get('sources_found', 0) for s in search_iterations)}
Confidence Score: {state.get('confidence_score', 0.0):.2f}
Termination Reason: {state.get('termination_reason', 'N/A')}

"""
    
    # Add reflection summaries
    prompt += "\n## Research Findings (All Iterations)\n\n"
    for i, reflection in enumerate(reflection_memory):
        prompt += f"### Iteration {i}\n"
        prompt += f"**Analysis Summary:**\n{reflection.get('analysis_summary', 'No analysis available')}\n\n"
        prompt += f"**Decision:** {'Continue' if reflection.get('should_continue') else 'Stop'}\n"
        prompt += f"**Reasoning:** {reflection.get('reasoning', 'N/A')}\n\n"
    
    # Add entity graph summary
    if entity_graph.get("nodes"):
        prompt += f"\n## Entity Graph\n"
        prompt += f"Total Entities: {len(entity_graph.get('nodes', []))}\n"
        prompt += f"Total Relationships: {len(entity_graph.get('edges', []))}\n\n"
        
        prompt += "**Key Entities:**\n"
        for node in entity_graph.get("nodes", [])[:10]:
            prompt += f"- {node.get('name', 'Unknown')} ({node.get('type', 'unknown')})\n"
        
        prompt += "\n**Key Relationships:**\n"
        for edge in entity_graph.get("edges", [])[:15]:
            source = edge.get("source", "?")
            target = edge.get("target", "?")
            rel = edge.get("relationship", "?")
            prompt += f"- {source} → {rel} → {target}\n"
    
    # Add risk indicators summary
    prompt += "\n## Risk Indicators Summary\n"
    prompt += f"Red Flags: {len(risk_indicators.get('red_flags', []))}\n"
    prompt += f"Neutral Facts: {len(risk_indicators.get('neutral', []))}\n"
    prompt += f"Positive Indicators: {len(risk_indicators.get('positive', []))}\n"
    
    # Add source quality info
    total_sources = sum(s.get("sources_found", 0) for s in search_iterations)
    prompt += f"\n## Source Quality\n"
    prompt += f"Total Sources Referenced: {total_sources}\n"
    
    # Task instructions
    prompt += """

## Your Task: Synthesize Executive-Grade Due Diligence Report

Create a comprehensive, defensible intelligence report using the following structure:

### 1. EXECUTIVE SUMMARY
**Format**: 3-5 sentences capturing essence
**Content**:
- Who is the subject (full name with identifying context: title, organization, location)
- Overall risk assessment (one sentence)
- Top 1-3 most critical concerns (if any)
- Bottom-line implication for decision-making

**Example**: "Sam Bankman-Fried, former CEO of FTX cryptocurrency exchange (2019-2022, Bahamas), is currently facing federal criminal charges for fraud and money laundering. Investigation uncovered systematic misappropriation of $8+ billion in customer funds. Evidence indicates deliberate fraud involving senior executives and falsified financial records. RISK LEVEL: CRITICAL - Subject poses severe legal, financial, and reputational risk."

**Note**: For common names, add clarifying details to avoid confusion (e.g., "John Smith, CFO of Acme Corp, Boston")

### 2. RISK LEVEL ASSESSMENT
**Rating**: CRITICAL / HIGH / MEDIUM / LOW
**Justification**: 2-3 sentences explaining rating
**Key Risk Factors**: Bulleted list of primary risks driving assessment

**Risk Level Criteria**:
- CRITICAL: Active criminal charges, proven fraud, bankruptcy, sanctions
- HIGH: Serious allegations, major litigation, regulatory violations
- MEDIUM: Minor legal issues, reputational concerns, business failures
- LOW: Clean record, positive reputation, normal business conduct

### 3. KEY FINDINGS (Top 5-10)
**Priority**: Red flags first, then material neutral/positive facts
**Format**: For each finding:
- [SEVERITY if red flag] Specific finding statement
- Evidence: Primary sources (2-3)
- Impact: Why this matters
- Status: Alleged/Proven/Ongoing/Resolved

### 4. BIOGRAPHICAL OVERVIEW
**Focus**: Identity, background, formative experiences
**Include**:
- Full name, aliases, date of birth, nationality (include company/title to confirm correct person)
- Education (institutions, degrees, years)
- Family background (if relevant to wealth/power)
- Early career and formative experiences
- Geographic history (relevant residences)

**Note**: If researching a common name, verify identity by cross-referencing multiple identifiers (company, title, location, dates)

### 5. PROFESSIONAL HISTORY
**Format**: Timeline or chronological narrative
**Include**:
- Current positions (titles, organizations, since when)
- Career progression (key roles, employers, dates)
- Business ventures (founded, invested, board seats)
- Professional achievements and failures
- Transitions and career gaps (with explanations)

### 6. FINANCIAL ANALYSIS
**Focus**: Wealth, financial interests, transactions
**Include**:
- Net worth estimates (sources, dates, methodology)
- Income sources (employment, investments, businesses)
- Major assets (real estate, companies, holdings)
- Significant transactions (acquisitions, sales, investments)
- Business ownership and partnerships
- Debt, liabilities, financial distress (if any)

### 7. LEGAL & REGULATORY EXPOSURE
**Priority**: Active issues first, then historical
**Include**:
- Criminal matters (charges, convictions, investigations)
- Civil litigation (plaintiff/defendant, amounts, status)
- Regulatory actions (violations, fines, consent orders)
- Bankruptcy filings, tax liens, judgments
- Ongoing investigations or compliance issues
- Legal outcomes and resolutions

**Critical**: Distinguish allegations from proven facts

### 8. BEHAVIORAL PATTERNS & REPUTATION
**Focus**: Character, ethics, conduct, reputation
**Include**:
- Decision-making patterns (risk appetite, governance)
- Ethical conduct and integrity indicators
- Associations and social circles
- Public statements and media presence
- Employee/partner feedback
- Reputation in industry and community
- Crisis response and accountability

### 9. RED FLAGS (Detailed)
**Format**: Severity-tiered list
**For each red flag**:
- [CRITICAL/HIGH/MEDIUM] Specific description
- Evidence: Primary sources with citations
- Corroboration: How many independent sources?
- Implications: Impact on risk assessment
- Counterpoints: Any mitigating information?

**Example**:
[CRITICAL] Misappropriation of $8 billion in customer funds
- Evidence: SEC complaint, DOJ indictment, bankruptcy filings
- Corroboration: Confirmed by 5+ sources (regulators, courts, testimony)
- Implications: Federal criminal charges, total loss for customers, life sentence exposure
- Counterpoints: None - admitted by defendant's own executives

### 10. NEUTRAL FACTS
**Purpose**: Context without risk implications
**Include**: Education, career moves, business activities, family info
**Exclude**: Irrelevant personal details, subjective opinions

### 11. POSITIVE INDICATORS
**Purpose**: Balanced view, mitigating factors
**Include**:
- Legitimate achievements and credentials
- Positive contributions (philanthropy, innovation)
- Strong governance or compliance programs
- Favorable industry reputation (pre-incident)

**Critical**: Distinguish genuine positives from reputation laundering

### 12. KEY RELATIONSHIPS (Entity Network)
**Format**: Prioritized list of connections
**Include**:
- Professional relationships (co-founders, business partners, board members)
- Financial connections (investors, co-investors, lenders)
- Personal relationships (if relevant to risk)
- Political connections and lobbying
- For each: Nature, duration, context, risk relevance

**Note**: Always include title/organization when naming people to avoid confusion (e.g., "John Smith, CFO of Acme Corp" not just "John Smith")

### 13. SUSPICIOUS CONNECTIONS & PATTERNS
**Focus**: Red flags in network and behavior
**Include**:
- Conflicts of interest (dual roles, related-party transactions)
- Hidden or undisclosed relationships
- Associations with high-risk entities/individuals
- Pattern of concerning behaviors (repeated fraud, serial bankruptcies)
- Timeline anomalies (coordinated actions, suspicious timing)
- Network overlaps suggesting collusion

### 14. SOURCE ASSESSMENT
**Purpose**: Evidence quality and confidence levels
**Include**:
- Source distribution (% Tier 1/2/3/4)
- Key primary sources (most valuable)
- Corroboration rate (multi-source facts vs. single-source)
- Source limitations (paywalls, sealed docs, missing records)
- Overall confidence in findings (High/Medium/Low)

### 15. EVIDENCE STRENGTH EVALUATION
**For each major finding**:
- **Documentary Evidence**: Court filings, official records, verified documents (Strongest)
- **Testimony/Admissions**: Sworn testimony, admissions by parties
- **Multiple Media Reports**: Independent confirmation by credible outlets
- **Single Source**: Uncorroborated claims (Weakest)

**Overall Assessment**: How strong is the evidence base?

### 16. INFORMATION GAPS
**Priority**: Gaps affecting decision-making
**Format**:
- Critical Gaps (HIGH impact): Information essential for risk assessment
- Important Gaps (MEDIUM impact): Would enhance understanding
- Minor Gaps (LOW impact): Nice to have but not material

**For each**: Why it matters, feasibility of obtaining, workarounds

### 17. RESEARCH LIMITATIONS
**Transparency**: Constraints on investigation
**Include**:
- Time/resource limitations
- Access restrictions (sealed records, paywalls, foreign jurisdictions)
- Data unavailability (private companies, offshore entities)
- Temporal constraints (events too recent for full documentation)

**Impact**: How limitations affect conclusions

### 18. RECOMMENDATIONS
**Format**: Tiered, actionable recommendations
**Include**:

**A. IMMEDIATE ACTIONS**:
- Decision: Proceed/Don't Proceed/Proceed with Cautions
- Risk Mitigations: Specific controls or safeguards if proceeding
- Escalations: Issues requiring senior review or board notification

**B. FURTHER INVESTIGATION** (if applicable):
- Priority leads requiring follow-up
- Specific questions to resolve
- Additional sources to consult
- Estimated effort and value

**C. MONITORING** (if proceeding):
- Ongoing risks to track
- Red flags that would trigger reassessment
- Compliance or oversight measures

**D. DECISION FRAMEWORK**:
- Risk tolerance considerations
- Trade-offs and alternatives
- Timeline for decision-making

## WRITING STANDARDS

**Tone**: Formal, professional, objective (no editorializing)
**Style**: Clear, concise, precise (no jargon or fluff)
**Structure**: Well-organized with clear headers (executive-readable)
**Evidence**: Every material claim cited to source
**Precision**: Specific facts (dates, amounts, names), not vague statements
**Balance**: Fair assessment (acknowledge strengths and weaknesses)
**Defensibility**: Can withstand legal/audit scrutiny

**Language**:
✓ "SEC complaint alleges misappropriation of $8 billion" (specific, sourced)
✗ "There were some financial problems" (vague, unsourced)

✓ "[CRITICAL] Federal criminal fraud charges filed November 2022" (precise)
✗ "Subject has legal issues" (imprecise)

Generate the complete report in JSON format matching the DueDiligenceReport schema.
"""
    
    return prompt

