"""
数据洞察 Agent 的 LangGraph 状态机工作流

This workflow orchestrates the entire data insight process:
1. Parse natural language query
2. Generate SQL from query
3. Validate SQL syntax and security
4. Execute SQL and get results
5. Interpret query results
6. Detect anomalies in data
7. Analyze root cause of anomalies
8. Generate complete insight report
9. Human-in-the-loop for high-value/high-risk cases
"""

from typing import Optional, List
from dataclasses import dataclass, field
from langgraph.graph import StateGraph, END

from src.agents.data_insight.data_insight_agent import (
    DataInsightAgent,
    QueryResult,
    RootCauseReport,
    InsightReport,
    SQLQuery,
)
from src.agents.data_insight.anomaly_detector import AnomalyPoint, SeverityLevel
from src.agents.data_insight.text_to_sql import ValidationError


@dataclass
class DataInsightWorkflowState:
    """工作流状态"""
    # Input
    natural_query: Optional[str] = None

    # Intermediate states
    sql_query: Optional[SQLQuery] = None
    query_result: Optional[QueryResult] = None
    interpretation: Optional[str] = None
    anomalies: List[AnomalyPoint] = field(default_factory=list)
    root_causes: List[RootCauseReport] = field(default_factory=list)
    insight_report: Optional[InsightReport] = None

    # Validation and retry
    validation_error: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3

    # Human review
    human_approved: bool = False
    human_feedback: Optional[str] = None

    # High risk threshold
    high_risk_threshold: float = 0.7  # Anomalies with severity >= HIGH are high risk

    # Final output
    final_report: Optional[str] = None
    is_high_risk: bool = False


def create_data_insight_workflow(
    agent: Optional[DataInsightAgent] = None,
) -> StateGraph:
    """创建数据洞察工作流"""

    agent = agent or DataInsightAgent()

    def parse_query_node(state: DataInsightWorkflowState) -> DataInsightWorkflowState:
        """解析自然语言查询（初始化节点）"""
        if state.natural_query is None:
            state.natural_query = "Show OEE trends for the last 7 days"
        # Reset validation error on new query
        state.validation_error = None
        return state

    def generate_sql_node(state: DataInsightWorkflowState) -> DataInsightWorkflowState:
        """从自然语言生成 SQL"""
        if state.natural_query is None:
            raise ValueError("natural_query is required")

        try:
            state.sql_query = agent.text_to_sql(state.natural_query)
            state.validation_error = None
        except Exception as e:
            state.validation_error = str(e)
        return state

    def validate_sql_node(state: DataInsightWorkflowState) -> DataInsightWorkflowState:
        """验证 SQL 语法和安全性"""
        if state.sql_query is None:
            state.validation_error = "No SQL query to validate"
            return state

        try:
            # Use the text_to_sql converter's validation
            agent.text_to_sql_converter._validate_sql(state.sql_query.sql)
            state.validation_error = None
        except ValidationError as e:
            state.validation_error = str(e)
        except Exception as e:
            state.validation_error = f"Validation error: {e}"

        return state

    def execute_query_node(state: DataInsightWorkflowState) -> DataInsightWorkflowState:
        """执行 SQL 查询并获取结果"""
        if state.sql_query is None:
            raise ValueError("sql_query is required")

        try:
            state.query_result = agent.execute_query(state.sql_query)
        except Exception as e:
            state.validation_error = f"Query execution error: {e}"
        return state

    def interpret_result_node(state: DataInsightWorkflowState) -> DataInsightWorkflowState:
        """解释查询结果"""
        if state.query_result is None:
            raise ValueError("query_result is required")

        state.interpretation = agent.interpret_result(state.query_result)
        return state

    def detect_anomaly_node(state: DataInsightWorkflowState) -> DataInsightWorkflowState:
        """检测数据中的异常"""
        if state.query_result is None:
            raise ValueError("query_result is required")

        # Extract numeric data from results for anomaly detection
        if state.query_result.results:
            # Try to detect anomalies in the first numeric column
            numeric_data = []
            for row in state.query_result.results:
                if row[0] is not None and isinstance(row[0], (int, float)):
                    numeric_data.append(float(row[0]))

            if len(numeric_data) >= 3:
                state.anomalies = agent.detect_anomaly(
                    metric="query_result",
                    data=numeric_data,
                    threshold=2.0,
                    method="statistical"
                )

        return state

    def analyze_root_cause_node(state: DataInsightWorkflowState) -> DataInsightWorkflowState:
        """分析异常的根本原因"""
        if not state.anomalies:
            return state

        state.root_causes = []
        for anomaly in state.anomalies:
            root_cause = agent.root_cause_analysis(anomaly)
            state.root_causes.append(root_cause)

        return state

    def generate_report_node(state: DataInsightWorkflowState) -> DataInsightWorkflowState:
        """生成完整的洞察报告"""
        if state.query_result is None:
            raise ValueError("query_result is required")

        state.insight_report = agent.generate_insight_report(
            state.query_result,
            state.anomalies
        )

        # Determine if high risk based on anomalies
        high_severity_anomalies = [
            a for a in state.anomalies
            if a.severity in (SeverityLevel.HIGH, SeverityLevel.CRITICAL)
        ]
        state.is_high_risk = len(high_severity_anomalies) > 0

        # Generate final report text
        report_parts = []

        if state.insight_report:
            report_parts.append(f"# 数据洞察报告\n")
            report_parts.append(f"## 查询\n{state.natural_query}\n")
            report_parts.append(f"## SQL\n```sql\n{state.insight_report.query}\n```\n")

            if state.interpretation:
                report_parts.append(f"## 解释\n{state.interpretation}\n")

            if state.anomalies:
                report_parts.append(f"## 检测到的异常 ({len(state.anomalies)})\n")
                for anomaly in state.anomalies:
                    report_parts.append(f"- **{anomaly.metric}**: {anomaly.description} (严重程度: {anomaly.severity.value})\n")

            if state.root_causes:
                report_parts.append(f"## 根本原因分析\n")
                for rc in state.root_causes:
                    report_parts.append(f"### {rc.anomaly.metric}\n")
                    report_parts.append(f"可能原因:\n")
                    for cause in rc.possible_causes:
                        report_parts.append(f"- {cause}\n")
                    report_parts.append(f"建议行动:\n")
                    for action in rc.recommended_actions:
                        report_parts.append(f"- {action}\n")
                    report_parts.append(f"置信度: {rc.confidence:.0%}\n")

            if state.insight_report.recommendations:
                report_parts.append(f"## 建议\n")
                for rec in state.insight_report.recommendations:
                    report_parts.append(f"- {rec}\n")

        state.final_report = "".join(report_parts)
        return state

    def human_review_node(state: DataInsightWorkflowState) -> DataInsightWorkflowState:
        """人工审核节点（HITL）- 用于高价值/高风险决策"""
        # Simplified implementation: auto-approve unless high risk with no recommendations
        # In production, this would integrate with a real approval workflow

        if state.is_high_risk:
            # High risk cases require explicit approval
            # For PoC, we auto-approve but set human_approved based on feedback
            if state.human_feedback is None:
                # No feedback yet - default to approved in PoC
                state.human_approved = True
            elif "reject" in state.human_feedback.lower():
                state.human_approved = False
            else:
                state.human_approved = True
        else:
            # Non-high-risk cases are auto-approved
            state.human_approved = True

        return state

    # 构建状态图
    workflow = StateGraph(DataInsightWorkflowState)

    # 添加节点
    workflow.add_node("parse_query", parse_query_node)
    workflow.add_node("generate_sql", generate_sql_node)
    workflow.add_node("validate_sql", validate_sql_node)
    workflow.add_node("execute_query", execute_query_node)
    workflow.add_node("interpret_result", interpret_result_node)
    workflow.add_node("detect_anomaly", detect_anomaly_node)
    workflow.add_node("analyze_root_cause", analyze_root_cause_node)
    workflow.add_node("generate_report", generate_report_node)
    workflow.add_node("human_review", human_review_node)

    # 设置入口点
    workflow.set_entry_point("parse_query")

    # 设置边
    workflow.add_edge("parse_query", "generate_sql")
    workflow.add_edge("generate_sql", "validate_sql")

    # 条件边: validate_sql -> execute_query (valid) 或 generate_sql (invalid, retry)
    def validation_route(state: DataInsightWorkflowState) -> str:
        if state.validation_error:
            if state.retry_count < state.max_retries:
                state.retry_count += 1
                return "invalid_retry"
            else:
                # Max retries exceeded, fail
                return "invalid_final"
        return "valid"

    workflow.add_conditional_edges(
        "validate_sql",
        validation_route,
        {
            "valid": "execute_query",
            "invalid_retry": "generate_sql",
            "invalid_final": END,
        }
    )

    workflow.add_edge("execute_query", "interpret_result")
    workflow.add_edge("interpret_result", "detect_anomaly")

    # 条件边: detect_anomaly -> analyze_root_cause (anomalies found) 或 generate_report (no anomalies)
    def anomaly_route(state: DataInsightWorkflowState) -> str:
        if state.anomalies and len(state.anomalies) > 0:
            return "anomalies_found"
        return "no_anomalies"

    workflow.add_conditional_edges(
        "detect_anomaly",
        anomaly_route,
        {
            "anomalies_found": "analyze_root_cause",
            "no_anomalies": "generate_report",
        }
    )

    workflow.add_edge("analyze_root_cause", "generate_report")

    # 条件边: generate_report -> human_review (high risk) 或 END (not high risk)
    def risk_route(state: DataInsightWorkflowState) -> str:
        if state.is_high_risk:
            return "high_risk"
        return "low_risk"

    workflow.add_conditional_edges(
        "generate_report",
        risk_route,
        {
            "high_risk": "human_review",
            "low_risk": END,
        }
    )

    # Human review conditional edges
    def human_review_route(state: DataInsightWorkflowState) -> str:
        if state.human_approved:
            return "approved"
        return "rejected"

    workflow.add_conditional_edges(
        "human_review",
        human_review_route,
        {
            "approved": END,
            "rejected": "parse_query",
        }
    )

    return workflow.compile()


def run_data_insight_workflow(
    natural_query: Optional[str] = None,
    agent: Optional[DataInsightAgent] = None,
) -> DataInsightWorkflowState:
    """运行数据洞察工作流并返回最终状态"""
    workflow = create_data_insight_workflow(agent)

    initial_state = DataInsightWorkflowState(natural_query=natural_query)
    final_state = workflow.invoke(initial_state)

    return final_state