import pytest
from unittest.mock import MagicMock, patch
from src.llm.claude_client import ClaudeClient
from src.agents.strategic_planning_agent import StrategicPlanningAgent, CompanyInfo


@pytest.fixture
def mock_llm_client():
    """Mock LLM 客户端"""
    client = MagicMock(spec=ClaudeClient)
    client.generate.return_value = "模拟 LLM 回复"
    return client


@pytest.fixture
def sample_company_info():
    """示例企业信息"""
    return CompanyInfo(
        industry="制造业",
        scale="中型企业（年营收 10-50 亿）",
        existing_systems=["ERP（用友/金蝶）", "部分手工报表"],
        business_goals=["提升 OEE", "降低库存", "质量追溯"],
        constraints="预算有限，需 Quick Win",
    )