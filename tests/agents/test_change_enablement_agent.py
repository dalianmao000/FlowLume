import pytest
from unittest.mock import MagicMock
from src.agents.change_enablement.change_enablement_agent import (
    ChangeEnablementAgent,
    SkillLevel,
    UserRole,
    UserProfile,
)


class TestChangeEnablementAgent:
    """ChangeEnablementAgent 单元测试"""

    @pytest.fixture
    def mock_llm(self):
        """Mock LLM client"""
        client = MagicMock()
        client.generate.return_value = "测试回复"
        return client

    @pytest.fixture
    def agent(self, mock_llm):
        """Agent instance with mock LLM"""
        from src.tracking.user_behavior_tracker import UserBehaviorTracker
        import tempfile, os
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        tracker = UserBehaviorTracker(db_path=path)
        return ChangeEnablementAgent(
            llm_client=mock_llm,
            tracker=tracker
        )

    def test_initialization(self, agent):
        """测试 Agent 初始化"""
        assert agent.llm is not None
        assert agent.tracker is not None
        assert agent.emotion_detector is not None

    def test_identify_user(self, agent):
        """测试用户识别"""
        profile = agent.identify_user("user-001", "操作员")
        assert isinstance(profile, UserProfile)
        assert profile.user_id == "user-001"
        assert profile.role == UserRole.OPERATOR

    def test_assess_skill_level(self, agent, mock_llm):
        """测试技能水平评估"""
        mock_llm.generate.return_value = "用户表示熟悉系统操作" * 50

        skill_level = agent.assess_skill_level(
            "user-001",
            "操作员",
            "MES报工"
        )
        assert isinstance(skill_level, SkillLevel)

    def test_generate_learning_path(self, agent):
        """测试学习路径生成"""
        profile = UserProfile(
            user_id="user-001",
            role=UserRole.OPERATOR,
            skill_level=SkillLevel.BEGINNER,
            current_task="MES报工"
        )
        path = agent.generate_learning_path(
            "user-001",
            UserRole.OPERATOR,
            SkillLevel.BEGINNER,
            "MES报工"
        )
        assert len(path.modules) == 3