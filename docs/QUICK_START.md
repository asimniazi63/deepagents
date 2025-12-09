# Quick Start Guide

## Installation

### Prerequisites
- Python 3.11+
- OpenAI API Key
- Anthropic API Key

### Setup

```bash
# Clone and install
git clone <repository-url>
cd deepagents
pip install -r requirements.txt

# Configure API keys
cp .env.example .env
# Edit .env and add your API keys
```

### Required Environment Variables

```bash
OPENAI_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here
```

## Basic Usage

### CLI

```bash
# Basic research
python -m src.main "Sam Bankman-Fried"

# With context
python -m src.main "Elizabeth Holmes" --context "Former CEO of Theranos"

# Custom depth
python -m src.main "Elon Musk" --max-depth 7
```

### Python API

```python
from src.main import DeepResearchAgent
import asyncio

async def run_research():
    agent = DeepResearchAgent()
    
    result = await agent.research(
        subject="Sam Bankman-Fried",
        context="Founder of FTX",
        max_depth=5
    )
    
    if result["success"]:
        print(f"Report: {result['report_path']}")
        print(f"Risk Level: {result['report']['risk_level']}")

asyncio.run(run_research())
```

## Output

Each session generates:

1. **Report**: `reports/sess_{timestamp}_report.json`
   - Executive summary & risk level
   - Biographical, professional, financial analysis
   - Legal & regulatory issues
   - Red flags with severity levels
   - Entity relationship graph
   - Recommendations

2. **Audit Log**: `logs/sess_{timestamp}.jsonl`
   - Complete event trail
   - All LLM calls with tokens/costs
   - Compliance-ready format

3. **Console Output**: Real-time progress

## Configuration

### Workflow Parameters

Edit `.env` or `config/models.yaml`:

```bash
# Workflow control
MAX_SEARCH_DEPTH=5              # Total iterations
MAX_QUERIES_PER_DEPTH=10        # Queries per iteration
MAX_CONCURRENT_SEARCHES=5       # Parallel search limit
STAGNATION_CHECK_ITERATIONS=2   # Stagnation detection
```

### Model Configuration

Edit `config/models.yaml` to change models without touching code:

```yaml
query_generation:
  provider: anthropic
  model: claude-sonnet-4-5-20250929
  temperature: 0.3

web_search:
  provider: openai
  model: GPT-4o

analysis:
  provider: anthropic
  model: claude-sonnet-4-5-20250929
```

## How It Works

### Workflow

```
Initialize
  ↓
[ITERATION LOOP]
  Generate Queries (Claude) → Strategic, targeted queries
  ↓
  Execute Search (OpenAI) → Parallel web searches
  ↓
  Analyze & Reflect (Claude) → Extract insights, assess progress
  ↓
  [Routing Decision]
    • Max depth? → Finalize
    • Reflection says stop? → Finalize
    • Stagnant? → Finalize
    • Otherwise → Continue (loop back)
[END LOOP]
  ↓
Map Connections (OpenAI) → Build entity graph
  ↓
Synthesize Report (OpenAI) → Generate JSON report
```

### Termination Criteria

Research stops when:
- Max depth reached
- Reflection analysis recommends stopping
- Stagnation detected (no new entities for N iterations)

## Understanding Output

### Console Output

```
================================================================================
🔍 Deep Research AI Agent
================================================================================
Subject: Sam Bankman-Fried
Session ID: sess_20251207_120000
Max depth: 5
================================================================================

[... iteration progress ...]

================================================================================
✅ Research Complete
================================================================================
Duration: 8m 30s
Total Queries: 40
Total Sources: 127
Total Entities: 35
Risk Level: CRITICAL
Red Flags: 15
Report saved: reports/sess_20251207_120000_report.json
================================================================================
```

### Report Structure

```json
{
  "executive_summary": "...",
  "risk_level": "CRITICAL",
  "key_findings": ["...", "..."],
  "red_flags": [
    {
      "severity": "CRITICAL",
      "detail": "..."
    }
  ],
  "entity_graph": {
    "nodes": [...],
    "edges": [...]
  },
  "recommendations": [...]
}
```

## Common Use Cases

### Due Diligence Investigation
```bash
python -m src.main "CEO Name" \
  --context "CEO of Company X, considering investment" \
  --max-depth 5
```

### Background Check
```bash
python -m src.main "Person Name" \
  --context "Potential executive hire" \
  --max-depth 3
```

### Risk Assessment
```bash
python -m src.main "Organization" \
  --context "Vendor due diligence" \
  --max-depth 4
```

## Tuning Performance

### Fast Mode (2-3 minutes)
```yaml
workflow:
  max_search_depth: 2
  max_queries_per_depth: 5
```

### Balanced Mode (6-8 minutes)
```yaml
workflow:
  max_search_depth: 5
  max_queries_per_depth: 10
```

### Quality Mode (12-15 minutes)
```yaml
workflow:
  max_search_depth: 7
  max_queries_per_depth: 10
```

## Troubleshooting

### Dependencies Issue
```bash
pip install -r requirements.txt
```

### API Key Not Found
```bash
# Check .env file
cat .env | grep API_KEY
```

### Research Stops Too Early
```bash
# Increase depth or reduce stagnation threshold
MAX_SEARCH_DEPTH=7
STAGNATION_CHECK_ITERATIONS=3
```

### Too Expensive
```bash
# Reduce depth and queries
MAX_SEARCH_DEPTH=3
MAX_QUERIES_PER_DEPTH=5
```

## Next Steps

1. **Run test research** with a well-known person
2. **Review generated reports** in `reports/` directory
3. **Check audit logs** in `logs/` directory
4. **Tune configuration** in `config/models.yaml`
5. **Read architecture** in [SOLUTION_DESIGN.md](SOLUTION_DESIGN.md)

## Tips

- Start with `max_depth=2` for testing
- Use `--context` parameter for better initial queries
- Monitor costs via audit logs
- Review reflection reasoning in logs to understand decisions
- Adjust stagnation threshold based on research goals

---

**For detailed architecture**: See [SOLUTION_DESIGN.md](SOLUTION_DESIGN.md)
