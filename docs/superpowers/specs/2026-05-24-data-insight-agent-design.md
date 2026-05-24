# 数据洞察 Agent 技术验证设计文档

**日期**：2026-05-24
**Agent 编号**：Agent-03
**验证阶段**：PoC-03
**状态**：草稿

---

## 1. 问题陈述

### 1.1 背景

精益数字化高级工程师岗位的核心价值之一是"用数据说话"——将分散在 SAP、MES、IoT 设备中的生产数据转化为可行动的洞察。传统 BI 报表依赖静态模板，无法满足"实时监控 + 异常预警 + 根因分析"的动态需求。数据洞察 Agent 旨在验证：能否通过 Text-to-SQL + 实时数据管道 + LLM 推理，实现"问数据得答案"的交互体验。

### 1.2 验证目标

**主目标**：验证 Claude Code 平台能否通过自然语言查询生产数据库，并生成可解释的分析结果和行动建议。

**次目标**：
- 验证 Text-to-SQL 的准确率（复杂查询场景）
- 验证实时数据管道的稳定性
- 验证异常检测与预警的及时性
- 评估预测模型的可行性（PoC 阶段仅验证概念）

### 1.3 成功标准

| 指标 | 达标阈值 | 验证方法 |
|:---|:---|:---|
| Text-to-SQL 准确率 | ≥85% | 20 条测试 SQL，人工验证结果正确性 |
| 查询响应时间 | ≤10s（简单查询）/ ≤30s（复杂查询） | 计时器测量 |
| 异常预警召回率 | ≥90% | 注入已知异常，确认触发预警 |
| 看板刷新延迟 | ≤60s | 端到端延迟监控 |

---

## 2. 解决方案概述

### 2.1 核心功能

```
输入：
  - 自然语言查询（"昨天哪个产线 OEE 最低？"）
  - 数据源配置（SAP / MES / IoT 数据库连接）
  - 告警规则（阈值设定）

处理：
  - Text-to-SQL：LLM 将自然语言转为 SQL
  - 数据查询：执行 SQL 并获取结果
  - 异常检测：统计方法 + 规则引擎识别异常点
  - 根因分析：调用 LLM 推理异常原因
  - 预测建模（探索）：基于历史数据的趋势预测

输出：
  - 查询结果（表格 + 图表描述）
  - 自然语言解读（"OEE 最低的原因是 X"）
  - 异常告警（实时推送）
  - 根因分析报告
  - 预测趋势（可选）
```

### 2.2 技术架构

```
┌───────────────────────────────────────────────────────────────┐
│                       Claude Code CLI                          │
│           (Orchestrator: 查询分发 / 结果审核 / HITL)           │
└───────────────────────────┬───────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
┌───────▼──────┐    ┌──────▼──────┐    ┌─────▼─────┐
│  Text-to-SQL  │    │  异常检测   │    │  根因分析 │
│   模块        │    │  模块       │    │   模块    │
└───────┬───────┘    └──────┬──────┘    └─────┬─────┘
        │                   │                   │
        └───────────────────┼───────────────────┘
                            │
              ┌─────────────▼─────────────┐
              │       数据访问层 (DAL)      │
              │  SAP OData / MES REST /   │
              │  OPC UA / SQLite (模拟)   │
              └─────────────┬─────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
┌───────▼──────┐    ┌──────▼──────┐    ┌─────▼─────┐
│  SAP S/4HANA │    │    MES      │    │   IoT     │
│   数据库      │    │   数据库    │    │  时序数据  │
└──────────────┘    └─────────────┘    └───────────┘
```

### 2.3 Agent 系统提示词（初版）

```
你是制造业数据分析师，擅长：
1. 将业务问题转化为精确的 SQL 查询
2. 解读数据异常并推断可能原因
3. 生成可操作的改善建议
4. 用业务语言而非技术术语解释数据发现

工作流程：
1. 解析自然语言查询，识别关键实体（产线/时间/指标）
2. 构建 SQL 查询（处理日期过滤、聚合、JOIN）
3. 执行查询并验证结果合理性
4. 解读结果，生成自然语言总结
5. 如发现异常，触发根因分析流程
6. 生成可行动的改善建议

输出格式：
- 查询结果（表格形式，带列说明）
- 数据解读（自然语言，1-3 句话）
- 异常标记（如有异常，标注原因和置信度）
- 改善建议（如有，列出具体行动项）

注意：
- SQL 需包含明确的表名和字段来源
- 涉及财务或质量数据需标注数据敏感性
- 复杂查询需附带查询逻辑说明
```

---

## 3. 技术实现

### 3.1 依赖技术栈

| 组件 | 技术选型 | 用途 |
|:---|:---|:---|
| LLM | Claude Sonnet 4.6 (via Claude Code) | Text-to-SQL + 推理 |
| 数据库 | SQLite（模拟）+ MySQL/PostgreSQL（真实环境） | 数据存储 |
| SQL 解析 | SQLGlot / Jina AI SQL Parser | SQL 验证与优化 |
| 数据管道 | Python asyncio + APScheduler | 定时任务 + 实时轮询 |
| 异常检测 | scipy.stats + 规则引擎 | 统计异常检测 |
| 时序预测 | statsmodels / Prophet（可选） | 趋势预测探索 |
| 可视化 | Matplotlib / Plotly（生成图表描述） | 图表渲染 |

### 3.2 数据模型（PoC 阶段）

#### 3.2.1 模拟数据结构

```
表：production_daily
├── date: 日期
├── plant: 工厂
├── line: 产线
├── output_qty: 产出数量
├── defect_qty: 缺陷数量
├── downtime_hours: 停机时间
├── oee: OEE（计算得出）

表：equipment_status
├── timestamp: 时间戳
├── equipment_id: 设备 ID
├── status: 运行/停机/故障
├── temperature: 温度（可选）
├── pressure: 压力（可选）

表：quality_inspection
├── inspection_date: 检验日期
├── batch_no: 批次号
├── inspection_result: 合格/不合格
├── defect_type: 缺陷类型
├── quantity: 数量
```

#### 3.2.2 Text-to-SQL 映射规则

| 自然语言 | SQL 逻辑 |
|:---|:---|
| "昨天 OEE 最低的产线" | SELECT line, MIN(oee) FROM production_daily WHERE date = yesterday GROUP BY line ORDER BY oee LIMIT 1 |
| "停机超过 2 小时的次数" | SELECT COUNT(*) FROM equipment_status WHERE status = '停机' AND downtime_hours > 2 |
| "质量报废率趋势" | SELECT date, defect_qty/output_qty AS scrap_rate FROM production_daily ORDER BY date |

### 3.3 核心模块设计

#### 3.3.1 Agent 模块（`src/agents/data_insight_agent.py`）

```python
# 伪代码结构
class DataInsightAgent:
    def __init__(self, config):
        self.llm = ClaudeLLM(model="sonnet-4.6")
        self.sql_parser = SQLParser()  # SQLGlot
        self.db_conn = DatabaseConnection(config)
        self.anomaly_engine = AnomalyDetector()
        self.system_prompt = SYSTEM_PROMPT  # 见 2.3

    def text_to_sql(self, query: str, schema: dict) -> SQLQuery:
        """将自然语言转换为 SQL"""

    def execute_query(self, sql: SQLQuery) -> QueryResult:
        """执行 SQL 并验证结果"""

    def interpret_result(self, result: QueryResult) -> str:
        """生成自然语言解读"""

    def detect_anomaly(self, metric: str, threshold: float) -> List[AnomalyPoint]:
        """检测指定指标的异常"""

    def root_cause_analysis(self, anomaly: AnomalyPoint) -> RootCauseReport:
        """根因分析"""

    def generate_insight_report(self, query_result: QueryResult) -> InsightReport:
        """生成完整洞察报告"""
```

#### 3.3.2 数据管道模块（`src/pipeline/data_pipeline.py`）

```python
# 伪代码结构
class DataPipeline:
    def __init__(self, sources: List[DataSource]):
        self.sources = sources
        self.scheduler = APScheduler()

    def start_monitoring(self, metrics: List[str], interval: int = 60):
        """启动定时监控"""

    def fetch_data(self, source: DataSource) -> DataFrame:
        """从数据源拉取数据"""

    def aggregate_metrics(self, df: DataFrame) -> MetricsSnapshot:
        """聚合计算关键指标"""

    def trigger_alert(self, metric: str, value: float, threshold: float):
        """触发告警"""
```

### 3.4 工作流定义（LangGraph）

```
states:
  - natural_query: 用户自然语言查询
  - sql_query: 生成的 SQL 语句
  - query_result: 查询执行结果
  - interpretation: 自然语言解读
  - anomaly_flag: 异常标记
  - root_cause: 根因分析结果
  - insight_report: 完整洞察报告

nodes:
  - parse_query: 解析自然语言查询
  - generate_sql: 生成 SQL 语句
  - validate_sql: 验证 SQL 语法和安全性
  - execute_query: 执行查询
  - interpret_result: 解读查询结果
  - detect_anomaly: 检测异常
  - analyze_root_cause: 根因分析
  - generate_report: 生成洞察报告
  - human_review: 人工审核（HITL，复杂查询场景）

edges:
  - parse_query -> generate_sql
  - generate_sql -> validate_sql
  - validate_sql -> execute_query [label="验证通过"]
  - validate_sql -> generate_sql [label="验证失败，重试"]
  - execute_query -> interpret_result
  - interpret_result -> detect_anomaly
  - detect_anomaly -> analyze_root_cause [label="发现异常"]
  - detect_anomaly -> generate_report [label="无异常"]
  - analyze_root_cause -> generate_report
  - generate_report -> human_review [label="高价值/高风险"]
  - human_review: approve -> END
  - human_review: reject -> parse_query
```

---

## 4. 测试计划

### 4.1 测试用例

| 用例 ID | 场景描述 | 输入 | 预期输出 | 验证指标 |
|:---|:---|:---|:---|:---|
| TC-11 | 简单聚合查询 | "上周各产线产出是多少？" | 正确的汇总表 | SQL 准确率≥90% |
| TC-12 | 复杂 JOIN 查询 | "对比 MES 和 SAP 的工单完成率" | 跨系统对比数据 | JOIN 逻辑正确 |
| TC-13 | 异常检测 | 注入 OEE 异常数据 | 触发告警 | 召回率≥90% |
| TC-14 | 根因分析 | "为什么 3 号线昨天 OEE 下降？" | 根因分析报告 | 包含 ≥2 个可能原因 |
| TC-15 | Text-to-SQL 边界 | "找出所有名字以 A 开头的员工" | 拒绝/安全处理 | 无 SQL 注入风险 |

### 4.2 验证环境

| 环境 | 配置 | 用途 |
|:---|:---|:---|
| 本地开发 | SQLite + Python | 日常开发调试 |
| PoC 验证 | MySQL + 模拟生产数据 | 功能验证 + 性能测试 |
| 压力测试 | 10 万行数据 + 复杂 JOIN | 响应时间验证 |

### 4.3 评估方法

1. **SQL 准确率**：人工逐条验证生成的 SQL
2. **响应时间**：计时器测量 P50/P95/P99
3. **异常检测**：注入已知异常，确认触发率和误报率
4. **根因分析**：专家评审分析逻辑合理性

---

## 5. 已知限制与风险

| 风险 | 严重程度 | 缓解措施 |
|:---|:---|:---|
| Text-to-SQL 幻觉 | 高 | 白名单表/字段，LLM 输出需经 SQL 验证 |
| 数据泄露 | 高 | 禁止 LLM 直接访问生产库，SQL 审查层过滤 |
| 查询性能 | 中 | 限制结果集大小，超时熔断 |
| 跨系统 JOIN | 高 | PoC 仅验证单系统查询，跨系统留待 Agent-05 |
| 预测模型准确性 | 低 | PoC 阶段不承诺预测准确率，仅探索概念 |

---

## 6. 与其他 Agent 的接口

| 上游 Agent | 传递数据 | 说明 |
|:---|:---|:---|
| 战略规划 Agent | `maturity_assessment` 中的数据能力缺口 | 识别数据采集和分析改进方向 |
| 精益优化 Agent | 瓶颈分析所需的原始数据 | 提供数据查询支持 |

| 下游 Agent | 传递数据 | 说明 |
|:---|:---|:---|
| 精益优化 Agent | 接收异常告警和根因分析结果 | 聚焦流程优化机会 |
| 战略规划 Agent | 数据能力成熟度评分 | 更新路线图中的数据维度 |

---

## 7. 下一步行动

- [ ] 搭建 MySQL + 模拟生产数据集
- [ ] 实现 Text-to-SQL 模块（SQLGlot 集成）
- [ ] 实现异常检测引擎
- [ ] 执行 TC-11 ~ TC-15 测试
- [ ] 汇总 PoC-03 验证结论

---

*本文档为 PoC-03 阶段技术验证设计，与 Agent-01/02 保持一致的文档结构。*