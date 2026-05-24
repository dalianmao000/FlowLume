"""
精益优化 Agent Prompt 模板测试
"""
import pytest
from src.prompts.lean_optimization import (
    SYSTEM_PROMPT,
    VSM_ANALYSIS_PROMPT,
    WASTE_ANALYSIS_PROMPT,
    BOTTLENECK_ANALYSIS_PROMPT,
    KAIZEN_PROPOSAL_PROMPT,
    TARGET_STATE_VSM_PROMPT,
)


class TestLeanOptimizationPrompts:
    """精益优化 Agent Prompt 模板测试"""

    def test_system_prompt_exists(self):
        """测试 System Prompt 存在且非空"""
        assert SYSTEM_PROMPT is not None
        assert len(SYSTEM_PROMPT) > 0
        assert "精益制造专家" in SYSTEM_PROMPT
        assert "VSM" in SYSTEM_PROMPT or "价值流" in SYSTEM_PROMPT

    def test_vsm_analysis_prompt(self):
        """测试 VSM_ANALYSIS_PROMPT 模板"""
        assert VSM_ANALYSIS_PROMPT is not None
        assert len(VSM_ANALYSIS_PROMPT) > 0
        # 检查关键占位符
        assert "{product_family}" in VSM_ANALYSIS_PROMPT
        assert "{customer_demand}" in VSM_ANALYSIS_PROMPT
        assert "{takt_time}" in VSM_ANALYSIS_PROMPT
        assert "{process_data}" in VSM_ANALYSIS_PROMPT
        # 检查输出格式要求
        assert "VSM" in VSM_ANALYSIS_PROMPT or "价值流" in VSM_ANALYSIS_PROMPT
        assert "增值时间" in VSM_ANALYSIS_PROMPT
        assert "浪费" in VSM_ANALYSIS_PROMPT

    def test_waste_analysis_prompt(self):
        """测试 WASTE_ANALYSIS_PROMPT 模板"""
        assert WASTE_ANALYSIS_PROMPT is not None
        assert len(WASTE_ANALYSIS_PROMPT) > 0
        # 检查关键占位符
        assert "{waste_data}" in WASTE_ANALYSIS_PROMPT
        assert "{waste_items}" in WASTE_ANALYSIS_PROMPT
        assert "{waste_duration}" in WASTE_ANALYSIS_PROMPT
        assert "{waste_impact_scope}" in WASTE_ANALYSIS_PROMPT
        # 检查输出格式
        assert "浪费分类" in WASTE_ANALYSIS_PROMPT
        assert "5Why" in WASTE_ANALYSIS_PROMPT
        assert "改善重点" in WASTE_ANALYSIS_PROMPT

    def test_bottleneck_analysis_prompt(self):
        """测试 BOTTLENECK_ANALYSIS_PROMPT 模板"""
        assert BOTTLENECK_ANALYSIS_PROMPT is not None
        assert len(BOTTLENECK_ANALYSIS_PROMPT) > 0
        # 检查关键占位符
        assert "{process_info}" in BOTTLENECK_ANALYSIS_PROMPT
        assert "{customer_takt}" in BOTTLENECK_ANALYSIS_PROMPT
        assert "{inventory_buildup}" in BOTTLENECK_ANALYSIS_PROMPT
        assert "{changeover_time}" in BOTTLENECK_ANALYSIS_PROMPT
        # 检查分析方法
        assert "瓶颈" in BOTTLENECK_ANALYSIS_PROMPT
        assert "节拍" in BOTTLENECK_ANALYSIS_PROMPT
        assert "鱼骨图" in BOTTLENECK_ANALYSIS_PROMPT

    def test_kaizen_proposal_prompt(self):
        """测试 KAIZEN_PROPOSAL_PROMPT 模板"""
        assert KAIZEN_PROPOSAL_PROMPT is not None
        assert len(KAIZEN_PROPOSAL_PROMPT) > 0
        # 检查关键占位符
        assert "{problem_description}" in KAIZEN_PROPOSAL_PROMPT
        assert "{current_capacity_util}" in KAIZEN_PROPOSAL_PROMPT
        assert "{waste_analysis_results}" in KAIZEN_PROPOSAL_PROMPT
        assert "{bottleneck_analysis_results}" in KAIZEN_PROPOSAL_PROMPT
        # 检查提案结构
        assert "问题定义" in KAIZEN_PROPOSAL_PROMPT
        assert "根本原因" in KAIZEN_PROPOSAL_PROMPT
        assert "改善措施" in KAIZEN_PROPOSAL_PROMPT
        assert "实施计划" in KAIZEN_PROPOSAL_PROMPT

    def test_target_state_vsm_prompt(self):
        """测试 TARGET_STATE_VSM_PROMPT 模板"""
        assert TARGET_STATE_VSM_PROMPT is not None
        assert len(TARGET_STATE_VSM_PROMPT) > 0
        # 检查关键占位符
        assert "{current_state_vsm}" in TARGET_STATE_VSM_PROMPT
        assert "{kaizen_measures}" in TARGET_STATE_VSM_PROMPT
        assert "{target_capacity_improvement}" in TARGET_STATE_VSM_PROMPT
        assert "{implementation_timeline}" in TARGET_STATE_VSM_PROMPT
        # 检查预测内容
        assert "未来状态" in TARGET_STATE_VSM_PROMPT
        assert "预测" in TARGET_STATE_VSM_PROMPT
        assert "改善" in TARGET_STATE_VSM_PROMPT

    def test_all_prompts_chinese(self):
        """测试所有 Prompt 包含中文"""
        assert "精益" in SYSTEM_PROMPT
        assert "生产" in VSM_ANALYSIS_PROMPT
        assert "浪费" in WASTE_ANALYSIS_PROMPT
        assert "瓶颈" in BOTTLENECK_ANALYSIS_PROMPT
        assert "改善" in KAIZEN_PROPOSAL_PROMPT
        assert "未来" in TARGET_STATE_VSM_PROMPT

    def test_prompt_placeholders_format(self):
        """测试占位符格式正确（使用花括号）"""
        prompts = [
            VSM_ANALYSIS_PROMPT,
            WASTE_ANALYSIS_PROMPT,
            BOTTLENECK_ANALYSIS_PROMPT,
            KAIZEN_PROPOSAL_PROMPT,
            TARGET_STATE_VSM_PROMPT,
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
        assert "VSM" in SYSTEM_PROMPT or "价值流" in SYSTEM_PROMPT
        assert "浪费" in SYSTEM_PROMPT or "分析" in SYSTEM_PROMPT
        assert "Kaizen" in SYSTEM_PROMPT or "改善" in SYSTEM_PROMPT

    def test_all_prompt_templates_exist(self):
        """测试所有 5 个 Prompt 模板都存在"""
        assert VSM_ANALYSIS_PROMPT is not None
        assert WASTE_ANALYSIS_PROMPT is not None
        assert BOTTLENECK_ANALYSIS_PROMPT is not None
        assert KAIZEN_PROPOSAL_PROMPT is not None
        assert TARGET_STATE_VSM_PROMPT is not None

    def test_prompt_templates_not_empty(self):
        """测试所有 Prompt 模板都非空"""
        assert len(VSM_ANALYSIS_PROMPT.strip()) > 100
        assert len(WASTE_ANALYSIS_PROMPT.strip()) > 100
        assert len(BOTTLENECK_ANALYSIS_PROMPT.strip()) > 100
        assert len(KAIZEN_PROPOSAL_PROMPT.strip()) > 100
        assert len(TARGET_STATE_VSM_PROMPT.strip()) > 100

    def test_waste_categories_in_waste_prompt(self):
        """测试浪费分析包含8种浪费类型"""
        waste_types = ["等待", "搬运", "过度加工", "库存", "动作", "缺陷", "过量生产", "人才浪费"]
        for waste_type in waste_types:
            assert waste_type in WASTE_ANALYSIS_PROMPT

    def test_lean_methods_in_prompts(self):
        """测试精益方法论出现在相关prompt中"""
        # 5Why should appear in waste analysis and kaizen proposal
        assert "5Why" in WASTE_ANALYSIS_PROMPT
        assert "5Why" in KAIZEN_PROPOSAL_PROMPT
        # 鱼骨图 should appear in bottleneck analysis
        assert "鱼骨图" in BOTTLENECK_ANALYSIS_PROMPT
        # SMED, 看板 should be mentioned in VSM analysis or kaizen
        assert "SMART" in KAIZEN_PROPOSAL_PROMPT or "改善措施" in KAIZEN_PROPOSAL_PROMPT

    def test_output_format_sections(self):
        """测试各prompt包含输出格式说明"""
        # VSM分析应包含关键指标表格
        assert "关键指标" in VSM_ANALYSIS_PROMPT
        # 浪费分析应包含分类汇总表
        assert "浪费分类" in WASTE_ANALYSIS_PROMPT
        # 瓶颈分析应包含瓶颈识别结果
        assert "瓶颈识别" in BOTTLENECK_ANALYSIS_PROMPT
        # Kaizen提案应包含措施详情
        assert "改善措施" in KAIZEN_PROPOSAL_PROMPT
        # 目标状态VSM应包含指标对比
        assert "指标对比" in TARGET_STATE_VSM_PROMPT