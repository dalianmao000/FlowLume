# 系统集成 Agent 技术验证设计文档

**日期**：2026-05-24
**Agent 编号**：Agent-05
**验证阶段**：PoC-05
**状态**：草稿

---

## 1. 问题陈述

### 1.1 背景

精益数字化高级工程师岗位的技术核心之一是 SAP S/4HANA 和 MES 系统的实施与集成。这包括：业务需求转译、配置校验、UAT 测试、数据映射和缺陷追踪。传统方式依赖大量人工文档和沟通，容易出现需求失真和集成遗漏。系统集成 Agent 旨在验证：能否通过 LLM + 文档理解 + API 模拟，实现业务需求到系统配置的自动化桥梁。

### 1.2 验证目标

**主目标**：验证 Claude Code 平台能否从业务需求文档（BRD）自动生成 SAP/MES 配置建议，并自动化生成 UAT 测试用例。

**次目标**：
- 验证需求转译的准确性（业务语言 → 系统配置逻辑）
- 验证 UAT 用例生成的覆盖率
- 验证数据映射的完整性
- 探索 SAP/MES API 的自动化测试能力

### 1.3 成功标准

| 指标 | 达标阈值 | 验证方法 |
|:---|:---|:---|
| 需求转译准确率 | ≥85% | 专家评审，对比原需求与生成配置 |
| UAT 用例覆盖率 | ≥90% | 覆盖关键业务流程路径 |
| 配置建议完整性 | ≥80% | 检查必需配置项是否包含 |
| 数据映射准确率 | ≥90% | 与人工映射表对比 |

---

## 2. 解决方案概述

### 2.1 核心功能

```
输入：
  - 业务需求文档（BRD，Word/Markdown 格式）
  - SAP S/4HANA 模块文档（PP/MM/QM/PM）
  - MES 系统接口文档（REST API + 数据字典）
  - 现有系统配置（如有）

处理：
  - 文档解析：提取业务需求中的关键实体和流程
  - 需求转译：将业务需求映射到 SAP/MES 配置项
  - 用例生成：从业务流程自动生成 UAT 测试步骤
  - 数据映射：生成 SAP ↔ MES 字段映射表
  - 缺陷分析：基于错误日志推断配置问题

输出：
  - 配置建议清单（SAP 配置项 + MES 配置项）
  - UAT 测试用例集（Excel 格式，可导入 TestRail）
  - 数据映射表（SAP ↔ MES 字段对应）
  - 配置变更草案（供人工审核）
```

### 2.2 技术架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        Claude Code CLI                           │
│              (Orchestrator: 文档处理 / 配置生成 / HITL)           │
└────────────────────────────────┬────────────────────────────────┘
                                 │
         ┌───────────────────────┼───────────────────────┐
         │                       │                       │
┌────────▼───────┐    ┌─────────▼──────┐    ┌─────────▼──────┐
│   文档解析     │    │   需求转译      │    │   用例生成     │
│     模块       │    │     模块        │    │     模块       │
└────────┬───────┘    └─────────┬──────┘    └─────────┬──────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
              ┌──────────────────▼──────────────────┐
              │           配置与映射引擎              │
              │  SAP 配置知识库 │ MES 配置知识库 │     │
              │  数据映射规则   │ 字段转换逻辑   │     │
              └──────────────────┬──────────────────┘
                                 │
         ┌───────────────────────┼───────────────────────┐
         │                       │                       │
┌────────▼───────┐    ┌─────────▼──────┐    ┌─────────▼──────┐
│   SAP S/4HANA  │    │      MES       │    │   模拟器        │
│   配置知识库    │    │   配置知识库    │    │  (Mock Server) │
│  (PP/MM/QM/PM) │    │  (排产/报工)   │    │               │
└────────────────┘    └────────────────┘    └────────────────┘
```

### 2.3 Agent 系统提示词（初版）

```
你是 SAP/MES 系统实施专家，擅长：
1. 将业务需求文档转化为精确的系统配置项
2. 理解 SAP S/4HANA PP/MM/QM/PM 模块的配置逻辑
3. 理解 MES 排产、报工、质量追溯的配置逻辑
4. 生成覆盖完整业务流程的 UAT 测试用例
5. 设计 SAP 与 MES 之间的数据映射关系

工作流程：
1. 解析业务需求文档（BRD），提取关键实体和流程
2. 识别涉及的系统模块（SAP 模块 + MES 功能）
3. 从知识库中匹配对应的配置项
4. 生成 SAP 配置建议（事务代码 + 配置路径 + 参数值）
5. 生成 MES 配置建议（功能模块 + 参数设置）
6. 从业务流程中推演 UAT 测试步骤
7. 生成 SAP ↔ MES 数据映射表
8. 生成配置变更草案供人工审核

输出格式：
- SAP 配置清单（事务码 + 配置路径 + 说明）
- MES 配置清单（功能模块 + 配置项 + 说明）
- UAT 测试用例（步骤 + 预期结果 + 测试数据）
- 数据映射表（SAP 字段 ↔ MES 字段）
- 配置变更草案（可导出为 Word）

注意：
- 所有配置建议需标注适用条件和前提依赖
- 涉及跨系统数据流必须标注接口方式和数据格式
- 核心配置变更（如物料主数据、BOM）需标注"需人工审批"
```

---

## 3. 技术实现

### 3.1 依赖技术栈

| 组件 | 技术选型 | 用途 |
|:---|:---|:---|
| LLM | Claude Sonnet 4.6 (via Claude Code) | 文档理解 + 配置推理 |
| 文档解析 | python-docx / PyMuPDF | Word/PDF 解析 |
| SAP 知识库 | 本地 Markdown/SQLite | SAP 配置逻辑存储 |
| MES 知识库 | 本地 Markdown/SQLite | MES 配置逻辑存储 |
| API 模拟 | FastAPI + Mock 数据 | SAP/MES 接口模拟 |
| 用例导出 | openpyxl | 生成 Excel 格式 UAT 用例 |

### 3.2 知识库结构（PoC 阶段）

#### 3.2.1 SAP S/4HANA 配置知识库（精简版）

| 业务场景 | 相关模块 | 事务代码 | 配置路径 | 关键参数 |
|:---|:---|:---|:---|:---|
| 工单创建 | PP | CO01 | 工厂参数 | 订单类型/工序编码 | |
| 物料移动 | MM | MIGO | 移动类型 | 移动标识/库存地点 | |
| 质量检验 | QM | Q01 | 检验类型 | 检验代码/采样程序 | |
| 设备维护 | PM | IW31 | 维护订单类型 | 工厂/优先级 | |

#### 3.2.2 MES 功能配置知识库（精简版）

| 业务场景 | MES 模块 | 配置项 | 说明 |
|:---|:---|:---|:---|
| 报工 | 生产报工 | 报工方式 | 扫码/手动 |
| 排产 | 生产排程 | 排产规则 | 优先级/产能约束 |
| 质量追溯 | 质量追溯 | 追溯颗粒度 | 批次/单品 |

#### 3.2.3 数据映射规则

```
SAP → MES：
- 工单号 (AUFM-AUFNR) → MES 工单 ID
- 物料号 (MARA-MATNR) → MES 物料编码
- 工序代码 (PLKO-PLNNR) → MES 工序 ID
- 检验结果 (QALS) → MES 质检结论

MES → SAP：
- 报工数量 → 工单确认数量 (CONFIRM)
- 不良品数量 → 报工不良 (METHOD: 101)
```

### 3.3 核心模块设计

#### 3.3.1 Agent 模块（`src/agents/system_integration_agent.py`）

```python
# 伪代码结构
class SystemIntegrationAgent:
    def __init__(self, config):
        self.llm = ClaudeLLM(model="sonnet-4.6")
        self.sap_kb = KnowledgeBase("sap_config_kb")
        self.mes_kb = KnowledgeBase("mes_config_kb")
        self.doc_parser = DocumentParser()
        self.uat_generator = UATGenerator()
        self.data_mapper = DataMapper()
        self.system_prompt = SYSTEM_PROMPT  # 见 2.3

    def parse_brd(self, doc_path: str) -> BusinessRequirements:
        """解析业务需求文档"""

    def translate_to_sap_config(self, req: BusinessRequirements) -> List[SAPConfigItem]:
        """将业务需求转译为 SAP 配置项"""

    def translate_to_mes_config(self, req: BusinessRequirements) -> List[MESConfigItem]:
        """将业务需求转译为 MES 配置项"""

    def generate_uat_cases(self, process: BusinessProcess) -> List[UATCase]:
        """从业务流程生成 UAT 测试用例"""

    def generate_data_mapping(self, sap_fields: List, mes_fields: List) -> DataMappingTable:
        """生成 SAP ↔ MES 数据映射表"""

    def analyze_defect_log(self, error_log: str) -> ConfigSuggestion:
        """基于错误日志分析配置问题"""
```

#### 3.3.2 文档解析模块（`src/parsing/brd_parser.py`）

```python
# 伪代码结构
class BRDParser:
    def __init__(self):
        self.llm = ClaudeLLM(model="sonnet-4.6")

    def parse_document(self, file_path: str) -> BusinessRequirements:
        """解析 BRD，提取关键实体和流程"""

    def extract_entities(self, text: str) -> List[Entity]:
        """提取实体（物料/工单/设备/供应商等）"""

    def extract_processes(self, text: str) -> List[ProcessStep]:
        """提取业务流程步骤"""

    def extract_constraints(self, text: str) -> List[Constraint]:
        """提取约束条件（业务规则）"""
```

### 3.4 工作流定义（LangGraph）

```
states:
  - brd_document: 业务需求文档
  - parsed_requirements: 解析后的需求
  - sap_config_items: SAP 配置建议
  - mes_config_items: MES 配置建议
  - uat_cases: UAT 测试用例集
  - data_mapping: 数据映射表
  - config_draft: 配置变更草案

nodes:
  - parse_brd: 解析业务需求文档
  - identify_modules: 识别涉及的系统模块
  - translate_sap: 生成 SAP 配置建议
  - translate_mes: 生成 MES 配置建议
  - generate_uat: 生成 UAT 测试用例
  - generate_mapping: 生成数据映射表
  - compile_draft: 汇编配置变更草案
  - human_review: 人工审核（HITL）

edges:
  - parse_brd -> identify_modules
  - identify_modules -> translate_sap
  - identify_modules -> translate_mes
  - translate_sap -> generate_uat
  - translate_mes -> generate_uat
  - generate_uat -> generate_mapping
  - generate_mapping -> compile_draft
  - compile_draft -> human_review [label="高风险配置"]
  - human_review: approve -> END
  - human_review: reject -> parse_brd
```

---

## 4. 测试计划

### 4.1 测试用例

| 用例 ID | 场景描述 | 输入 | 预期输出 | 验证指标 |
|:---|:---|:---|:---|:---|
| TC-21 | 基础 BRD 解析 | 工单创建需求文档 | 提取关键实体 + 流程步骤 | 实体识别准确率≥85% |
| TC-22 | SAP 配置生成 | "需要支持工单分批报工" | SAP 配置清单（事务码+路径） | 配置项完整率≥80% |
| TC-23 | MES 配置生成 | "报工需要支持扫码方式" | MES 配置清单 | 配置项完整率≥80% |
| TC-24 | UAT 用例生成 | 完整生产报工流程 | 10+ 条 UAT 测试用例 | 覆盖率≥90% |
| TC-25 | 数据映射生成 | SAP 工单字段 + MES 报工字段 | 映射表（字段对应） | 映射准确率≥90% |

### 4.2 验证环境

| 环境 | 配置 | 用途 |
|:---|:---|:---|
| 本地开发 | Python + 本地知识库 | 日常开发调试 |
| PoC 验证 | Mock Server（FastAPI） | SAP/MES 接口模拟 |
| 集成测试 | 需连接真实 SAP/MES 环境 | 完整流程验证（后期） |

### 4.3 评估方法

1. **需求转译准确性**：专家评审，对比原需求与生成配置
2. **UAT 覆盖率**：与标准业务流程清单对比
3. **数据映射完整性**：与人工映射表逐项核对

---

## 5. 已知限制与风险

| 风险 | 严重程度 | 缓解措施 |
|:---|:---|:---|
| SAP 知识库不完整 | 高 | PoC 仅覆盖核心场景（PP/MM/QM），其余留待扩展 |
| MES 接口标准化程度低 | 高 | 预设主流 MES 品牌（西门子/罗克韦尔）的适配层 |
| 配置项有版本差异 | 中 | 知识库标注版本号，输出时附带版本假设 |
| 涉及财务配置 | 高 | PoC 不涉及财务模块，明确标注排除范围 |

---

## 6. 与其他 Agent 的接口

| 上游 Agent | 传递数据 | 说明 |
|:---|:---|:---|
| 战略规划 Agent | `roadmap` 中的系统实施节点 | 确定哪些系统需要上线/配置 |
| 精益优化 Agent | 改善提案中的 IT 需求 | 判断哪些需要 SAP/MES 配置变更 |

| 下游 Agent | 传递数据 | 说明 |
|:---|:---|:---|
| 数据洞察 Agent | 接收配置后的系统数据 | 监控配置变更效果 |
| 变革赋能 Agent | 接收新功能上线通知 | 准备对应培训内容 |

---

## 7. 下一步行动

- [ ] 构建 SAP 配置知识库（PP/MM 模块，核心场景）
- [ ] 构建 MES 配置知识库（排产/报工/质量追溯）
- [ ] 实现 BRD 解析模块
- [ ] 执行 TC-21 ~ TC-25 测试
- [ ] 汇总 PoC-05 验证结论

---

## 8. 五个 Agent 汇总

| Agent | 核心职责 | PoC 优先级 | 外部依赖 | 验证难度 |
|:---|:---|:---|:---|:---|
| Agent-01 战略规划 | 成熟度评估 / 机会识别 / Roadmap 生成 | #1 | 低 | 低 |
| Agent-02 变革赋能 | 个性化培训 / adoption 追踪 | #1 | 低 | 低 |
| Agent-03 数据洞察 | Text-to-SQL / 异常检测 / 根因分析 | #2 | 中 | 中 |
| Agent-04 精益优化 | 流程挖掘 / VSM 生成 / 改善提案 | #2 | 中 | 中 |
| Agent-05 系统集成 | 需求转译 / UAT 生成 / 数据映射 | #3 | 高 | 高 |

---

*本文档为 PoC-05 阶段技术验证设计，与 Agent-01/02/03/04 保持一致的文档结构。*