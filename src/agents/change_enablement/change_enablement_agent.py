"""
变革赋能 Agent - 数字化转型培训专家
"""
from typing import Optional, List, Dict
from dataclasses import dataclass, field
from enum import Enum

from src.llm.claude_client import ClaudeClient
from src.rag.retriever import Retriever
from src.tracking.user_behavior_tracker import UserBehaviorTracker, LearningEvent
from src.agents.emotion_detector import EmotionDetector, EmotionResult, EmotionTag
from src.prompts.change_enablement import (
    SYSTEM_PROMPT,
    SKILL_ASSESSMENT_TEMPLATE,
    LEARNING_PATH_TEMPLATE,
    OPERATION_GUIDE_TEMPLATE,
    QUIZ_TEMPLATE,
    EMOTION_RESPONSE_TEMPLATE,
)


class SkillLevel(Enum):
    """技能水平"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    EXPERT = "expert"


class UserRole(Enum):
    """用户角色"""
    OPERATOR = "operator"        # 操作员
    SUPERVISOR = "supervisor"     # 班组长
    TECHNICIAN = "technician"     # 维修工程师
    MANAGER = "manager"           # 管理人员


@dataclass
class UserProfile:
    """用户画像"""
    user_id: str
    role: UserRole
    skill_level: SkillLevel
    current_task: str
    learning_history: List[str] = field(default_factory=list)


@dataclass
class LearningPath:
    """学习路径"""
    user_id: str
    modules: List[Dict]  # [{module_id, name, duration, difficulty}]
    recommendations: str


@dataclass
class GuideResponse:
    """操作指导响应"""
    step_number: int
    instruction: str
    confirmation_needed: bool
    next_hint: Optional[str] = None


@dataclass
class QuizResult:
    """测验结果"""
    module_id: str
    score: float  # 0.0 - 1.0
    correct_answers: int
    total_questions: int
    feedback: str


class ChangeEnablementAgent:
    """变革赋能 Agent"""

    def __init__(
        self,
        llm_client: Optional[ClaudeClient] = None,
        retriever: Optional[Retriever] = None,
        tracker: Optional[UserBehaviorTracker] = None,
        db_path: str = "data/adoption.db",
    ):
        self.llm = llm_client or ClaudeClient()
        self.retriever = retriever
        self.tracker = tracker or UserBehaviorTracker(db_path=db_path)
        self.emotion_detector = EmotionDetector()
        self.system_prompt = SYSTEM_PROMPT

    def identify_user(self, user_id: str, role: str) -> UserProfile:
        """识别用户身份和角色"""
        # 角色映射
        role_map = {
            "操作员": UserRole.OPERATOR,
            "班组长": UserRole.SUPERVISOR,
            "维修工程师": UserRole.TECHNICIAN,
            "管理员": UserRole.MANAGER,
        }
        user_role = role_map.get(role, UserRole.OPERATOR)

        # 获取历史学习进度
        progress = self.tracker.get_user_progress(user_id)
        modules_completed = []
        if progress:
            import json
            modules_completed = json.loads(progress.get("modules_completed", "[]"))

        return UserProfile(
            user_id=user_id,
            role=user_role,
            skill_level=SkillLevel.INTERMEDIATE,  # 默认中级
            current_task="",
            learning_history=modules_completed,
        )

    def assess_skill_level(self, user_id: str, role: str, task: str) -> SkillLevel:
        """评估用户技能水平"""
        # 生成评估问题
        prompt = SKILL_ASSESSMENT_TEMPLATE.format(
            role=role,
            task=task,
            skill_level="待评估"
        )

        # 如果有 RAG 检索器，获取相关 SOP 作为上下文
        context = ""
        if self.retriever:
            docs = self.retriever.retrieve(f"{task} 操作指南", top_k=3)
            context = "\n\n".join([d["content"][:500] for d in docs])

        full_prompt = f"{prompt}\n\n相关操作参考：\n{context}"

        response = self.llm.generate(self.system_prompt, full_prompt)

        # 记录评估事件
        self._record_event(user_id, "skill_assessment", task, {"task": task})

        # 简化：基于回答长度和关键词判断技能水平
        if len(response) > 500 or "熟悉" in response or "经验" in response:
            return SkillLevel.INTERMEDIATE
        return SkillLevel.BEGINNER

    def generate_learning_path(
        self,
        user_id: str,
        role: UserRole,
        skill_level: SkillLevel,
        task: str,
    ) -> LearningPath:
        """生成个性化学习路径"""
        # 获取 SOP 知识库内容
        sop_context = ""
        if self.retriever:
            docs = self.retriever.retrieve(f"{task} 学习路径", top_k=5)
            sop_context = "\n\n".join([f"- {d['content'][:300]}" for d in docs])

        prompt = LEARNING_PATH_TEMPLATE.format(
            role=role.value,
            skill_level=skill_level.value,
            module_1=f"{task}基础操作",
            duration_1="15分钟",
            difficulty_1="基础",
            module_2=f"{task}进阶功能",
            duration_2="20分钟",
            difficulty_2="进阶",
            module_3=f"{task}高级技巧",
            duration_3="25分钟",
            difficulty_3="高级",
            learning_suggestion="建议按照顺序学习，完成后进行测验"
        )

        full_prompt = f"{prompt}\n\nSOP 知识库：\n{sop_context}"

        response = self.llm.generate(self.system_prompt, full_prompt)

        # 记录学习路径生成事件
        self._record_event(user_id, "learning_path_generated", task, {
            "role": role.value,
            "skill_level": skill_level.value,
            "task": task
        })

        modules = [
            {"module_id": f"{task}_basic", "name": f"{task}基础操作", "duration": "15分钟", "difficulty": "基础"},
            {"module_id": f"{task}_intermediate", "name": f"{task}进阶功能", "duration": "20分钟", "difficulty": "进阶"},
            {"module_id": f"{task}_advanced", "name": f"{task}高级技巧", "duration": "25分钟", "difficulty": "高级"},
        ]

        return LearningPath(
            user_id=user_id,
            modules=modules,
            recommendations="建议按顺序学习"
        )

    def guide_operation(
        self,
        user_id: str,
        task: str,
        step: int,
    ) -> GuideResponse:
        """对话式操作指导"""
        # 获取当前步骤的 SOP
        context = ""
        if self.retriever:
            docs = self.retriever.retrieve(f"{task} 步骤{step}", top_k=3)
            context = "\n\n".join([d["content"][:500] for d in docs])

        prompt = OPERATION_GUIDE_TEMPLATE.format(
            operation_name=f"{task} - 步骤 {step}",
            step_1_title="准备阶段",
            step_1_description="进入系统并选择正确的工单",
            step_2_title="执行阶段",
            step_2_description=f"按照提示完成{task}操作",
            step_3_title="确认阶段",
            step_3_description="核对结果并提交"
        )

        full_prompt = f"{prompt}\n\n参考内容：\n{context}"

        response = self.llm.generate(self.system_prompt, full_prompt)

        return GuideResponse(
            step_number=step,
            instruction=response,
            confirmation_needed=True,
            next_hint="请确认您已完成当前步骤"
        )

    def conduct_quiz(self, user_id: str, module_id: str) -> QuizResult:
        """随堂测验"""
        prompt = QUIZ_TEMPLATE.format(
            module_name=module_id,
            question_1=f"{module_id}的第一个关键步骤是什么？",
            option_1_a="正确操作",
            option_1_b="错误操作",
            option_1_c="不确定",
            question_2="为什么要这样操作？",
            option_2_a="为了数据准确",
            option_2_b="不知道"
        )

        response = self.llm.generate(self.system_prompt, prompt)

        # 记录测验事件
        self._record_event(user_id, "quiz", module_id, {"module_id": module_id})

        # 简化评估：实际应该解析用户回答
        return QuizResult(
            module_id=module_id,
            score=0.85,  # 简化值
            correct_answers=2,
            total_questions=3,
            feedback="掌握良好，继续加油！"
        )

    def detect_and_respond_to_emotion(
        self,
        user_id: str,
        user_input: str,
    ) -> tuple[EmotionResult, str]:
        """检测情绪并生成响应"""
        emotion_result = self.emotion_detector.detect(user_input)

        # 记录情绪检测事件
        self._record_event(user_id, "emotion_detected", "general", {
            "emotion": emotion_result.tag.value,
            "confidence": emotion_result.confidence
        })

        # 如果是负面情绪，生成安抚回复
        if emotion_result.tag in [EmotionTag.FRUSTRATED, EmotionTag.RESISTANT, EmotionTag.CONFUSED]:
            response = EMOTION_RESPONSE_TEMPLATE.format(
                sense_response="我理解您的感觉",
                empathetic_message="别担心，我们会一起慢慢来。",
                alternative_explanation="让我用更简单的方式解释..."
            )
        else:
            response = emotion_result.suggested_response

        return emotion_result, response

    def track_progress(self, user_id: str, module_id: str, completed: bool) -> None:
        """追踪学习进度"""
        if completed:
            self._record_event(user_id, "complete", module_id, {"completed": True})

    def _record_event(
        self,
        user_id: str,
        event_type: str,
        module_id: str,
        metadata: Optional[dict] = None
    ) -> None:
        """记录学习事件的内部方法"""
        from datetime import datetime
        import uuid

        event = LearningEvent(
            event_id=str(uuid.uuid4()),
            user_id=user_id,
            event_type=event_type,
            module_id=module_id,
            timestamp=datetime.now().isoformat(),
            metadata=metadata
        )
        self.tracker.record_learning_event(event)