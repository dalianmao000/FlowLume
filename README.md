# FlowLume - 精益数字化高级工程师 AI Agent 系统

制造业数字化转型 AI Agent 系统，模拟精益数字化高级工程师的思维和工作方式，通过 5 个专业 Agent 实现数字孪生、流程优化和智能决策。

## 核心功能

| Agent | 名称 | 状态 | 核心职责 |
|:---|:---|:---|:---|
| Agent-01 | 战略规划 | ✅ 已完成 | 成熟度评估、机会识别、Roadmap 生成 |
| Agent-02 | 变革赋能 | ✅ 已完成 | 个性化培训、adoption 追踪 |
| Agent-03 | 数据洞察 | ✅ 已完成 | Text-to-SQL、异常检测、根因分析 |
| Agent-04 | 精益优化 | ✅ 已完成 | 流程挖掘、VSM 生成、改善提案 |
| Agent-05 | 系统集成 | 🔄 待开发 | 需求转译、UAT 生成、数据映射 |

## 技术架构

```
Claude Code CLI (Orchestrator)
├── Agent-01: Strategic Planning (LangGraph)
├── Agent-02: Change Enablement (LangGraph)
├── Agent-03: Data Insight (LangGraph)
│   ├── Text-to-SQL (SQLGlot 验证)
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

## 技术栈

- **LLM**: Claude Sonnet 4.6
- **Workflow**: LangGraph (状态机编排)
- **SQL 验证**: SQLGlot
- **数据库**: SQLite (PoC 模拟数据)
- **测试**: pytest (500+ 测试用例)

## 快速开始

```bash
# 安装依赖
pip install -e .

# 初始化模拟数据库
python -c "from src.agents.data_insight.mock_database import init_mock_db; init_mock_db()"

# 运行测试
pytest tests/ -v

# 使用 Agent
python -c "
from src.agents.data_insight import DataInsightAgent
agent = DataInsightAgent()
result = agent.analyze('昨天哪个产线 OEE 最低？')
print(result)
"
```

## 项目结构

```
src/
├── agents/
│   ├── strategic_planning/    # Agent-01
│   ├── change_enablement/     # Agent-02
│   ├── data_insight/          # Agent-03
│   ├── lean_optimization/     # Agent-04
│   └── system_integration/   # Agent-05 🔄
├── prompts/                   # Agent 系统提示词
├── workflows/                 # LangGraph 工作流定义
└── llm/                       # LLM 客户端封装
tests/
├── agents/                    # Agent 单元测试
└── workflows/                # Workflow 集成测试
docs/
├── specs/                     # Agent 技术设计文档
└── plans/                     # 实施计划
```

## 开发进度

### Agent 实现状态

| Agent | 功能模块 | 状态 | 测试用例 |
|:---|:---|:---|:---|
| Agent-01 战略规划 | 成熟度评估、机会识别、ROI 测算、Roadmap 生成 | ✅ 已完成 | — |
| Agent-02 变革赋能 | 培训生成、adoption 追踪、SOP 生成 | ✅ 已完成 | — |
| Agent-03 数据洞察 | Text-to-SQL、异常检测、根因分析、洞察报告 | ✅ 已完成 | 161 |
| Agent-04 精益优化 | 流程挖掘、VSM 计算、浪费识别、改善提案 | ✅ 已完成 | 141 |
| Agent-05 系统集成 | BRD 解析、SAP/MES 配置、UAT 生成、数据映射 | 🔄 待开发 | — |

### 未来开发计划

| 优先级 | 功能 | 描述 | 依赖 |
|:---|:---|:---|:---|
| P1 | Agent-05 系统集成 | 完成 SAP/MES 需求转译、UAT 用例生成、数据映射表生成 | Agent-03/04 |
| P2 | 跨 Agent 编排 | 实现 Agent 间状态共享与协作流程 | Agent-05 |
| P2 | 真实数据库集成 | MySQL/PostgreSQL 连接器替代 SQLite | — |
| P3 | Web UI | 基于 Gradio/Streamlit 的交互界面 | P1 完成 |
| P3 | 预测模型 | 基于历史数据的趋势预测模块 | Agent-03 |

## 测试覆盖

| Agent | 测试用例数 |
|:---|:---|
| Agent-03 Data Insight | 161 tests |
| Agent-04 Lean Optimization | 141 tests |
| **总计** | **302+ tests** |

## 文档

- [业务需求文档](业务需求文档.md) - 原始需求来源
- [Agent 设计文档](docs/superpowers/specs/) - 各 Agent 详细技术设计
- [实施计划](docs/superpowers/plans/) - 迭代实施计划

## License

MIT