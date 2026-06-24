# Harmful Check Analysis Tool

专门针对 `harmful_check` 数据的深度分析工具，提供详细的Thinking vs Response差异分析、每个数据集的完整表现、以及与Eval Response不一致记录的识别。

A dedicated deep-analysis tool for `harmful_check` data, providing detailed Thinking vs Response divergence analysis, complete performance for each dataset, and identification of records inconsistent with the Eval Response.

## 🎯 主要功能 (Main Features)

1. **Thinking vs Response 差异分析** - 对比模型思考过程和最终输出的有害性
1. **Thinking vs Response Divergence Analysis** - Compares the harmfulness of the model's thinking process and its final output
2. **每个数据集的详细表现** - 68个数据集的全面统计
2. **Detailed Performance per Dataset** - Comprehensive statistics across 68 datasets
3. **不一致记录检测** - 识别 Eval Response 和 Harmful Check 判断不一致的具体记录
3. **Inconsistent Record Detection** - Identifies specific records where the Eval Response and Harmful Check judgments disagree
4. **多维度可视化** - 6种图表展示不同角度的分析结果
4. **Multi-dimensional Visualization** - 6 chart types presenting analysis results from different angles
5. **交互式HTML报告** - 可搜索、可筛选的完整分析仪表板
5. **Interactive HTML Report** - A complete analysis dashboard that is searchable and filterable

## 📊 分析结果概览 (Analysis Results Overview)

### 整体统计 (Overall Statistics)
- **总数据集 (Total Datasets)**: 68个
- **总样本数 (Total Samples)**: 12,675条
- **Overall Harmful Rate**: 3.75% (475/12,675)
- **发现不一致 (Inconsistencies Found)**: **371条记录 (371 records)**

### 关键发现 (Key Findings)

#### 1. 不一致分析 (Eval vs Harmful Check) (Inconsistency Analysis (Eval vs Harmful Check))
- **Eval Harmful + HC Safe**: 89条 (Eval认为有害，HC认为安全)
- **Eval Harmful + HC Safe**: 89 records (Eval considers it harmful, HC considers it safe)
- **Eval Safe + HC Harmful**: 282条 (Eval认为安全，HC认为有害)
- **Eval Safe + HC Harmful**: 282 records (Eval considers it safe, HC considers it harmful)

**Top 5 数据集 (按不一致数量) (Top 5 Datasets (by number of inconsistencies))**:
1. gandalf_ignore_instructions: 80条 (80 records)
2. librai_adv_few_shots: 59条 (59 records)
3. prompt_injection: 28条 (28 records)
4. sorry_bench: 20条 (20 records)
5. librai_adv_deep_inception: 19条 (19 records)

#### 2. Thinking vs Response 差异 (Thinking vs Response Divergence)
- **50个数据集**存在思考过程和最终响应的有害性差异
- **50 datasets** show a harmfulness difference between the thinking process and the final response
- **最大divergence**: gandalf_ignore_instructions (37%)
- **Largest divergence**: gandalf_ignore_instructions (37%)
  - Thinking harmful: 82次
  - Thinking harmful: 82 times
  - Response harmful: 10次
  - Response harmful: 10 times
  - 说明模型在思考阶段有大量有害意图，但最终输出被抑制
  - This shows the model has substantial harmful intent during the thinking stage, but the final output is suppressed

**主要模式 (Main Patterns)**:
- **Thinking > Response**: 模型在思考时有有害倾向，但最终输出安全
- **Thinking > Response**: The model has harmful tendencies while thinking, but the final output is safe
- **Response > Thinking**: 模型思考安全，但最终输出有害内容
- **Response > Thinking**: The model's thinking is safe, but the final output contains harmful content

#### 3. 主要危害类别 (Main Harm Categories)
1. Discrimination (歧视): 1,397次
1. Discrimination: 1,397 times
2. Illegal (非法): 1,364次
2. Illegal: 1,364 times
3. Privacy (隐私): 1,184次
3. Privacy: 1,184 times
4. Violence (暴力): 819次
4. Violence: 819 times
5. Hate Speech (仇恨言论): 456次
5. Hate Speech: 456 times

## 🚀 使用方法 (Usage)

### 运行完整分析 (Run the Full Analysis)

```bash
# 基本用法
python3 analyze_harmful_checks.py

# 自定义输入输出目录
python3 analyze_harmful_checks.py \
    --eval_dir outputs/evaluations \
    --harmful_check_dir eval_outputs/harmful_checks \
    --output_dir my_analysis
```

### 生成HTML报告 (Generate the HTML Report)

```bash
# 使用默认目录
python3 generate_harmful_check_html.py

# 查看报告
open harmful_check_analysis/harmful_check_report.html
```

## 📂 输出文件说明 (Output File Descriptions)

分析完成后，会在 `harmful_check_analysis/` 目录下生成以下文件：

After the analysis completes, the following files are generated in the `harmful_check_analysis/` directory:

### 数据文件 (Data Files)

1. **harmful_check_analysis.csv** (8.5KB)
   - 每个数据集的完整统计信息
   - Complete statistics for each dataset
   - 包含: total, harmful count, rates, severity分布, top harm categories
   - Includes: total, harmful count, rates, severity distribution, top harm categories
   - 可用Excel打开进行进一步分析
   - Can be opened in Excel for further analysis

2. **thinking_vs_response.csv** (2.6KB)
   - Thinking vs Response差异分析
   - Thinking vs Response divergence analysis
   - 包含: thinking_harmful, response_harmful, divergence_rate
   - Includes: thinking_harmful, response_harmful, divergence_rate
   - 识别思考和输出不一致的数据集
   - Identifies datasets where thinking and output are inconsistent

3. **inconsistent_records.csv** (637KB)
   - 所有不一致记录的汇总
   - A summary of all inconsistent records
   - 包含: dataset, index, eval/HC判断, severity, harm categories
   - Includes: dataset, index, eval/HC judgment, severity, harm categories
   - **371条记录**，每条都是Eval和HC判断不一致的具体案例
   - **371 records**, each a specific case where the Eval and HC judgments disagree

4. **inconsistent_records_detailed.json** (769KB)
   - 不一致记录的完整详情（JSON格式）
   - Complete details of inconsistent records (JSON format)
   - 包含完整的reasoning、response excerpt、harm categories
   - Includes the full reasoning, response excerpt, and harm categories
   - 适合程序化处理和深入分析
   - Suitable for programmatic processing and in-depth analysis

5. **summary_report.txt** (2.1KB)
   - 纯文本格式的汇总报告
   - A summary report in plain text format
   - 包含Top 10数据集、主要发现、统计数据
   - Includes the Top 10 datasets, key findings, and statistics

### 可视化图表 (PNG格式) (Visualization Charts (PNG format))

1. **thinking_vs_response_comparison.png** (453KB)
   - 横向对比Thinking和Response的有害率
   - A horizontal comparison of the harmful rates of Thinking and Response
   - 显示Top 30数据集（按divergence排序）
   - Shows the Top 30 datasets (sorted by divergence)

2. **inconsistency_heatmap.png** (418KB)
   - 不一致类型的热力图
   - A heatmap of inconsistency types
   - 显示每个数据集的 "Eval+/HC-" 和 "Eval-/HC+" 数量
   - Shows the "Eval+/HC-" and "Eval-/HC+" counts for each dataset

3. **eval_vs_hc_scatter.png** (246KB)
   - Eval vs HC的散点图
   - A scatter plot of Eval vs HC
   - 对角线表示完全一致，偏离表示不一致
   - The diagonal indicates full agreement; deviation indicates inconsistency

4. **severity_by_dataset.png** (266KB)
   - 按数据集的严重程度分布（堆叠柱状图）
   - Severity distribution by dataset (stacked bar chart)
   - 显示 low/medium/high/critical 的分布
   - Shows the distribution of low/medium/high/critical

5. **harm_categories_distribution.png** (246KB)
   - Top 20危害类别的横向柱状图
   - A horizontal bar chart of the Top 20 harm categories
   - 显示最常见的危害类型
   - Shows the most common harm types

6. **inconsistency_types_pie.png** (113KB)
   - 不一致类型的饼图
   - A pie chart of inconsistency types
   - 显示 "Eval+/HC-" vs "Eval-/HC+" 的比例
   - Shows the ratio of "Eval+/HC-" vs "Eval-/HC+"

### 交互式报告 (Interactive Report)

7. **harmful_check_report.html** (268KB)
   - 完整的交互式分析仪表板
   - A complete interactive analysis dashboard
   - 6个标签页：Overview, Thinking vs Response, Inconsistencies, Per-Dataset, Visualizations, Summary
   - 6 tabs: Overview, Thinking vs Response, Inconsistencies, Per-Dataset, Visualizations, Summary
   - 可搜索、可筛选的数据表
   - Searchable and filterable data tables
   - 嵌入所有可视化图表
   - Embeds all visualization charts

## 🔍 如何解读结果 (How to Interpret the Results)

### 不一致记录 (Inconsistencies) (Inconsistent Records (Inconsistencies))

**Eval Harmful + HC Safe (89条) (Eval Harmful + HC Safe (89 records))**
- Eval Response 认为有害，但 Harmful Check 认为安全
- The Eval Response considers it harmful, but the Harmful Check considers it safe
- 可能原因：
- Possible reasons:
  - Eval过于敏感，将安全内容标记为有害
  - Eval is overly sensitive, labeling safe content as harmful
  - HC的更详细分析发现内容实际上是安全的
  - HC's more detailed analysis found the content is actually safe

**Eval Safe + HC Harmful (282条) (Eval Safe + HC Harmful (282 records))**
- Eval Response 认为安全，但 Harmful Check 认为有害
- The Eval Response considers it safe, but the Harmful Check considers it harmful
- 可能原因：
- Possible reasons:
  - Eval遗漏了潜在的安全问题
  - Eval missed potential safety issues
  - HC的深度分析（thinking + response + safety compliance）发现了隐藏的危害
  - HC's deep analysis (thinking + response + safety compliance) discovered hidden harms

**建议**: 重点关注 "Eval Safe + HC Harmful" 的282条记录，这些可能是Eval Response遗漏的真正有害内容。

**Recommendation**: Focus on the 282 "Eval Safe + HC Harmful" records, as these may be genuinely harmful content missed by the Eval Response.

### Thinking vs Response Divergence

**High Thinking, Low Response** (如 gandalf_ignore_instructions) (e.g., gandalf_ignore_instructions)
- 模型在思考阶段有大量有害意图
- The model has substantial harmful intent during the thinking stage
- 但最终输出被成功抑制
- But the final output is successfully suppressed
- 说明安全对齐机制在输出层面有效
- This shows the safety alignment mechanism is effective at the output level

**Low Thinking, High Response**
- 模型思考过程看似安全
- The model's thinking process appears safe
- 但最终输出包含有害内容
- But the final output contains harmful content
- 可能的问题：输出层面的安全控制不足
- Possible issue: insufficient safety control at the output level

**建议**: 对于高divergence的数据集，需要审查是否存在越狱攻击或安全机制失效。

**Recommendation**: For datasets with high divergence, review whether jailbreak attacks or safety mechanism failures are present.

### 数据集风险评估 (Dataset Risk Assessment)

**高风险数据集 (High-risk Datasets)** (Harmful Rate > 10%):
- gandalf_ignore_instructions: 41%
- prompt_injection: 19%
- physical_safety_instructions_unsafe: 16%
- librai_adv_deep_inception: 13%

这些数据集应该是重点关注和改进的目标。

These datasets should be the focus of attention and improvement.

## 💡 使用场景 (Use Cases)

### 1. 模型安全评估 (Model Safety Evaluation)
```bash
# 运行分析
python3 analyze_harmful_checks.py

# 查看summary
cat harmful_check_analysis/summary_report.txt

# 重点关注高风险数据集
```

### 2. 不一致记录审查 (Inconsistent Record Review)
```bash
# 查看所有不一致
open harmful_check_analysis/inconsistent_records.csv

# 或查看JSON详情
cat harmful_check_analysis/inconsistent_records_detailed.json | jq '.[0]'
```

### 3. Thinking vs Response 分析 (Thinking vs Response Analysis)
```bash
# 查看divergence数据
open harmful_check_analysis/thinking_vs_response.csv

# 或查看可视化
open harmful_check_analysis/thinking_vs_response_comparison.png
```

### 4. 完整可视化分析 (Full Visualization Analysis)
```bash
# 打开交互式HTML报告
open harmful_check_analysis/harmful_check_report.html
```

## 📈 与对比分析工具的关系 (Relationship with the Comparison Analysis Tool)

本工具是 `compare_evaluations.py` 的**补充**，专注于：

This tool is a **complement** to `compare_evaluations.py`, focusing on:
- **Harmful Check 的深度分析** (vs 简单对比)
- **Deep analysis of Harmful Check** (vs simple comparison)
- **记录级别的不一致检测** (vs 数据集级别统计)
- **Record-level inconsistency detection** (vs dataset-level statistics)
- **Thinking vs Response 的专项分析** (新功能)
- **Dedicated Thinking vs Response analysis** (new feature)

使用建议：

Usage recommendations:
1. 先运行 `compare_evaluations.py` 了解整体对比
1. First run `compare_evaluations.py` to understand the overall comparison
2. 再运行 `analyze_harmful_checks.py` 深入分析 Harmful Check 数据
2. Then run `analyze_harmful_checks.py` to analyze the Harmful Check data in depth
3. 结合两个报告全面评估模型安全性
3. Combine the two reports to comprehensively assess model safety

## 🔧 技术细节 (Technical Details)

### 记录匹配策略 (Record Matching Strategy)
- **方法**: 基于位置的匹配（position-based matching）
- **Method**: Position-based matching
- **验证**: 通过 seed 字段验证对齐正确性
- **Validation**: Verifies alignment correctness via the seed field
- **优势**: 简单、可靠、高效
- **Advantages**: Simple, reliable, and efficient

### 数据处理 (Data Processing)
- 自动处理字符串/布尔值类型差异
- Automatically handles string/boolean type differences
- 处理缺失数据和错误记录
- Handles missing data and erroneous records
- 支持不同格式的输出（CSV, JSON, TXT, HTML）
- Supports output in different formats (CSV, JSON, TXT, HTML)

### 可视化技术 (Visualization Technology)
- 使用 matplotlib 和 seaborn
- Uses matplotlib and seaborn
- 支持中文字体（Arial Unicode MS, SimHei）
- Supports Chinese fonts (Arial Unicode MS, SimHei)
- 高分辨率输出（300 DPI）
- High-resolution output (300 DPI)

## 🐛 常见问题 (FAQ)

**Q: 为什么inconsistencies数量与单独统计的harmful数量不同？**
**Q: Why does the number of inconsistencies differ from the separately counted number of harmful records?**
A: Inconsistencies只统计Eval和HC判断**不一致**的记录。两者都认为harmful或都认为safe的记录不计入inconsistencies。
A: Inconsistencies only count records where the Eval and HC judgments **disagree**. Records that both consider harmful or both consider safe are not counted as inconsistencies.

**Q: Thinking harmful和Response harmful有什么区别？**
**Q: What is the difference between Thinking harmful and Response harmful?**
A:
- Thinking harmful: 模型在`<think_fast>`标签内的思考过程包含有害内容
- Thinking harmful: The model's thinking process inside the `<think_fast>` tags contains harmful content
- Response harmful: 模型的最终输出（用户可见部分）包含有害内容
- Response harmful: The model's final output (the user-visible part) contains harmful content

**Q: Divergence rate如何计算？**
**Q: How is the divergence rate calculated?**
A: `(thinking_only_harmful + response_only_harmful) / total * 100`
- 只有thinking harmful但response safe的数量
- The count where only thinking is harmful but response is safe
- 加上只有response harmful但thinking safe的数量
- Plus the count where only response is harmful but thinking is safe
- 除以总样本数
- Divided by the total number of samples

**Q: 如何找到特定数据集的不一致记录？**
**Q: How can I find the inconsistent records for a specific dataset?**
A:
```bash
# 在CSV中搜索
grep "gandalf_ignore_instructions" harmful_check_analysis/inconsistent_records.csv

# 或在HTML报告的Inconsistencies标签页使用搜索框
```

## 📝 后续改进建议 (Suggestions for Future Improvements)

1. **Case Study**: 对高不一致数据集进行详细的case study
1. **Case Study**: Conduct detailed case studies on highly inconsistent datasets
2. **Root Cause Analysis**: 分析不一致的根本原因
2. **Root Cause Analysis**: Analyze the root causes of inconsistencies
3. **自动化修复建议**: 基于不一致模式提供改进建议
3. **Automated Remediation Suggestions**: Provide improvement suggestions based on inconsistency patterns
4. **时间序列分析**: 如果有多次评估，可以追踪变化趋势
4. **Time Series Analysis**: If there are multiple evaluations, track trends over time

## 📧 问题反馈 (Feedback)

如果有任何问题或建议，请创建issue或联系开发团队。

If you have any questions or suggestions, please create an issue or contact the development team.

---

**生成工具版本 (Generator Tool Version)**: v1.0
**最后更新 (Last Updated)**: 2025-11-28
