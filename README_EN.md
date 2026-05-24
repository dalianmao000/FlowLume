# FlowLume - Lean Digital Senior Engineer AI Agent System

A manufacturing digital transformation AI Agent system that simulates the thinking and working patterns of a Lean Digital Senior Engineer, implementing digital twin, process optimization, and intelligent decision-making through 5 specialized agents.

## Core Features

| Agent | Name | Status | Core Responsibilities |
|:---|:---|:---|:---|
| Agent-01 | Strategic Planning | ✅ Complete | Maturity assessment, opportunity identification, Roadmap generation |
| Agent-02 | Change Enablement | ✅ Complete | Personalized training, adoption tracking |
| Agent-03 | Data Insight | ✅ Complete | Text-to-SQL, anomaly detection, root cause analysis |
| Agent-04 | Lean Optimization | ✅ Complete | Process mining, VSM generation, Kaizen proposals |
| Agent-05 | System Integration | 🔄 Planned | Requirements translation, UAT generation, data mapping |

## Architecture

```
Claude Code CLI (Orchestrator)
├── Agent-01: Strategic Planning (LangGraph)
├── Agent-02: Change Enablement (LangGraph)
├── Agent-03: Data Insight (LangGraph)
│   ├── Text-to-SQL (SQLGlot validation)
│   ├── Anomaly Detection (z-score / IQR)
│   └── Root Cause Analysis (LLM)
├── Agent-04: Lean Optimization (LangGraph)
│   ├── Event Log Processing
│   ├── VSM Calculator
│   └── Waste Identifier
└── Agent-05: System Integration (LangGraph) 🔄
    ├── BRD Parser
    ├── SAP/MES Config Generator
    └── Data Mapper
```

## Tech Stack

- **LLM**: Claude Sonnet 4.6
- **Workflow**: LangGraph (state machine orchestration)
- **SQL Validation**: SQLGlot
- **Database**: SQLite (PoC mock data)
- **Testing**: pytest (500+ test cases)

## Quick Start

```bash
# Install dependencies
pip install -e .

# Initialize mock database
python -c "from src.agents.data_insight.mock_database import init_mock_db; init_mock_db()"

# Run tests
pytest tests/ -v

# Use Agent
python -c "
from src.agents.data_insight import DataInsightAgent
agent = DataInsightAgent()
result = agent.analyze('Which production line had the lowest OEE yesterday?')
print(result)
"
```

## Project Structure

```
src/
├── agents/
│   ├── strategic_planning/    # Agent-01
│   ├── change_enablement/     # Agent-02
│   ├── data_insight/          # Agent-03
│   ├── lean_optimization/     # Agent-04
│   └── system_integration/   # Agent-05 🔄
├── prompts/                   # Agent system prompts
├── workflows/                 # LangGraph workflow definitions
└── llm/                       # LLM client wrapper
tests/
├── agents/                    # Agent unit tests
└── workflows/                 # Workflow integration tests
docs/
├── specs/                     # Agent technical design docs
└── plans/                     # Implementation plans
```

## Development Status

### Agent Implementation Status

| Agent | Features | Status | Test Cases |
|:---|:---|:---|:---|
| Agent-01 Strategic Planning | Maturity assessment, opportunity ID, ROI calculation, Roadmap | ✅ Complete | — |
| Agent-02 Change Enablement | Training generation, adoption tracking, SOP generation | ✅ Complete | — |
| Agent-03 Data Insight | Text-to-SQL, anomaly detection, root cause analysis, insight reports | ✅ Complete | 161 |
| Agent-04 Lean Optimization | Process mining, VSM calculation, waste identification, Kaizen proposals | ✅ Complete | 141 |
| Agent-05 System Integration | BRD parsing, SAP/MES config, UAT generation, data mapping | 🔄 Planned | — |

### Future Development Plan

| Priority | Feature | Description | Dependencies |
|:---|:---|:---|:---|
| P1 | Agent-05 System Integration | Complete SAP/MES requirements translation, UAT case generation, data mapping | Agent-03/04 |
| P2 | Cross-Agent Orchestration | Implement inter-agent state sharing and collaboration | Agent-05 |
| P2 | Real Database Integration | MySQL/PostgreSQL connectors replacing SQLite | — |
| P3 | Web UI | Gradio/Streamlit based interactive interface | P1 complete |
| P3 | Prediction Module | Historical data-based trend forecasting | Agent-03 |

## Test Coverage

| Agent | Test Cases |
|:---|:---|
| Agent-03 Data Insight | 161 tests |
| Agent-04 Lean Optimization | 141 tests |
| **Total** | **302+ tests** |

## Documentation

- [Business Requirements Doc](业务需求文档.md) - Original requirements source
- [Agent Design Docs](docs/superpowers/specs/) - Detailed technical design for each agent
- [Implementation Plans](docs/superpowers/plans/) - Iterative implementation plans

## License

MIT