from typing import List, Optional, TYPE_CHECKING
from dataclasses import dataclass

from src.llm.claude_client import ClaudeClient
from src.prompts.strategic_planning import (
    SYSTEM_PROMPT,
    MATURITY_ASSESSMENT_TEMPLATE,
    OPPORTUNITY_IDENTIFICATION_TEMPLATE,
    ROADMAP_GENERATION_TEMPLATE,
    ROI_ESTIMATION_TEMPLATE,
)

if TYPE_CHECKING:
    from src.rag.retriever import Retriever


@dataclass
class CompanyInfo:
    """企业基础信息"""
    industry: str
    scale: str
    existing_systems: List[str]
    business_goals: Optional[List[str]] = None
    constraints: Optional[str] = None


@dataclass
class MaturityAssessment:
    """数字化成熟度评估结果"""
    strategy_score: int
    technology_score: int
    process_score: int
    data_score: int
    organization_score: int
    overall_score: float
    strengths: List[str]
    improvements: List[str]


@dataclass
class Opportunity:
    """数字化机会点"""
    name: str
    domain: str
    impact: int
    effort: int
    roi_estimate: str
    priority: str
    conditions: str
    risks: str


@dataclass
class RoadmapItem:
    """路线图节点"""
    name: str
    start_quarter: str
    end_quarter: str
    year: int
    deliverables: List[str]
    owner: str


@dataclass
class StrategicPlan:
    """完整战略规划报告"""
    company_info: CompanyInfo
    maturity_assessment: MaturityAssessment
    opportunities: List[Opportunity]
    roadmap: List[RoadmapItem]
    roi_estimate: dict


class StrategicPlanningAgent:
    """战略规划 Agent"""

    def __init__(
        self,
        llm_client: Optional[ClaudeClient] = None,
        retriever: Optional["Retriever"] = None,
    ):
        self.llm = llm_client or ClaudeClient()
        self.retriever = retriever
        self.system_prompt = SYSTEM_PROMPT

    def assess_maturity(self, company_info: CompanyInfo) -> MaturityAssessment:
        """评估数字化成熟度"""
        # 检索相关行业基准
        industry_context = ""
        if self.retriever:
            docs = self.retriever.retrieve(
                f"{company_info.industry} 数字化转型成熟度",
                top_k=3
            )
            industry_context = "\n\n".join([d["content"][:500] for d in docs])

        # 构建 prompt
        prompt = f"""
{MATURITY_ASSESSMENT_TEMPLATE.format(
    industry=company_info.industry,
    scale=company_info.scale,
    existing_systems=", ".join(company_info.existing_systems)
)}

参考行业最佳实践：
{industry_context}

请生成五维成熟度评分。
"""

        response = self.llm.generate(self.system_prompt, prompt)

        # 解析评分（简化实现）
        return self._parse_maturity_response(response)

    def identify_opportunities(
        self,
        maturity: MaturityAssessment,
        industry: str,
    ) -> List[Opportunity]:
        """识别数字化机会"""
        industry_context = ""
        if self.retriever:
            docs = self.retriever.retrieve(
                f"{industry} 数字化转型 机会 最佳实践",
                top_k=5
            )
            industry_context = "\n\n".join([f"- {d['content'][:300]}" for d in docs])

        prompt = f"""
{OPPORTUNITY_IDENTIFICATION_TEMPLATE.format(priority="High")}

参考行业实践：
{industry_context}

基于以下成熟度评估结果，识别优先机会：
- 待改善领域：{maturity.improvements}
- 行业：{industry}
"""

        response = self.llm.generate(self.system_prompt, prompt)

        return self._parse_opportunities_response(response)

    def generate_roadmap(
        self,
        opportunities: List[Opportunity],
        company_info: CompanyInfo,
    ) -> List[RoadmapItem]:
        """生成转型路线图"""
        op_list = "\n".join([
            f"- {op.name} (Impact={op.impact}, Effort={op.effort})"
            for op in opportunities
        ])

        prompt = f"""
{ROADMAP_GENERATION_TEMPLATE}

优先机会清单：
{op_list}

企业约束：{company_info.constraints or "无特殊约束"}
"""

        response = self.llm.generate(self.system_prompt, prompt)

        return self._parse_roadmap_response(response)

    def estimate_roi(
        self,
        roadmap: List[RoadmapItem],
        company_info: CompanyInfo,
    ) -> dict:
        """初步 ROI 测算"""
        roadmap_summary = "\n".join([
            f"- {item.name}: {item.start_quarter} ~ {item.end_quarter}"
            for item in roadmap
        ])

        prompt = f"""
{ROI_ESTIMATION_TEMPLATE}

路线图概要：
{roadmap_summary}

企业规模：{company_info.scale}
"""

        response = self.llm.generate(self.system_prompt, prompt)

        return self._parse_roi_response(response)

    def generate_full_plan(self, company_info: CompanyInfo) -> StrategicPlan:
        """生成完整战略规划"""
        # 1. 评估成熟度
        maturity = self.assess_maturity(company_info)

        # 2. 识别机会
        opportunities = self.identify_opportunities(maturity, company_info.industry)

        # 3. 生成路线图
        roadmap = self.generate_roadmap(opportunities, company_info)

        # 4. 测算 ROI
        roi_estimate = self.estimate_roi(roadmap, company_info)

        return StrategicPlan(
            company_info=company_info,
            maturity_assessment=maturity,
            opportunities=opportunities,
            roadmap=roadmap,
            roi_estimate=roi_estimate,
        )

    # 以下为解析方法（简化实现，实际生产应使用结构化输出）
    def _parse_maturity_response(self, response: str) -> MaturityAssessment:
        """解析 LLM 返回的成熟度评估"""
        # 简化实现：从文本中提取评分
        import re
        scores = {}
        for dim in ["strategy", "technology", "process", "data", "organization"]:
            match = re.search(rf"{dim}[^0-9]*(\d)", response, re.IGNORECASE)
            if match:
                scores[dim] = int(match.group(1))

        return MaturityAssessment(
            strategy_score=scores.get("strategy", 3),
            technology_score=scores.get("technology", 3),
            process_score=scores.get("process", 3),
            data_score=scores.get("data", 3),
            organization_score=scores.get("organization", 3),
            overall_score=sum(scores.values()) / len(scores) if scores else 3.0,
            strengths=["待补充"],
            improvements=["待补充"],
        )

    def _parse_opportunities_response(self, response: str) -> List[Opportunity]:
        """解析机会列表"""
        return [
            Opportunity(
                name="待识别",
                domain="待确认",
                impact=3,
                effort=3,
                roi_estimate="待测算",
                priority="Medium",
                conditions="待确认",
                risks="待确认",
            )
        ]

    def _parse_roadmap_response(self, response: str) -> List[RoadmapItem]:
        """解析路线图"""
        return [
            RoadmapItem(
                name="待规划",
                start_quarter="Q1",
                end_quarter="Q4",
                year=2026,
                deliverables=[],
                owner="待定",
            )
        ]

    def _parse_roi_response(self, response: str) -> dict:
        """解析 ROI 测算"""
        return {"roi": "待测算", "payback_period": "待测算"}