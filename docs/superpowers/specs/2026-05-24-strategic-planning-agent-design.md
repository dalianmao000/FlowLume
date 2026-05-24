# 战略规划 Agent 技术验证设计文档

**日期**：2026-05-24
**Agent 编号**：Agent-01
**验证阶段**：PoC-01
**状态**：草稿

---

## 1. 问题陈述

### 1.1 背景

精益数字化高级工程师岗位的核心职责之一是制定数字化转型路线图。当前行业内大多数企业依赖咨询公司或内部高管的经验判断，缺乏结构化的数据分析支撑。战略规划 Agent 旨在验证：通过 LLM + RAG 技术，能否自动化生成高质量的数字化转型策略报告。

### 1.2 验证目标

**主目标**：验证 Claude Code 平台能否在无外部企业系统依赖的情况下，基于公开数据源生成可供参考的数字化转型战略报告。

**次目标**：
- 验证 RAG 检索的准确性（与人工分析对比）
- 验证 LLM 生成报告的结构化程度
- 评估 Token 消耗与响应质量的关系

### 1.3 成功标准

| 指标 | 达标阈值 | 验证方法 |
|:---|:---|:---|
| 报告生成成功率 | ≥90% | 连续 10 次测试，≥9 次成功 |
| 关键维度覆盖率 | ≥85% | 对照业务需求文档，检查报告章节 |
| 战略建议可执行性 | 专家评分 ≥3.5/5 | 组织内部评审 |
| 单次响应时间 | ≤30s | 计时器测量 |

---

## 2. 解决方案概述

### 2.1 核心功能

```
输入：
  - 企业基础信息（行业、规模、现有数字化基础）
  - 分析维度偏好（成本优先/质量优先/效率优先）
  - 参考资料（可选：内部文档、行业报告）

处理：
  - RAG 检索：向量数据库匹配相关行业最佳实践
  - LLM 生成：调用 Claude Sonnet 4.6 生成结构化报告
  - 后处理：格式化输出为 Markdown/PDF

输出：
  - 数字化成熟度评估（雷达图数据）
  - 机会优先级矩阵
  - 3年转型路线图（甘特图格式）
  - ROI 初步测算
```

### 2.2 技术架构

```
┌─────────────────────────────────────────────┐
│              Claude Code CLI                │
│  (Orchestrator: 任务分发 / 质量审核 / HITL) │
└────────────────────┬────────────────────────┘
                     │ Skill 调用
┌────────────────────▼────────────────────────┐
│           战略规划 Agent (Agent-01)         │
│  - system prompt (角色定义)                 │
│  - 工具集 (WebSearch, Read, Bash)           │
│  - RAG Pipeline (Milvus + LangChain)        │
└────────────────────┬────────────────────────┘
                     │
        ┌────────────┴────────────┐
        │                         │
┌───────▼──────┐          ┌──────▼──────┐
│  公开数据源   │          │  向量知识库  │
│  (行业报告)   │          │ (本地存储)   │
└──────────────┘          └─────────────┘
```

### 2.3 Agent 系统提示词（初版）

```
你是数字化转型战略规划专家，擅长：
1. 分析企业当前数字化成熟度（基于行业基准）
2. 识别高价值数字化机会点（ROI 导向）
3. 制定可落地的 3 年转型路线图
4. 评估技术风险与组织准备度

工作流程：
1. 收集企业基础信息（行业、规模、现有系统）
2. 检索相关行业数字化转型最佳实践
3. 生成数字化成熟度评估报告
4. 输出机会优先级矩阵和路线图

输出格式：
- 成熟度评估报告（文本 + 五维雷达图数据点，可用 Python/Matplotlib 渲染）
- 机会优先级矩阵（文本表格 + Impact/Effort 坐标数据）
- 3年路线图（Markdown 甘特图文本格式，附日期范围数据）
- ROI 初步测算表（结构化文本，可导入 Excel）

注意：
- 所有建议必须附带适用条件和潜在风险
- 涉及重大投资的建议需标注"需人工审批"
```

---

## 3. 技术实现

### 3.1 依赖技术栈

| 组件 | 技术选型 | 用途 |
|:---|:---|:---|
| LLM | Claude Sonnet 4.6 (via Claude Code) | 核心推理引擎 |
| RAG 检索 | LangChain + Milvus (本地) | 知识检索 |
| 文档解析 | PyMuPDF / pdfplumber | 行业报告解析 |
| 向量嵌入 | sentence-transformers (all-MiniLM-L6-v2) | 文本向量化 |
| 报告生成 | Claude Code + Markdown | 结构化输出 |

### 3.2 RAG 数据源（PoC 阶段）

| 数据源 | 类型 | 公开可用性 | 用途 |
|:---|:---|:---|:---|
| Gartner 数字化转型报告 | PDF | 需申请/公开摘要 | 行业基准 |
| 麦肯锡制造业数字化洞察 | 网页 | 公开部分 | 转型框架 |
| IEC 工业 4.0 白皮书 | PDF | 公开 | 技术成熟度模型 |
| 中国智能制造 2025 规划 | 政府文件 | 公开 | 政策合规性参考 |

### 3.3 核心模块设计

#### 3.3.1 Agent 模块（`src/agents/strategic_planning_agent.py`）

```python
# 伪代码结构
class StrategicPlanningAgent:
    def __init__(self, config):
        self.llm = ClaudeLLM(model="sonnet-4.6")
        self.rag_pipeline = RAGPipeline(
            vector_store="milvus",
            embedding_model="all-MiniLM-L6-v2"
        )
        self.system_prompt = SYSTEM_PROMPT  # 见 2.3

    def assess_digital_maturity(self, company_info: dict) -> MaturityReport:
        """生成数字化成熟度评估"""

    def identify_opportunities(self, industry: str, constraints: dict) -> List[Opportunity]:
        """识别数字化机会点"""

    def generate_roadmap(self, opportunities: List[Opportunity], timeline: str) -> Roadmap:
        """生成转型路线图"""

    def estimate_roi(self, roadmap: Roadmap, company_scale: dict) -> ROIModel:
        """初步 ROI 测算"""
```

#### 3.3.2 RAG 模块（`src/rag/industry_knowledge_base.py`）

```python
# 伪代码结构
class IndustryKnowledgeBase:
    def __init__(self, data_sources: List[str]):
        self.embedding_model = load_embedding_model()
        self.vector_store = MilvusCollection("digital_transformation")

    def load_documents(self, pdf_paths: List[str]) -> int:
        """加载并索引行业报告"""

    def retrieve(self, query: str, top_k: int = 5) -> List[Document]:
        """基于语义检索相关片段"""
```

### 3.4 工作流定义（LangGraph）

```
states:
  - company_info: 企业基础信息
  - maturity_assessment: 成熟度评估结果
  - opportunities: 机会清单
  - roadmap: 路线图
  - roi_model: ROI 测算

nodes:
  - collect_company_info: 收集企业信息
  - assess_maturity: 评估数字化成熟度
  - search_opportunities: 检索行业机会
  - rank_opportunities: 优先级排序
  - generate_roadmap: 生成路线图
  - calculate_roi: 计算 ROI
  - human_review: 人工审核（HITL）

edges:
  - collect_company_info -> assess_maturity
  - assess_maturity -> search_opportunities
  - search_opportunities -> rank_opportunities
  - rank_opportunities -> generate_roadmap
  - generate_roadmap -> calculate_roi
  - calculate_roi -> human_review
  - human_review: approve -> END
  - human_review: reject -> collect_company_info
```

---

## 4. 测试计划

### 4.1 测试用例

| 用例 ID | 场景描述 | 输入 | 预期输出 | 验证指标 |
|:---|:---|:---|:---|:---|
| TC-01 | 基础报告生成 | 制造业中型企业，年营收 10 亿 | 完整战略报告 | 覆盖率≥85% |
| TC-02 | 高成熟度企业 | 已有 SAP+MES，需优化 | 聚焦改进建议 | 建议数≥5 |
| TC-03 | 低成熟度企业 | 数字化刚起步 | 渐进式路线图 | Quick Win 占比≥30% |
| TC-04 | 特定行业聚焦 | 电子制造业 | 行业特定机会 | 包含行业关键词 |
| TC-05 | 约束条件输入 | 预算有限 | 性价比优先建议 | ROI 排序合理 |

### 4.2 验证环境

| 环境 | 配置 | 用途 |
|:---|:---|:---|
| 本地开发 | MacBook M2 + 16GB | 日常开发调试 |
| PoC 验证 | Claude Code + 本地 Milvus | 功能验证 |
| 压力测试 | 高频调用场景 | Token 消耗评估 |

### 4.3 评估方法

1. **自动化评估**：比对输出结构与标准模板的覆盖率
2. **人工评审**：组织 2-3 名业务专家打分
3. **对比基准**：与咨询公司同类报告对比（脱敏后）

---

## 5. 已知限制与风险

| 风险 | 严重程度 | 缓解措施 |
|:---|:---|:---|
| 公开数据质量参差 | 中 | 人工筛选高可信度来源，标注置信度 |
| LLM 生成幻觉 | 高 | 强制引用来源，HITL 审核关键建议 |
| Token 消耗不可控 | 低 | 设置单次调用上限，缓存检索结果 |
| 缺乏企业内部数据 | 中 | PoC 阶段仅用公开数据，正式版可接入客户数据 |

---

## 6. 后续 Agent 承接关系

| 下游 Agent | 依赖接口 |
|:---|:---|
| 精益优化 Agent | 接收 `opportunities` 列表，聚焦流程优化机会 |
| 系统集成 Agent | 接收 `roadmap` 中的技术实施节点 |
| 数据洞察 Agent | 接收 `maturity_assessment` 中的数据能力缺口 |
| 变革赋能 Agent | 接收 `roadmap` 中的培训与变革里程碑 |

---

## 7. 下一步行动

- [ ] 搭建本地 Milvus + LangChain 环境
- [ ] 准备 PoC 数据集（3-5 份行业报告）
- [ ] 实现 Agent-01 核心代码
- [ ] 执行 TC-01 ~ TC-05 测试
- [ ] 汇总 PoC-01 验证结论

---

*本文档为 PoC-01 阶段技术验证设计，后续 Agent 文档结构保持一致。*