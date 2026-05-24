import pytest
from unittest.mock import MagicMock
from src.agents.strategic_planning_agent import (
    StrategicPlanningAgent,
    CompanyInfo,
    MaturityAssessment,
    Opportunity,
)


class TestStrategicPlanningAgent:
    """战略规划 Agent 单元测试"""

    def test_initialization(self, mock_llm_client):
        """测试 Agent 初始化"""
        agent = StrategicPlanningAgent(llm_client=mock_llm_client)
        assert agent.llm is not None
        assert agent.system_prompt is not None

    def test_assess_maturity(self, mock_llm_client):
        """测试成熟度评估"""
        agent = StrategicPlanningAgent(llm_client=mock_llm_client)

        company_info = CompanyInfo(
            industry="制造业",
            scale="中型",
            existing_systems=["ERP"],
        )

        maturity = agent.assess_maturity(company_info)

        assert isinstance(maturity, MaturityAssessment)
        assert 1 <= maturity.strategy_score <= 5

    def test_identify_opportunities(self, mock_llm_client):
        """测试机会识别"""
        agent = StrategicPlanningAgent(llm_client=mock_llm_client)

        maturity = MaturityAssessment(
            strategy_score=3,
            technology_score=2,
            process_score=2,
            data_score=3,
            organization_score=2,
            overall_score=2.4,
            strengths=["基础ERP"],
            improvements=["数据分析能力不足", "设备联网率低"],
        )

        opportunities = agent.identify_opportunities(maturity, "制造业")

        assert isinstance(opportunities, list)

    def test_generate_full_plan(self, mock_llm_client, sample_company_info):
        """测试完整规划生成"""
        agent = StrategicPlanningAgent(llm_client=mock_llm_client)

        plan = agent.generate_full_plan(sample_company_info)

        assert plan.company_info == sample_company_info
        assert plan.maturity_assessment is not None
        assert plan.opportunities is not None