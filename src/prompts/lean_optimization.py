"""
精益优化 Agent 的 System Prompt 和输出模板
"""

SYSTEM_PROMPT = """你是精益制造专家，擅长：
1. 分析生产流程，识别各种浪费（等待、搬运、过度加工、库存、动作、缺陷、过量生产、人才浪费）
2. 生成当前状态和未来状态的价值流图（VSM）
3. 提出 Kaizen 改善方案，运用 5Why 和鱼骨图进行根本原因分析
4. 用业务语言解释技术发现，非技术人员也能理解

工作流程：
1. 收集生产数据（节拍时间、换型时间、库存、在制品数量）
2. 绘制当前状态价值流图
3. 分析浪费点及其根本原因
4. 识别瓶颈工序
5. 设计未来状态价值流图
6. 提出具体改善措施及预期效果

输出格式：
- 当前状态 VSM（带时间轴和物流信息）
- 浪费清单及分类（按精益浪费类型）
- 瓶颈分析报告
- Kaizen 改善提案（问题描述、根因分析、改善措施、预期效果）
- 未来状态 VSM 预测

语气要求：
- 专业但易懂，避免过多精益术语
- 用数据和事实说话
- 改善建议要具体可执行
- 关注业务价值而非技术细节"""

VSM_ANALYSIS_PROMPT = """
## 当前状态价值流图分析

### 生产信息
- 产品族：{product_family}
- 客户需求：{customer_demand}
- 节拍时间（TT）：{takt_time} 秒/件
- 工作时间：{working_hours} 小时/天

### 工序数据
{process_data}

### 物流数据
- 运输距离：{transport_distance}
- 在制品库存：{work_in_process}
- 等待时间：{waiting_time}

### 质量数据
- 缺陷率：{defect_rate}
- 返工率：{rework_rate}

---

请生成当前状态价值流图（VSM）。

**分析要求**：
1. 识别增值活动和非增值活动（浪费）
2. 计算增值时间比
3. 标注瓶颈工序
4. 识别改善机会点

**输出格式**：

### 当前状态 VSM

```
时间轴：
[工序1] ---> [工序2] ---> [工序3] ---> [出货]
  |          |          |          |
  V          V          V          V
增值时间:    增值时间:   增值时间:   增值时间:
{takt_time1} {takt_time2} {takt_time3} {takt_time4}

库存/在制品：
工序间库存: {inventory_between}
```

### 关键指标
- 总增值时间：{total_value_added_time} 秒
- 总非增值时间：{total_non_value_added_time} 秒
- 增值时间比：{value_added_ratio}%
- 预计改善空间：{improvement_potential}%

### 浪费识别
| 浪费类型 | 位置 | 描述 | 估计损失时间 |
|:---|:---|:---|:---|
| 等待 | {waste_location_1} | {waste_description_1} | {waste_time_1} |
| 搬运 | {waste_location_2} | {waste_description_2} | {waste_time_2} |
| 库存 | {waste_location_3} | {waste_description_3} | {waste_time_3} |

### 改善机会
1. {opportunity_1}
2. {opportunity_2}
3. {opportunity_3}
"""

WASTE_ANALYSIS_PROMPT = """
## 浪费分析与分类

### 生产数据
{waste_data}

### 识别的浪费项目
{waste_items}

### 浪费持续时间
{waste_duration}

### 影响范围
{waste_impact_scope}

---

请对上述浪费进行分类和分析。

**浪费分类标准**：
1. 等待（Wait）- 人员和设备空转
2. 搬运（Transportation）- 不必要的物料移动
3. 过度加工（Over-processing）- 超出客户需求的加工
4. 库存（Inventory）- 超过必要数量的在制品和成品
5. 动作（Motion）- 操作人员不必要的动作
6. 缺陷（Defect）- 需要返工或报废的质量问题
7. 过量生产（Over-production）- 超过客户需求的产量
8. 人才浪费（Skills）- 未充分利用人员能力和知识

**输出格式**：

### 浪费分类汇总

| 浪费类型 | 次数 | 总时间损失 | 占比 | 优先级 |
|:---|:---|:---|:---|:---|
| 等待 | {wait_count} | {wait_time} | {wait_ratio}% | {wait_priority} |
| 搬运 | {transport_count} | {transport_time} | {transport_ratio}% | {transport_priority} |
| 过度加工 | {overprocess_count} | {overprocess_time} | {overprocess_ratio}% | {overprocess_priority} |
| 库存 | {inventory_count} | {inventory_time} | {inventory_ratio}% | {inventory_priority} |
| 动作 | {motion_count} | {motion_time} | {motion_ratio}% | {motion_priority} |
| 缺陷 | {defect_count} | {defect_time} | {defect_ratio}% | {defect_priority} |
| 过量生产 | {overprod_count} | {overprod_time} | {overprod_ratio}% | {overprod_priority} |
| 人才浪费 | {skills_count} | {skills_time} | {skills_ratio}% | {skills_priority} |

### 主要浪费根因（5Why 分析）
**浪费项**：{main_waste_item}

- Why 1：{why1} → Because {cause1}
- Why 2：{why2} → Because {cause2}
- Why 3：{why3} → Because {cause3}
- Why 4：{why4} → Because {cause4}
- Why 5：{why5} → Because {root_cause}

### Top 3 改善重点
1. **{priority_1_waste}**
   - 当前损失：{priority_1_loss}
   - 改善方向：{priority_1_direction}

2. **{priority_2_waste}**
   - 当前损失：{priority_2_loss}
   - 改善方向：{priority_2_direction}

3. **{priority_3_waste}**
   - 当前损失：{priority_3_loss}
   - 改善方向：{priority_3_direction}

### 改善优先级矩阵
| | 高频率 | 低频率 |
|:---|:---|:---|
| **高损失** | {high_freq_high_loss} | {low_freq_high_loss} |
| **低损失** | {high_freq_low_loss} | {low_freq_low_loss} |
"""

BOTTLENECK_ANALYSIS_PROMPT = """
## 瓶颈工序分析

### 工序信息
{process_info}

### 节拍时间对比
| 工序 | 节拍时间(秒) | 利用率 | 状态 |
|:---|:---|:---|:---|
| {process_1} | {tt_1} | {util_1}% | {status_1} |
| {process_2} | {tt_2} | {util_2}% | {status_2} |
| {process_3} | {tt_3} | {util_3}% | {status_3} |
| {process_4} | {tt_4} | {util_4}% | {status_4} |

### 客户需求节拍
{customer_takt}

### 库存积压情况
{inventory_buildup}

### 换型时间分布
{changeover_time}

---

请识别和分析瓶颈工序。

**分析方法**：
1. 节拍时间对比法（各工序节拍 vs 客户需求节拍）
2. 利用率分析法（实际产出 vs 理论产能）
3. 库存积压识别法（在制品堆积点）
4. 换型时间影响分析

**输出格式**：

### 瓶颈识别结果

| 瓶颈工序 | 节拍时间 | 与TT差距 | 利用率 | 优先级 |
|:---|:---|:---|:---|:---|
| {bottleneck_process_1} | {bottleneck_tt_1} | +{gap_1}秒 | {bottleneck_util_1}% | P{bottleneck_priority_1} |
| {bottleneck_process_2} | {bottleneck_tt_2} | +{gap_2}秒 | {bottleneck_util_2}% | P{bottleneck_priority_2} |

### 瓶颈影响分析
**对整体产能的影响**：
{bottleneck_impact_on_capacity}

**对交付周期的影响**：
{bottleneck_impact_on_leadtime}

**对在制品库存的影响**：
{bottleneck_impact_on_inventory}

### 瓶颈根因分析（鱼骨图维度）
**人**（Man）：
{man_factor}

**机**（Machine）：
{machine_factor}

**料**（Material）：
{material_factor}

**法**（Method）：
{method_factor}

**环**（Environment）：
{environment_factor}

**测**（Measurement）：
{measurement_factor}

### 改善方向建议
1. **短期措施**：{short_term_measures}
2. **中期措施**：{medium_term_measures}
3. **长期措施**：{long_term_measures}

### 预期改善效果
- 预计产能提升：{capacity_improvement}%
- 预计交付周期缩短：{leadtime_reduction}天
- 预计库存降低：{inventory_reduction}%
"""

KAIZEN_PROPOSAL_PROMPT = """
## Kaizen 改善提案

### 问题描述
{problem_description}

### 当前状态指标
- 产能利用率：{current_capacity_util}%
- 交付周期：{current_lead_time}天
- 在制品库存：{current_wip}件
- 缺陷率：{current_defect_rate}%

### 浪费识别结果
{waste_analysis_results}

### 瓶颈分析结果
{bottleneck_analysis_results}

---

请生成 Kaizen 改善提案。

**Kaizen 方法论**：
1. 明确问题（现状 vs 目标）
2. 分析根本原因（5Why、鱼骨图）
3. 提出改善措施（SMART 原则）
4. 制定实施计划（人员、时间、资源）
5. 设定改善目标和评估标准

**输出格式**：

### Kaizen 提案标题
{kaizen_title}

### 1. 问题定义

**现状问题**：
{current_problem}

**改善目标**（SMART）：
- Specific（具体）：{smart_specific}
- Measurable（可衡量）：{smart_measurable}
- Achievable（可达成）：{smart_achievable}
- Relevant（相关）：{smart_relevant}
- Time-bound（有时限）：{smart_timebound}

**目标指标**：
| 指标 | 当前值 | 目标值 | 改善幅度 |
|:---|:---|:---|:---|
| 产能利用率 | {current_capacity_util}% | {target_capacity_util}% | +{capacity_improvement}% |
| 交付周期 | {current_lead_time}天 | {target_lead_time}天 | -{leadtime_reduction}% |
| 在制品库存 | {current_wip}件 | {target_wip}件 | -{wip_reduction}% |
| 缺陷率 | {current_defect_rate}% | {target_defect_rate}% | -{defect_reduction}% |

### 2. 根本原因分析（5Why）

- Why 1：{why1} → Because {cause1}
- Why 2：{why2} → Because {cause2}
- Why 3：{why3} → Because {cause3}
- Why 4：{why4} → Because {cause4}
- Why 5：{why5} → Because {root_cause}

### 3. 改善措施

#### 措施 1：{measure_1_title}
- **内容**：{measure_1_content}
- **责任部门**：{measure_1_owner}
- **实施时间**：{measure_1_timeline}
- **所需资源**：{measure_1_resources}
- **预期效果**：{measure_1_expected_effect}

#### 措施 2：{measure_2_title}
- **内容**：{measure_2_content}
- **责任部门**：{measure_2_owner}
- **实施时间**：{measure_2_timeline}
- **所需资源**：{measure_2_resources}
- **预期效果**：{measure_2_expected_effect}

#### 措施 3：{measure_3_title}
- **内容**：{measure_3_content}
- **责任部门**：{measure_3_owner}
- **实施时间**：{measure_3_timeline}
- **所需资源**：{measure_3_resources}
- **预期效果**：{measure_3_expected_effect}

### 4. 实施计划

| 阶段 | 时间 | 行动项 | 责任人 | 检查点 |
|:---|:---|:---|:---|:---|
| 准备阶段 | {prep_phase_time} | {prep_phase_actions} | {prep_phase_owner} | {prep_phase_checkpoint} |
| 实施阶段 | {impl_phase_time} | {impl_phase_actions} | {impl_phase_owner} | {impl_phase_checkpoint} |
| 验证阶段 | {verify_phase_time} | {verify_phase_actions} | {verify_phase_owner} | {verify_phase_checkpoint} |

### 5. 预期效果

**业务价值**：
{business_value}

**财务价值**：
| 项 目 | 金 额 |
|:---|:---|
| 年化节约成本 | {annual_cost_saving}元 |
| 产能提升收益 | {capacity_revenue}元 |
| 质量成本降低 | {quality_cost_reduction}元 |
| **年度总效益** | {total_annual_benefit}元 |

### 6. 风险与应对

| 风险 | 影响 | 概率 | 应对措施 |
|:---|:---|:---|:---|
| {risk_1} | {risk_1_impact} | {risk_1_probability}% | {risk_1_countermeasure} |
| {risk_2} | {risk_2_impact} | {risk_2_probability}% | {risk_2_countermeasure} |
"""

TARGET_STATE_VSM_PROMPT = """
## 未来状态价值流图预测

### 当前状态 VSM
{current_state_vsm}

### Kaizen 改善措施
{kaizen_measures}

### 改善目标
- 目标产能提升：{target_capacity_improvement}%
- 目标交付周期缩短：{target_leadtime_reduction}天
- 目标库存降低：{target_inventory_reduction}%
- 目标缺陷率：{target_defect_rate}%

### 实施计划时间线
{implementation_timeline}

---

请预测未来状态价值流图（VSM）。

**预测方法**：
1. 基于改善措施重新计算工序节拍时间
2. 评估库存降低效果（看板拉动系统）
3. 预测换型时间改善（SMED）
4. 计算整体交付周期变化

**输出格式**：

### 未来状态 VSM

```
预计完工时间轴：
[工序1] ---> [工序2] ---> [工序3] ---> [出货]
  |          |          |          |
  V          V          V          V
预计增值时间:
{target_tt_1} {target_tt_2} {target_tt_3} {target_tt_4}

预计库存水平：
工序间库存: {target_inventory_between}
```

### 关键指标对比

| 指标 | 当前状态 | 未来状态 | 改善幅度 |
|:---|:---|:---|:---|
| 总增值时间 | {current_vat}秒 | {target_vat}秒 | -{vat_reduction}秒 |
| 总交付周期 | {current_leadtime}天 | {target_leadtime}天 | -{leadtime_reduction}天 |
| 在制品库存 | {current_wip}件 | {target_wip}件 | -{wip_reduction}件 |
| 产能利用率 | {current_util}% | {target_util}% | +{util_improvement}% |

### 改善前后对比图

**时间轴对比**：
```
当前状态：|======|====================|====================|======|
           ↑                    ↑                    ↑
        增值时间           非增值等待时间          库存等待

未来状态：|====|================|================|====|
           ↑                    ↑                ↑
        增值时间           非增值时间大幅减少    拉动生产
```

### 改善效果分析

**增值时间比提升**：
- 当前：{current_var}%
- 目标：{target_var}%
- 提升：+{var_improvement}个百分点

**交付周期缩短**：
- 客户需求节拍：{customer_takt}秒
- 当前交付周期：{current_leadtime}天
- 目标交付周期：{target_leadtime}天
- 缩短比例：{leadtime_reduction_ratio}%

**库存降低效果**：
- 当前平均库存：{current_avg_inventory}件
- 目标平均库存：{target_avg_inventory}件
- 库存降低：{inventory_reduction}%

### 新增改善机会

基于未来状态 VSM，识别进一步改善机会：

1. **{additional_opportunity_1}**
   - 预估效果：{additional_effect_1}
   - 实施难度：{additional_difficulty_1}

2. **{additional_opportunity_2}**
   - 预估效果：{additional_effect_2}
   - 实施难度：{additional_difficulty_2}

3. **{additional_opportunity_3}**
   - 预估效果：{additional_effect_3}
   - 实施难度：{additional_difficulty_3}

### 建议的后续行动

| 行动项 | 优先级 | 预计收益 | 备注 |
|:---|:---|:---|:---|
| {follow_up_action_1} | P{follow_up_priority_1} | {follow_up_benefit_1} | |
| {follow_up_action_2} | P{follow_up_priority_2} | {follow_up_benefit_2} | |
| {follow_up_action_3} | P{follow_up_priority_3} | {follow_up_benefit_3} | |
"""