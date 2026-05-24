# 精益优化 Agent 技术验证设计文档

**日期**：2026-05-24
**Agent 编号**：Agent-04
**验证阶段**：PoC-04
**状态**：草稿

---

## 1. 问题陈述

### 1.1 背景

精益数字化高级工程师岗位的核心技能之一是运用精益方法论（VSM、Kaizen、5Why 等）识别和消除流程浪费。传统方式依赖顾问现场调研和手工绘图，周期长、成本高。精益优化 Agent 旨在验证：能否通过流程挖掘 + LLM 推理，自动从系统日志中生成价值流图（VSM）并识别改善机会。

### 1.2 验证目标

**主目标**：验证 Claude Code 平台能否从生产工单日志和设备状态事件流中，自动生成 VSM 并输出可落地的改善建议。

**次目标**：
- 验证流程挖掘算法的准确性（与传统 VSM 人工绘制对比）
- 验证浪费识别（Muda/Mura/Muri）的覆盖率和准确率
- 评估改善建议的可执行性（专家评审）

### 1.3 成功标准

| 指标 | 达标阈值 | 验证方法 |
|:---|:---|:---|
| VSM 生成完整率 | ≥90% | 对照标准 VSM 六要素，覆盖率≥90% |
| 瓶颈识别准确率 | ≥80% | 与人工分析对比，一致率≥80% |
| 改善建议命中率 | ≥70% | 专家评审，可执行建议占比 |
| 单次分析耗时 | ≤5min（单产线） | 计时器测量 |

---

## 2. 解决方案概述

### 2.1 核心功能

```
输入：
  - 工单日志（订单创建 → 工序完成 → 交付）
  - 设备状态事件（运行/待机/停机/故障）
  - 工时记录（人工操作时间）
  - 库存数据（在制品数量）

处理：
  - 流程挖掘：从事件日志中重建流程路径
  - VSM 绘制：计算每个工序的增值时间/非增值时间
  - 浪费识别：标注 Muda（浪费）/ Mura（不均衡）/ Muri（过载）
  - 瓶颈定位：识别等待时间和在制品堆积点
  - 改善建议：生成 Kaizen 提案

输出：
  - 现状 VSM（甘特图形式）
  - 浪费清单（分类 + 量化损失）
  - 瓶颈分析报告
  - 改善建议（优先级排序）
  - 目标态 VSM（改善后预测）
```

### 2.2 技术架构

```
┌───────────────────────────────────────────────────────────────┐
│                       Claude Code CLI                          │
│             (Orchestrator: 任务编排 / 质量审核 / HITL)          │
└───────────────────────────┬───────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
┌───────▼──────┐    ┌──────▼──────┐    ┌─────▼─────┐
│  流程挖掘    │    │   VSM 生成  │    │  浪费识别  │
│   模块       │    │   模块       │    │   模块    │
└───────┬──────┘    └──────┬──────┘    └─────┬─────┘
        │                   │                │
        └───────────────────┼────────────────┘
                            │
              ┌─────────────▼─────────────┐
              │        数据访问层          │
              │  MES 工单 / 设备事件 /     │
              │  工时系统 / 库存台账       │
              └─────────────┬─────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
┌───────▼──────┐    ┌──────▼──────┐    ┌─────▼─────┐
│   MES        │    │  设备 IoT   │    │  工时系统  │
│   工单数据    │    │  状态数据   │    │   数据    │
└──────────────┘    └─────────────┘    └───────────┘
```

### 2.3 Agent 系统提示词（初版）

```
你是制造业精益改善专家，擅长：
1. 从系统日志中重建真实流程（流程挖掘）
2. 绘制价值流图（VSM）并量化每个工序的增值/非增值时间
3. 识别七种浪费（Muda: 等待/搬运/加工/库存/动作/缺陷/过度生产）
4. 定位流程瓶颈并提出具体改善方案
5. 设计目标态流程并估算改善效果

工作流程：
1. 收集数据源（工单日志 + 设备事件 + 工时记录）
2. 执行流程挖掘，重建流程路径
3. 计算每个工序的增值时间（VA）和非增值时间（NVA）
4. 标注库存堆积点和等待点
5. 识别浪费类型并量化时间损失
6. 定位瓶颈工序
7. 生成改善建议（按 Impact/Effort 排序）
8. 绘制目标态 VSM（改善后预测）

输出格式：
- 现状 VSM（文本表格，含时间轴）
- 浪费清单（分类 + 量化损失，如"等待时间：X 小时/周"）
- 瓶颈分析（根因 + 影响）
- 改善建议（优先级矩阵，Impact vs Effort）
- 目标态 VSM（预测值）

注意：
- 所有数据必须标注来源和计算逻辑
- 改善建议需附带实施条件（如：需要 IT 支持/需要培训）
- 涉及重大变更的建议标注"需人工审批"
```

---

## 3. 技术实现

### 3.1 依赖技术栈

| 组件 | 技术选型 | 用途 |
|:---|:---|:---|
| LLM | Claude Sonnet 4.6 (via Claude Code) | VSM 生成 + 推理 |
| 流程挖掘 | 自研算法 / Celonis（探索） | 流程路径重建 |
| 图数据库 | Neo4j（存储流程依赖） | 流程关系建模 |
| 时序计算 | Pandas + NumPy | 增值时间计算 |
| 离散事件仿真 | SimPy（探索） | 目标态 VSM 预测 |
| 规则引擎 | Drools / 规则集 | 浪费识别逻辑 |

### 3.2 数据模型（PoC 阶段）

#### 3.2.1 工单日志事件（模拟）

```
事件类型：
- ORDER_CREATED: 订单创建
- ORDER_RELEASED: 订单释放到产线
- OP_START: 工序开始
- OP_COMPLETE: 工序完成
- QC_PASS: 质检通过
- QC_FAIL: 质检失败
- ORDER_SHIPPED: 订单发货

事件字段：
├── event_id: 唯一标识
├── order_id: 订单号
├── event_type: 事件类型
├── operation: 工序名称
├── equipment_id: 设备 ID
├── start_time: 开始时间
├── end_time: 结束时间（可选）
├── quantity: 数量
├── location: 位置
```

#### 3.2.2 设备状态事件

```
状态类型：
- RUNNING: 运行中
- IDLE: 待机
- DOWN: 故障停机
- MAINTENANCE: 维护中

事件字段：
├── timestamp
├── equipment_id
├── status
├── duration: 持续时间
├── reason: 停机原因（可选）
```

### 3.3 核心模块设计

#### 3.3.1 Agent 模块（`src/agents/lean_optimization_agent.py`）

```python
# 伪代码结构
class LeanOptimizationAgent:
    def __init__(self, config):
        self.llm = ClaudeLLM(model="sonnet-4.6")
        self.process_miner = ProcessMiner()
        self.graph_db = Neo4jConnection(config.neo4j)
        self.simulation_engine = SimPyEngine()
        self.system_prompt = SYSTEM_PROMPT  # 见 2.3

    def collect_data(self, date_range: tuple) -> ProcessData:
        """从各数据源收集工单/设备/工时数据"""

    def mine_process(self, events: List[Event]) -> ProcessGraph:
        """从事件日志中挖掘流程路径"""

    def calculate_vsm(self, process_graph: ProcessGraph) -> VSMReport:
        """计算增值时间/非增值时间，生成 VSM"""

    def identify_waste(self, vsm: VSMReport) -> List[WastItem]:
        """识别七种浪费，量化损失"""

    def locate_bottlenecks(self, vsm: VSMReport) -> List[Bottleneck]:
        """定位瓶颈工序"""

    def generate_kaizen_proposals(self, vsm: VSMReport, bottlenecks: List[Bottleneck]) -> List[KaizenProposal]:
        """生成改善提案，按 Impact/Effort 排序"""

    def simulate_improvement(self, proposal: KaizenProposal, vsm: VSMReport) -> VSMReport:
        """仿真验证改善效果，生成目标态 VSM"""
```

#### 3.3.2 流程挖掘模块（`src/process_mining/event_log_processor.py`）

```python
# 伪代码结构
class ProcessMiner:
    def __init__(self):
        self.activity_graph = nx.DiGraph()  # NetworkX

    def parse_events(self, events: List[Event]) -> pd.DataFrame:
        """解析事件日志，转换为 DataFrame"""

    def discover_paths(self, df: pd.DataFrame) -> List[ProcessPath]:
        """发现流程路径（并行/串行/循环）"""

    def calculate_cycle_times(self, df: pd.DataFrame) -> Dict[str, float]:
        """计算各工序周期时间"""

    def identify_wait_times(self, df: pd.DataFrame) -> Dict[str, float]:
        """识别工序间等待时间"""

    def build_vsm_data(self, paths: List[ProcessPath], times: Dict) -> VSMData:
        """构建 VSM 数据结构"""
```

### 3.4 工作流定义（LangGraph）

```
states:
  - raw_data: 原始工单/设备/工时数据
  - process_graph: 挖掘后的流程图
  - current_vsm: 现状 VSM
  - waste_list: 浪费清单
  - bottlenecks: 瓶颈列表
  - kaizen_proposals: 改善提案
  - target_vsm: 目标态 VSM

nodes:
  - collect_data: 收集各数据源数据
  - parse_events: 解析事件日志
  - discover_process: 挖掘流程路径
  - calculate_vsm: 计算 VSM（增值/非增值时间）
  - identify_waste: 识别浪费类型
  - locate_bottleneck: 定位瓶颈
  - generate_proposals: 生成改善提案
  - simulate_improvement: 仿真验证改善效果
  - human_review: 人工审核（HITL）

edges:
  - collect_data -> parse_events
  - parse_events -> discover_process
  - discover_process -> calculate_vsm
  - calculate_vsm -> identify_waste
  - calculate_vsm -> locate_bottleneck
  - identify_waste -> generate_proposals
  - locate_bottleneck -> generate_proposals
  - generate_proposals -> simulate_improvement
  - simulate_improvement -> target_vsm
  - target_vsm -> human_review [label="高价值提案"]
  - human_review: approve -> END
  - human_review: reject -> collect_data
```

---

## 4. 测试计划

### 4.1 测试用例

| 用例 ID | 场景描述 | 输入 | 预期输出 | 验证指标 |
|:---|:---|:---|:---|:---|
| TC-16 | 基础 VSM 生成 | 单产线 1 周工单日志 | 完整 VSM（六要素） | 覆盖率≥90% |
| TC-17 | 多产线对比 | 3 条产线并行数据 | 各产线 VSM + 对比分析 | 瓶颈识别一致 |
| TC-18 | 浪费识别 | 注入已知浪费场景 | 浪费清单（分类+量化） | 识别准确率≥80% |
| TC-19 | 改善提案 | 基于 VSM + 瓶颈 | 3-5 个改善建议 | 可执行率≥70% |
| TC-20 | 目标态仿真 | 选择改善提案 | 目标态 VSM + 预测效果 | 逻辑自洽 |

### 4.2 验证环境

| 环境 | 配置 | 用途 |
|:---|:---|:---|
| 本地开发 | Python + SQLite（模拟数据） | 日常开发调试 |
| PoC 验证 | Neo4j + 模拟工单数据 | 流程挖掘验证 |
| 性能测试 | 1000+ 工单/天 | VSM 生成性能 |

### 4.3 评估方法

1. **VSM 完整性**：人工对照标准 VSM 六要素逐项核对
2. **瓶颈一致性**：与资深精益顾问的判断对比
3. **改善建议评审**：组织专家打分（可执行性 + Impact）

---

## 5. 已知限制与风险

| 风险 | 严重程度 | 缓解措施 |
|:---|:---|:---|
| 数据质量依赖 | 高 | PoC 使用高质量模拟数据，标注数据质量要求 |
| 流程挖掘准确性 | 中 | 仅验证"主路径"识别，循环/异常路径留待优化 |
| 目标态预测可信度 | 低 | 明确标注"预测值"，不承诺准确率 |
| 计算复杂度 | 中 | 限制分析窗口（1 周内），避免大规模数据 |

---

## 6. 与其他 Agent 的接口

| 上游 Agent | 传递数据 | 说明 |
|:---|:---|:---|
| 战略规划 Agent | `opportunities` 中的流程优化机会 | 接收优先级，聚焦分析 |
| 数据洞察 Agent | 异常告警触发 | 接收异常信号，启动专项分析 |

| 下游 Agent | 传递数据 | 说明 |
|:---|:---|:---|
| 系统集成 Agent | 接收改善提案中的 IT 需求 | 判断哪些需要修改 SAP/MES 配置 |
| 变革赋能 Agent | 接收培训需求（改善提案涉及 SOP 变更） | 提前准备对应培训 |
| 战略规划 Agent | 流程优化效果数据 | 更新路线图中的效率目标 |

---

## 7. 下一步行动

- [ ] 准备模拟工单日志数据集（1 周，3 条产线）
- [ ] 搭建 Neo4j 图数据库
- [ ] 实现流程挖掘核心算法
- [ ] 执行 TC-16 ~ TC-20 测试
- [ ] 汇总 PoC-04 验证结论

---

*本文档为 PoC-04 阶段技术验证设计，与 Agent-01/02/03 保持一致的文档结构。*