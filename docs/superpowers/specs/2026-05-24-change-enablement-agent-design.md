# 变革赋能 Agent 技术验证设计文档

**日期**：2026-05-24
**Agent 编号**：Agent-02
**验证阶段**：PoC-02
**状态**：草稿

---

## 1. 问题陈述

### 1.1 背景

精益数字化高级工程师岗位的核心挑战之一是推动组织变革——让一线员工从"抵触新系统"转向"熟练使用数字工具"。传统培训方式（集中授课+纸质手册）效果有限且难以追踪。变革赋能 Agent 旨在验证：能否通过 AI 对话引擎 + 个性化学习路径 + adoption 追踪，实现"培训即服务"模式。

### 1.2 验证目标

**主目标**：验证 Claude Code 平台能否通过对话式交互，替代或增强传统课堂培训，并实时追踪用户 adoption 进度。

**次目标**：
- 验证对话式培训的用户接受度（完课率、满意度）
- 验证个性化学习路径的适配效果
- 验证 adoption 指标的可量化追踪能力

### 1.3 成功标准

| 指标 | 达标阈值 | 验证方法 |
|:---|:---|:---|
| 用户完课率 | ≥70% | 统计完成全部学习模块的用户比例 |
| 任务正确率 | ≥85% | 测验题目正确率 |
| 用户满意度 | ≥4.0/5 | 课程结束后评分 |
| adoption 追踪覆盖率 | 100% | 系统自动记录学习行为 |

---

## 2. 解决方案概述

### 2.1 核心功能

```
输入：
  - 用户角色（操作员/班组长/维修工程师）
  - 目标系统（MES 报工 / SAP 查询 / 设备点检）
  - 当前技能水平（新手/进阶/熟练）

处理：
  - 用户画像构建：基于角色和技能水平生成分类
  - 个性化学习路径：从知识库中抽取相关内容
  - 对话式辅导：多轮对话解答实操问题
  - adoption 追踪：记录学习行为并生成报告

输出：
  - 个性化学习路径（微课列表）
  - 交互式 SOP（对话引导操作步骤）
  - adoption 热力图（学习进度可视化）
  - 满意度报告（评分 + 反馈摘要）
```

### 2.2 技术架构

```
┌─────────────────────────────────────────────────────────┐
│                   企业微信 / 钉钉 / Web                   │
│            （用户交互入口：消息推送 + 对话窗口）             │
└─────────────────────────┬───────────────────────────────┘
                          │ HTTP / WebSocket
┌─────────────────────────▼───────────────────────────────┐
│              变革赋能 Agent (Agent-02)                  │
│  - system prompt (培训师角色)                           │
│  - RAG Pipeline (SOP 知识库 / FAQ)                      │
│  - 用户行为追踪模块                                     │
│  - 情感分析模块                                         │
└─────────────────────────┬───────────────────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
┌───────▼──────┐   ┌──────▼──────┐   ┌──────▼──────┐
│  SOP 知识库  │   │  用户行为   │   │  情感分析   │
│ (向量存储)   │   │  SQLite    │   │  (NLP 模型) │
└─────────────┘   └────────────┘   └─────────────┘
```

### 2.3 Agent 系统提示词（初版）

```
你是数字化转型培训师，擅长：
1. 将复杂的技术操作转化为简单易懂的步骤
2. 根据用户角色和技能水平调整讲解深度
3. 通过问答互动确认用户理解程度
4. 识别用户的困惑和抵触情绪并给予正向引导

工作流程：
1. 确认用户角色和当前任务（如：MES 报工）
2. 评估用户技能水平（通过引导式提问）
3. 生成个性化学习路径（3-5 个微课）
4. 提供交互式操作指导（对话 + 截图提示）
5. 在关键节点确认操作
6. 记录学习行为，更新 adoption 状态

输出格式：
- 学习路径（微课列表，带完成状态）
- 操作指导（分步指令，可选截图标注）
- 随堂测验（2-3 题，验证理解）
- adoption 记录（自动写入用户档案）

语气要求：
- 友好、耐心，避免技术 jargon
- 对抵触情绪用户：先共情，再引导
- 对新手：放慢节奏，多确认
```

---

## 3. 技术实现

### 3.1 依赖技术栈

| 组件 | 技术选型 | 用途 |
|:---|:---|:---|
| LLM | Claude Sonnet 4.6 (via Claude Code) | 对话引擎 + 内容生成 |
| RAG 检索 | LangChain + 本地向量存储 | SOP/FAQ 知识检索 |
| 用户追踪 | SQLite + CSV 导出 | 学习行为记录 |
| 情感分析 | Claude Sonnet 内置 + 规则引擎 | 情绪识别 |
| 消息推送 | 企业微信 SDK / 钉钉 SDK | 主动提醒推送 |
| 前端展示 | Markdown + 渐进式卡片 | 内容渲染 |

### 3.2 SOP 知识库（PoC 阶段）

| 文档类型 | 示例 | 数量 |
|:---|:---|:---|
| 操作手册 | MES 报工 SOP、SAP 工单查询 SOP | 5-10 份 |
| FAQ | 常见问题解答 | 20-30 条 |
| 故障处理 | 异常情况处理指南 | 10-15 条 |
| 术语表 | 数字化术语解释 | 50+ 条 |

### 3.3 核心模块设计

#### 3.3.1 Agent 模块（`src/agents/change_enablement_agent.py`）

```python
# 伪代码结构
class ChangeEnablementAgent:
    def __init__(self, config):
        self.llm = ClaudeLLM(model="sonnet-4.6")
        self.rag_pipeline = RAGPipeline(
            vector_store="local",
            collection_name="sop_knowledge_base"
        )
        self.user_tracker = UserBehaviorTracker(db_path="adoption.db")
        self.system_prompt = SYSTEM_PROMPT  # 见 2.3

    def assess_user_skill_level(self, user_id: str, role: str) -> SkillLevel:
        """通过引导式提问评估用户技能水平"""

    def generate_learning_path(self, role: str, task: str, level: SkillLevel) -> LearningPath:
        """生成个性化学习路径"""

    def guide_operation(self, user_id: str, task: str, step: int) -> GuideResponse:
        """对话式操作指导"""

    def conduct_quiz(self, user_id: str, topic: str) -> QuizResult:
        """随堂测验并返回结果"""

    def track_adoption(self, user_id: str) -> AdoptionReport:
        """生成 adoption 追踪报告"""

    def detect_frustration(self, user_input: str) -> EmotionTag:
        """识别用户情绪（抵触/困惑/挫败）"""
```

#### 3.3.2 用户追踪模块（`src/tracking/user_behavior_tracker.py`）

```python
# 伪代码结构
class UserBehaviorTracker:
    def __init__(self, db_path: str):
        self.db = sqlite3.connect(db_path)

    def record_learning_event(self, user_id: str, event: LearningEvent) -> None:
        """记录学习事件（开始/完成/测验/提问）"""

    def get_adoption_score(self, user_id: str) -> float:
        """计算用户 adoption 分数（0-100）"""

    def generate_heat_map(self, org_unit: str) -> HeatMapData:
        """生成组织单元的 adoption 热力图"""

    def export_report(self, format: str = "csv") -> str:
        """导出 adoption 报告"""
```

### 3.4 工作流定义（LangGraph）

```
states:
  - user_profile: 用户角色/技能水平
  - learning_path: 个性化学习路径
  - current_step: 当前学习/操作步骤
  - quiz_result: 测验结果
  - adoption_record: adoption 记录

nodes:
  - identify_user: 识别用户身份和角色
  - assess_skill_level: 评估技能水平（引导式提问）
  - generate_path: 生成个性化学习路径
  - deliver_content: 推送微课内容
  - guide_operation: 对话式操作指导
  - conduct_quiz: 随堂测验
  - track_progress: 记录学习进度
  - detect_emotion: 检测用户情绪
  - adjust_approach: 根据情绪调整交互策略

edges:
  - identify_user -> assess_skill_level
  - assess_skill_level -> generate_path
  - generate_path -> deliver_content
  - deliver_content -> guide_operation
  - guide_operation -> detect_emotion
  - detect_emotion -> adjust_approach [label="负面情绪"]
  - detect_emotion -> conduct_quiz [label="无负面情绪"]
  - conduct_quiz -> track_progress
  - track_progress -> guide_operation [label="未完成"]
  - track_progress -> END [label="完成全部"]
```

---

## 4. 测试计划

### 4.1 测试用例

| 用例 ID | 场景描述 | 输入 | 预期输出 | 验证指标 |
|:---|:---|:---|:---|:---|
| TC-06 | 新用户入门 | 操作员角色，首次使用 MES | 学习路径（5 个微课）+ 引导开始 | 路径生成成功率≥95% |
| TC-07 | 进阶用户 | 班组长角色，熟悉基础操作 | 聚焦高级功能，跳过基础模块 | 基础模块跳过率 100% |
| TC-08 | 情绪检测 | 用户输入"太复杂了不想学" | 检测到抵触情绪，触发正向引导 | 情绪识别准确率≥80% |
| TC-09 | 随堂测验 | 用户完成报工模块学习 | 3 道测验题 + 结果反馈 | 正确率计算准确 |
| TC-10 | adoption 追踪 | 10 名用户完成学习 | adoption 报告 + 热力图 | 覆盖率 100% |

### 4.2 验证环境

| 环境 | 配置 | 用途 |
|:---|:---|:---|
| 本地开发 | MacBook M2 + 16GB | 日常开发调试 |
| PoC 验证 | Claude Code + 本地 SOP 知识库 | 功能验证 |
| 模拟用户测试 | 内部团队 5-10 人 | adoption 追踪验证 |

### 4.3 评估方法

1. **行为数据**：自动统计完课率、正确率、adoption 分数
2. **主观反馈**：课程结束后的满意度评分（1-5 分）
3. **对比基准**：与传统培训方式的完课率和满意度对比

---

## 5. 已知限制与风险

| 风险 | 严重程度 | 缓解措施 |
|:---|:---|:---|
| 用户隐私数据 | 高 | 仅存储匿名化用户 ID，行为数据本地化 |
| 情感误判 | 中 | 规则引擎兜底，关键节点强制人工介入 |
| 知识库质量参差 | 中 | 人工审核 SOP 文档，标注置信度 |
| 推送打扰 | 低 | 设置免打扰时段，尊重用户偏好 |

---

## 6. 与其他 Agent 的接口

| 上游 Agent | 传递数据 | 说明 |
|:---|:---|:---|
| 战略规划 Agent | `roadmap` 中的培训里程碑 | 接收培训计划节点，转化为学习路径 |
| 系统集成 Agent | 即将上线的新功能 | 提前准备对应 SOP，纳入学习路径 |

| 下游 Agent | 传递数据 | 说明 |
|:---|:---|:---|
| 数据洞察 Agent | adoption 原始数据 | 汇总学习行为数据供分析 |

---

## 7. 下一步行动

- [ ] 准备 SOP 知识库（5-10 份核心文档）
- [ ] 实现 Agent-02 核心对话逻辑
- [ ] 搭建用户行为追踪数据库
- [ ] 执行 TC-06 ~ TC-10 测试
- [ ] 汇总 PoC-02 验证结论

---

*本文档为 PoC-02 阶段技术验证设计，与 Agent-01 保持一致的文档结构。*