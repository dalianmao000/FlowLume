"""
战略规划 Agent 的 LangGraph 状态机工作流
"""

from typing import Optional, List
from dataclasses import dataclass, field
from langgraph.graph import StateGraph, END

from src.agents.strategic_planning_agent import (
    CompanyInfo,
    StrategicPlanningAgent,
    MaturityAssessment,
    Opportunity,
    RoadmapItem,
)


@dataclass
class StrategicWorkflowState:
    """工作流状态"""
    company_info: Optional[CompanyInfo] = None
    maturity_assessment: Optional[MaturityAssessment] = None
    opportunities: List[Opportunity] = field(default_factory=list)
    roadmap: List[RoadmapItem] = field(default_factory=list)
    roi_estimate: dict = field(default_factory=dict)
    human_feedback: Optional[str] = None
    approved: bool = False
    final_report: Optional[str] = None


def create_strategic_workflow(
    agent: Optional[StrategicPlanningAgent] = None,
) -> StateGraph:
    """创建战略规划工作流"""

    agent = agent or StrategicPlanningAgent()

    def collect_company_info_node(state: StrategicWorkflowState) -> StrategicWorkflowState:
        """收集企业信息（初始化节点）"""
        # 如果已有 company_info，直接使用
        if state.company_info is None:
            # 使用默认值进行 PoC
            state.company_info = CompanyInfo(
                industry="制造业",
                scale="中型企业（年营收 10-50 亿）",
                existing_systems=["ERP（用友/金蝶）", "部分手工报表"],
                business_goals=["提升 OEE", "降低库存", "质量追溯"],
                constraints="预算有限，需 Quick Win",
            )
        return state

    def assess_maturity_node(state: StrategicWorkflowState) -> StrategicWorkflowState:
        """评估数字化成熟度"""
        if state.company_info is None:
            raise ValueError("company_info is required")

        state.maturity_assessment = agent.assess_maturity(state.company_info)
        return state

    def identify_opportunities_node(state: StrategicWorkflowState) -> StrategicWorkflowState:
        """识别数字化机会"""
        if state.maturity_assessment is None:
            raise ValueError("maturity_assessment is required")

        state.opportunities = agent.identify_opportunities(
            state.maturity_assessment,
            state.company_info.industry,
        )
        return state

    def generate_roadmap_node(state: StrategicWorkflowState) -> StrategicWorkflowState:
        """生成路线图"""
        if not state.opportunities:
            raise ValueError("opportunities is required")

        state.roadmap = agent.generate_roadmap(state.opportunities, state.company_info)
        return state

    def estimate_roi_node(state: StrategicWorkflowState) -> StrategicWorkflowState:
        """测算 ROI"""
        if not state.roadmap:
            raise ValueError("roadmap is required")

        state.roi_estimate = agent.estimate_roi(state.roadmap, state.company_info)
        return state

    def human_review_node(state: StrategicWorkflowState) -> StrategicWorkflowState:
        """人工审核节点（HITL）"""
        # 简化实现：自动批准
        # 实际生产应接入人工审批流程
        state.approved = True
        return state

    def compile_report_node(state: StrategicWorkflowState) -> StrategicWorkflowState:
        """汇编最终报告"""
        report_parts = []

        # 成熟度评估
        if state.maturity_assessment:
            ma = state.maturity_assessment
            report_parts.append(f"""## 数字化成熟度评估

| 维度 | 评分 |
|:---|:---|
| 战略 | {ma.strategy_score}/5 |
| 技术 | {ma.technology_score}/5 |
| 流程 | {ma.process_score}/5 |
| 数据 | {ma.data_score}/5 |
| 组织 | {ma.organization_score}/5 |

**总体评分：{ma.overall_score}/5**
""")

        # 机会清单
        if state.opportunities:
            op_table = "\n".join([
                f"| {op.name} | {op.domain} | {op.impact} | {op.effort} |"
                for op in state.opportunities
            ])
            report_parts.append(f"""## 优先机会

| 机会 | 领域 | Impact | Effort |
|:---|:---|:---|:---|
{op_table}
""")

        # 路线图
        if state.roadmap:
            rm_items = "\n".join([
                f"- **{item.name}**: {item.start_quarter} ~ {item.end_quarter}"
                for item in state.roadmap
            ])
            report_parts.append(f"""## 3年路线图

{rm_items}
""")

        # ROI 估算
        if state.roi_estimate:
            report_parts.append(f"""## ROI 测算

- ROI: {state.roi_estimate.get('roi', 'N/A')}
- 回收期: {state.roi_estimate.get('payback_period', 'N/A')}
""")

        state.final_report = "\n\n".join(report_parts)
        return state

    # 构建状态图
    workflow = StateGraph(StrategicWorkflowState)

    # 添加节点
    workflow.add_node("collect_company_info", collect_company_info_node)
    workflow.add_node("assess_maturity", assess_maturity_node)
    workflow.add_node("identify_opportunities", identify_opportunities_node)
    workflow.add_node("generate_roadmap", generate_roadmap_node)
    workflow.add_node("estimate_roi", estimate_roi_node)
    workflow.add_node("human_review", human_review_node)
    workflow.add_node("compile_report", compile_report_node)

    # 设置边
    workflow.set_entry_point("collect_company_info")

    workflow.add_edge("collect_company_info", "assess_maturity")
    workflow.add_edge("assess_maturity", "identify_opportunities")
    workflow.add_edge("identify_opportunities", "generate_roadmap")
    workflow.add_edge("generate_roadmap", "estimate_roi")
    workflow.add_edge("estimate_roi", "human_review")
    workflow.add_edge("human_review", "compile_report")
    workflow.add_edge("compile_report", END)

    return workflow.compile()


def run_workflow(company_info: Optional[CompanyInfo] = None) -> StrategicWorkflowState:
    """运行工作流并返回最终状态"""
    workflow = create_strategic_workflow()

    initial_state = StrategicWorkflowState(company_info=company_info)
    final_state = workflow.invoke(initial_state)

    return final_state