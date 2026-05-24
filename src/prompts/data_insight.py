"""
数据洞察 Agent 的 System Prompt 和输出模板
"""

SYSTEM_PROMPT = """你是制造业数据分析师，擅长：
1. 将业务问题转化为精准的 SQL 查询
2. 解读数据异常并推断可能原因
3. 生成可操作的改善建议
4. 用业务语言解释技术发现

工作流程：
1. 理解业务问题的背景和目标
2. 分析数据库 schema 和可用字段
3. 构建高效的 SQL 查询
4. 解读查询结果，识别关键发现
5. 检测异常模式和趋势
6. 分析根本原因并提出改善建议
7. 生成结构化的洞察报告

输出格式：
- SQL 查询及说明
- 数据解读结论（带数据支撑）
- 异常分析报告（时间/设备/产品维度）
- 改善建议清单（按优先级排序）
- 洞察报告（业务语言，可直接呈现给管理层）

语气要求：
- 专业、严谨，数据驱动
- 用业务术语而非技术术语
- 结论要有数据支撑，建议要有可行性"""

TEXT_TO_SQL_PROMPT = """
## 自然语言转 SQL 查询

### 业务问题
{user_query}

### 数据库 Schema
{schema}

### 可用表及字段
{tables}

### 约束条件
{constraints}

---

请将上述业务问题转化为精准的 SQL 查询。

**要求**：
1. 考虑查询性能，使用合适的索引
2. 添加必要的过滤条件（如日期范围、状态筛选）
3. 处理 NULL 值和边界情况
4. 添加注释说明关键逻辑

**输出格式**：
```sql
-- 说明：{query_purpose}
SELECT
    ...
FROM ...
WHERE ...
GROUP BY ...
ORDER BY ...
```

**SQL 查询**：
```sql
{generated_sql}
```

**查询说明**：
- 使用了哪些表和字段：...
- 过滤条件：...
- 聚合方式：...
- 预期返回行数：...
"""

RESULT_INTERPRETATION_PROMPT = """
## 查询结果解读

### 业务问题
{user_query}

### SQL 查询
```sql
{query}
```

### 查询结果
{data_results}

---

请解读上述查询结果，回答业务问题。

**解读维度**：
1. **数据概览**：结果行数、数值范围、分布特征
2. **关键发现**：与业务问题直接相关的数据点
3. **异常检测**：是否有明显异常值或模式
4. **趋势分析**：数据随时间或其他维度的变化

**输出格式**：

### 数据概览
- 总记录数：{count}
- 数值范围：{min} ~ {max}
- 平均值：{avg}

### 关键发现
1. {finding_1}
2. {finding_2}
3. {finding_3}

### 异常标记
- 异常值：{anomalies}

### 结论
{conclusion}
"""

ANOMALY_DETECTION_PROMPT = """
## 数据异常检测

### 检测范围
- 时间范围：{date_range}
- 产品线：{product_lines}
- 设备范围：{equipment_ids}

### 正常基准
- 历史均值：{historical_mean}
- 历史标准差：{historical_std}
- 正常波动范围：{normal_range}

### 当前数据
{current_data}

---

请检测数据中的异常模式。

**检测方法**：
1. 统计方法（标准差、IQR、移动平均）
2. 模式识别（趋势突变、周期性异常）
3. 多维度交叉验证

**输出格式**：

### 异常清单

| 序号 | 时间戳 | 指标 | 测量值 | 异常类型 | 偏离程度 |
|:---|:---|:---|:---|:---|:---|
| 1 | {timestamp} | {metric} | {value} | {type} | {deviation} |

### 异常模式总结
- 时间维度：{temporal_pattern}
- 设备维度：{equipment_pattern}
- 产品维度：{product_pattern}

### 风险等级
- 高风险：{high_risk_count} 项
- 中风险：{medium_risk_count} 项
- 低风险：{low_risk_count} 项
"""

ROOT_CAUSE_ANALYSIS_PROMPT = """
## 根本原因分析

### 异常现象
{anomaly_description}

### 相关数据
{related_data}

### 环境信息
- 设备状态：{equipment_status}
- 操作记录：{operation_logs}
- 维护历史：{maintenance_history}

### 生产上下文
{production_context}

---

请分析异常的根本原因。

**分析方法**：
1. 5Why 分析法（连续追问为什么）
2. 鱼骨图维度（人、机、料、法、环、测）
3. 数据关联性分析（时序相关性、因果关系）

**输出格式**：

### 问题陈述
{problem_statement}

### 5Why 分析
- Why 1：{why1} → Because {cause1}
- Why 2：{why2} → Because {cause2}
- Why 3：{why3} → Because {cause3}
- Why 4：{why4} → Because {cause4}
- Why 5：{why5} → Because {root_cause}

### 可能原因

#### 设备因素
{equipment_factors}

#### 物料因素
{material_factors}

#### 方法因素
{process_factors}

#### 环境因素
{environment_factors}

### 最可能根因
{most_likely_root_cause}

### 置信度
{confidence}
"""

INSIGHT_REPORT_PROMPT = """
## 洞察报告生成

### 核心发现
{findings}

### 数据支撑
{data_evidence}

### 业务影响
{business_impact}

### 建议措施
{recommended_actions}

---

请生成结构化的业务洞察报告。

**报告要求**：
1. Executive Summary（1页，核心结论）
2. 详细分析（数据支撑、图表建议）
3. 行动建议（按优先级排序，附责任人）
4. 预期效果（量化指标）

**输出格式**：

# 数据洞察报告

## 执行摘要
{executive_summary}

## 关键发现

### 发现 1：{finding_title_1}
- 数据支撑：{evidence_1}
- 业务影响：{impact_1}

### 发现 2：{finding_title_2}
- 数据支撑：{evidence_2}
- 业务影响：{impact_2}

### 发现 3：{finding_title_3}
- 数据支撑：{evidence_3}
- 业务影响：{impact_3}

## 行动建议

| 优先级 | 行动项 | 预期效果 | 责任人 | 时间节点 |
|:---|:---|:---|:---|:---|
| P1 | {action_1} | {effect_1} | {owner_1} | {timeline_1} |
| P2 | {action_2} | {effect_2} | {owner_2} | {timeline_2} |
| P3 | {action_3} | {effect_3} | {owner_3} | {timeline_3} |

## 预期改善指标
- 指标 1：{metric_1}（改善 {improvement_1}%）
- 指标 2：{metric_2}（改善 {improvement_2}%）
- 指标 3：{metric_3}（改善 {improvement_3}%）

## 风险与注意事项
{risks_and_considerations}
"""