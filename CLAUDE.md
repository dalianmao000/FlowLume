# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build & Test Commands

```bash
# Install dependencies
pip install -e .

# Run all tests
pytest tests/ -v

# Run tests for specific agent
pytest tests/agents/test_data_insight_agent.py -v
pytest tests/agents/test_lean_optimization_agent.py -v

# Initialize mock database
python -c "from src.agents.data_insight.mock_database import init_mock_db; init_mock_db()"

# Run type checking
mypy src/
```

## Architecture

### 5-Agent System
Each Agent (01-05) is a self-contained module in `src/agents/<name>/` with:
- `__init__.py` - Public exports
- `<module>.py` - Core implementation (one file per concern)
- `mock_<data>.py` - Test data generators

Agent-03 and Agent-04 are fully implemented with tests. Agent-05 is designed but not yet built.

### LangGraph Workflow Pattern
Each agent has a corresponding workflow in `src/workflows/<name>_workflow.py`. Workflows define:
- State machine nodes (state transitions)
- Edges between nodes (including conditional branches)
- Human-in-the-loop (HITL) patterns via `human_review` nodes

### Text-to-SQL Security Model (Agent-03)
1. LLM generates SQL from natural language
2. SQLGlot validates syntax
3. Whitelist check: only `SELECT` allowed, no DDL/DML
4. Table/column names validated against schema whitelist
5. Parameterized queries prevent injection

### Key Data Flow
```
User Query → Agent.analyze() → Workflow (LangGraph)
                              ├── parse_query
                              ├── generate_sql (LLM)
                              ├── validate_sql (SQLGlot + whitelist)
                              ├── execute_query
                              ├── interpret_result (LLM)
                              ├── detect_anomaly
                              └── generate_report
```

### Mock Database
SQLite at `data/mock_manufacturing.db` with tables:
- `production_daily` - 180 rows (30 days × 3 lines × 2 plants)
- `equipment_status` - 500 event records
- `quality_inspection` - 100 inspection records

## Project Structure

```
src/
├── agents/           # One folder per agent (01-05)
│   ├── data_insight/ # agent modules + mock data
│   └── lean_optimization/
├── prompts/          # LLM system prompts per agent
├── workflows/        # LangGraph state machine definitions
└── llm/              # Claude API client

tests/
├── agents/           # One test file per agent module
└── workflows/        # Workflow integration tests
```

## Development Workflow

When implementing a new agent or module:
1. Create mock data generator first
2. Implement core module with TDD
3. Add prompt templates in `src/prompts/`
4. Build LangGraph workflow
5. Write integration tests in `tests/workflows/`

## Current Status

| Agent | Status |
|:---|:---|
| Agent-01 Strategic Planning | Implemented |
| Agent-02 Change Enablement | Implemented |
| Agent-03 Data Insight | Fully tested (161 tests) |
| Agent-04 Lean Optimization | Fully tested (141 tests) |
| Agent-05 System Integration | Designed, not built |