"""
变革赋能 Agent 的 LangGraph 状态机工作流
"""
from typing import Optional, List
from dataclasses import dataclass, field
from langgraph.graph import StateGraph, END

from src.agents.change_enablement.change_enablement_agent import (
    ChangeEnablementAgent,
    UserProfile,
    SkillLevel,
    LearningPath,
    GuideResponse,
    QuizResult,
    EmotionTag,
)


@dataclass
class ChangeWorkflowState:
    """工作流状态"""
    user_id: Optional[str] = None
    user_profile: Optional[UserProfile] = None
    skill_level: Optional[SkillLevel] = None
    learning_path: Optional[LearningPath] = None
    current_module: Optional[str] = None
    current_step: int = 0
    quiz_result: Optional[QuizResult] = None
    emotion_result: Optional[str] = None  # emotion tag as string
    adoption_score: float = 0.0
    completed_modules: List[str] = field(default_factory=list)
    final_report: Optional[str] = None


def create_change_workflow(
    agent: Optional[ChangeEnablementAgent] = None,
) -> StateGraph:
    """创建变革赋能工作流"""

    agent = agent or ChangeEnablementAgent()

    def identify_user_node(state: ChangeWorkflowState) -> ChangeWorkflowState:
        """识别用户身份（初始化节点）"""
        if state.user_id is None:
            state.user_id = "default_user"
        # 获取用户画像
        state.user_profile = agent.identify_user(state.user_id, "操作员")
        return state

    def assess_skill_node(state: ChangeWorkflowState) -> ChangeWorkflowState:
        """评估技能水平"""
        if state.user_profile is None:
            raise ValueError("user_profile is required")

        task = state.current_module or "MES报工"
        state.skill_level = agent.assess_skill_level(
            state.user_id,
            state.user_profile.role.value,
            task
        )
        return state

    def generate_path_node(state: ChangeWorkflowState) -> ChangeWorkflowState:
        """生成学习路径"""
        if state.user_profile is None or state.skill_level is None:
            raise ValueError("user_profile and skill_level are required")

        state.learning_path = agent.generate_learning_path(
            state.user_id,
            state.user_profile.role,
            state.skill_level,
            state.current_module or "MES报工"
        )
        return state

    def deliver_content_node(state: ChangeWorkflowState) -> ChangeWorkflowState:
        """推送微课内容"""
        # 推送当前模块的学习内容（简化实现）
        if state.learning_path and state.learning_path.modules:
            first_module = state.learning_path.modules[0]
            state.current_module = first_module["module_id"]
        return state

    def guide_operation_node(state: ChangeWorkflowState) -> ChangeWorkflowState:
        """对话式操作指导"""
        if state.user_id is None:
            raise ValueError("user_id is required")

        guide = agent.guide_operation(
            state.user_id,
            state.current_module or "MES报工",
            state.current_step + 1
        )
        state.current_step += 1
        return state

    def detect_emotion_node(state: ChangeWorkflowState) -> ChangeWorkflowState:
        """检测用户情绪（条件分支）"""
        # 简化：如果用户输入包含负面情绪关键词
        # 实际生产应接入真实用户输入
        state.emotion_result = "neutral"
        return state

    def conduct_quiz_node(state: ChangeWorkflowState) -> ChangeWorkflowState:
        """随堂测验"""
        if state.current_module is None:
            raise ValueError("current_module is required")

        state.quiz_result = agent.conduct_quiz(state.user_id, state.current_module)
        return state

    def track_progress_node(state: ChangeWorkflowState) -> ChangeWorkflowState:
        """记录学习进度"""
        if state.current_module and state.quiz_result:
            if state.quiz_result.score >= 0.7:
                state.completed_modules.append(state.current_module)
                agent.track_progress(state.user_id, state.current_module, True)

        state.adoption_score = agent.tracker.get_adoption_score(state.user_id or "default_user")
        return state

    def compile_report_node(state: ChangeWorkflowState) -> ChangeWorkflowState:
        """汇编最终报告"""
        modules_summary = "\n".join([
            f"- {m}" for m in state.completed_modules
        ]) if state.completed_modules else "无"

        state.final_report = f"""## 变革赋能学习报告

### 用户信息
- 用户ID：{state.user_id}
- 角色：{state.user_profile.role.value if state.user_profile else "未知"}
- 技能水平：{state.skill_level.value if state.skill_level else "未知"}

### 完成模块
{modules_summary}

### Adoption 分数
{state.adoption_score:.1f}/100

### 测验结果
- 模块：{state.quiz_result.module_id if state.quiz_result else "无"}
- 得分：{state.quiz_result.score * 100:.0f}% if state.quiz_result else "无"

### 建议
继续保持学习进度，完成更多模块可提升 Adoption 分数。
"""
        return state

    # 构建状态图
    workflow = StateGraph(ChangeWorkflowState)

    # 添加节点
    workflow.add_node("identify_user", identify_user_node)
    workflow.add_node("assess_skill", assess_skill_node)
    workflow.add_node("generate_path", generate_path_node)
    workflow.add_node("deliver_content", deliver_content_node)
    workflow.add_node("guide_operation", guide_operation_node)
    workflow.add_node("detect_emotion", detect_emotion_node)
    workflow.add_node("conduct_quiz", conduct_quiz_node)
    workflow.add_node("track_progress", track_progress_node)
    workflow.add_node("compile_report", compile_report_node)

    # 设置边
    workflow.set_entry_point("identify_user")

    workflow.add_edge("identify_user", "assess_skill")
    workflow.add_edge("assess_skill", "generate_path")
    workflow.add_edge("generate_path", "deliver_content")
    workflow.add_edge("deliver_content", "guide_operation")
    workflow.add_edge("guide_operation", "detect_emotion")

    # 情绪检测后的条件分支（简化实现）
    workflow.add_edge("detect_emotion", "conduct_quiz")
    workflow.add_edge("conduct_quiz", "track_progress")
    workflow.add_edge("track_progress", "compile_report")
    workflow.add_edge("compile_report", END)

    return workflow.compile()


def run_change_workflow(
    user_id: Optional[str] = None,
    current_module: Optional[str] = None,
) -> ChangeWorkflowState:
    """运行变革赋能工作流"""
    workflow = create_change_workflow()

    initial_state = ChangeWorkflowState(
        user_id=user_id,
        current_module=current_module,
    )
    final_state = workflow.invoke(initial_state)

    return final_state