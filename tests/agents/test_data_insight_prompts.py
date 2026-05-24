"""
数据洞察 Agent Prompt 模板测试
"""
import pytest
from src.prompts.data_insight import (
    SYSTEM_PROMPT,
    TEXT_TO_SQL_PROMPT,
    RESULT_INTERPRETATION_PROMPT,
    ANOMALY_DETECTION_PROMPT,
    ROOT_CAUSE_ANALYSIS_PROMPT,
    INSIGHT_REPORT_PROMPT,
)


class TestDataInsightPrompts:
    """数据洞察 Agent Prompt 模板测试"""

    def test_system_prompt_exists(self):
        """测试 System Prompt 存在且非空"""
        assert SYSTEM_PROMPT is not None
        assert len(SYSTEM_PROMPT) > 0
        assert "制造业数据分析师" in SYSTEM_PROMPT
        assert "SQL" in SYSTEM_PROMPT

    def test_text_to_sql_prompt(self):
        """测试 TEXT_TO_SQL_PROMPT 模板"""
        assert TEXT_TO_SQL_PROMPT is not None
        assert len(TEXT_TO_SQL_PROMPT) > 0
        # 检查关键占位符
        assert "{user_query}" in TEXT_TO_SQL_PROMPT
        assert "{schema}" in TEXT_TO_SQL_PROMPT
        assert "{tables}" in TEXT_TO_SQL_PROMPT
        assert "{constraints}" in TEXT_TO_SQL_PROMPT
        # 检查输出格式要求
        assert "SQL 查询" in TEXT_TO_SQL_PROMPT
        assert "GROUP BY" in TEXT_TO_SQL_PROMPT

    def test_result_interpretation_prompt(self):
        """测试 RESULT_INTERPRETATION_PROMPT 模板"""
        assert RESULT_INTERPRETATION_PROMPT is not None
        assert len(RESULT_INTERPRETATION_PROMPT) > 0
        # 检查关键占位符
        assert "{user_query}" in RESULT_INTERPRETATION_PROMPT
        assert "{query}" in RESULT_INTERPRETATION_PROMPT
        assert "{data_results}" in RESULT_INTERPRETATION_PROMPT
        # 检查输出格式
        assert "数据概览" in RESULT_INTERPRETATION_PROMPT
        assert "关键发现" in RESULT_INTERPRETATION_PROMPT
        assert "结论" in RESULT_INTERPRETATION_PROMPT

    def test_anomaly_detection_prompt(self):
        """测试 ANOMALY_DETECTION_PROMPT 模板"""
        assert ANOMALY_DETECTION_PROMPT is not None
        assert len(ANOMALY_DETECTION_PROMPT) > 0
        # 检查关键占位符
        assert "{date_range}" in ANOMALY_DETECTION_PROMPT
        assert "{product_lines}" in ANOMALY_DETECTION_PROMPT
        assert "{equipment_ids}" in ANOMALY_DETECTION_PROMPT
        assert "{historical_mean}" in ANOMALY_DETECTION_PROMPT
        assert "{current_data}" in ANOMALY_DETECTION_PROMPT
        # 检查输出格式
        assert "异常清单" in ANOMALY_DETECTION_PROMPT
        assert "风险等级" in ANOMALY_DETECTION_PROMPT

    def test_root_cause_analysis_prompt(self):
        """测试 ROOT_CAUSE_ANALYSIS_PROMPT 模板"""
        assert ROOT_CAUSE_ANALYSIS_PROMPT is not None
        assert len(ROOT_CAUSE_ANALYSIS_PROMPT) > 0
        # 检查关键占位符
        assert "{anomaly_description}" in ROOT_CAUSE_ANALYSIS_PROMPT
        assert "{related_data}" in ROOT_CAUSE_ANALYSIS_PROMPT
        assert "{equipment_status}" in ROOT_CAUSE_ANALYSIS_PROMPT
        assert "{production_context}" in ROOT_CAUSE_ANALYSIS_PROMPT
        # 检查分析方法
        assert "5Why" in ROOT_CAUSE_ANALYSIS_PROMPT
        assert "鱼骨图" in ROOT_CAUSE_ANALYSIS_PROMPT

    def test_insight_report_prompt(self):
        """测试 INSIGHT_REPORT_PROMPT 模板"""
        assert INSIGHT_REPORT_PROMPT is not None
        assert len(INSIGHT_REPORT_PROMPT) > 0
        # 检查关键占位符
        assert "{findings}" in INSIGHT_REPORT_PROMPT
        assert "{data_evidence}" in INSIGHT_REPORT_PROMPT
        assert "{business_impact}" in INSIGHT_REPORT_PROMPT
        assert "{recommended_actions}" in INSIGHT_REPORT_PROMPT
        # 检查报告结构
        assert "执行摘要" in INSIGHT_REPORT_PROMPT
        assert "行动建议" in INSIGHT_REPORT_PROMPT
        assert "预期改善指标" in INSIGHT_REPORT_PROMPT

    def test_all_prompts_chinese(self):
        """测试所有 Prompt 包含中文"""
        assert "制造业" in SYSTEM_PROMPT
        assert "业务" in TEXT_TO_SQL_PROMPT
        assert "数据" in RESULT_INTERPRETATION_PROMPT
        assert "异常" in ANOMALY_DETECTION_PROMPT
        assert "原因" in ROOT_CAUSE_ANALYSIS_PROMPT
        assert "报告" in INSIGHT_REPORT_PROMPT

    def test_prompt_placeholders_format(self):
        """测试占位符格式正确（使用花括号）"""
        prompts = [
            TEXT_TO_SQL_PROMPT,
            RESULT_INTERPRETATION_PROMPT,
            ANOMALY_DETECTION_PROMPT,
            ROOT_CAUSE_ANALYSIS_PROMPT,
            INSIGHT_REPORT_PROMPT,
        ]
        for prompt in prompts:
            # 检查占位符格式（避免 {abc} 写成 {{abc}} 或 { abc}）
            import re
            # 正确的占位符格式：{word}，不包括 {{ 或 }}
            placeholders = re.findall(r'\{([^}]+)\}', prompt)
            for p in placeholders:
                assert len(p.strip()) > 0, f"占位符格式错误: '{p}'"
                assert p == p.strip(), f"占位符有空格: '{p}'"

    def test_system_prompt_contains_workflow(self):
        """测试 System Prompt 包含工作流程"""
        assert "工作流程" in SYSTEM_PROMPT
        # 检查工作流程步骤
        assert "SQL" in SYSTEM_PROMPT or "查询" in SYSTEM_PROMPT
        assert "异常" in SYSTEM_PROMPT or "数据" in SYSTEM_PROMPT
        assert "改善建议" in SYSTEM_PROMPT or "建议" in SYSTEM_PROMPT

    def test_all_prompt_templates_exist(self):
        """测试所有 5 个 Prompt 模板都存在"""
        assert TEXT_TO_SQL_PROMPT is not None
        assert RESULT_INTERPRETATION_PROMPT is not None
        assert ANOMALY_DETECTION_PROMPT is not None
        assert ROOT_CAUSE_ANALYSIS_PROMPT is not None
        assert INSIGHT_REPORT_PROMPT is not None

    def test_prompt_templates_not_empty(self):
        """测试所有 Prompt 模板都非空"""
        assert len(TEXT_TO_SQL_PROMPT.strip()) > 100
        assert len(RESULT_INTERPRETATION_PROMPT.strip()) > 100
        assert len(ANOMALY_DETECTION_PROMPT.strip()) > 100
        assert len(ROOT_CAUSE_ANALYSIS_PROMPT.strip()) > 100
        assert len(INSIGHT_REPORT_PROMPT.strip()) > 100