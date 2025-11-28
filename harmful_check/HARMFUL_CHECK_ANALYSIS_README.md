# Harmful Check Analysis Tool

专门针对 `harmful_check` 数据的深度分析工具，提供详细的Thinking vs Response差异分析、每个数据集的完整表现、以及与Eval Response不一致记录的识别。

## 🎯 主要功能

1. **Thinking vs Response 差异分析** - 对比模型思考过程和最终输出的有害性
2. **每个数据集的详细表现** - 68个数据集的全面统计
3. **不一致记录检测** - 识别 Eval Response 和 Harmful Check 判断不一致的具体记录
4. **多维度可视化** - 6种图表展示不同角度的分析结果
5. **交互式HTML报告** - 可搜索、可筛选的完整分析仪表板

## 📊 分析结果概览

### 整体统计
- **总数据集**: 68个
- **总样本数**: 12,675条
- **Overall Harmful Rate**: 3.75% (475/12,675)
- **发现不一致**: **371条记录**

### 关键发现

#### 1. 不一致分析 (Eval vs Harmful Check)
- **Eval Harmful + HC Safe**: 89条 (Eval认为有害，HC认为安全)
- **Eval Safe + HC Harmful**: 282条 (Eval认为安全，HC认为有害)

**Top 5 数据集 (按不一致数量)**:
1. gandalf_ignore_instructions: 80条
2. librai_adv_few_shots: 59条
3. prompt_injection: 28条
4. sorry_bench: 20条
5. librai_adv_deep_inception: 19条

#### 2. Thinking vs Response 差异
- **50个数据集**存在思考过程和最终响应的有害性差异
- **最大divergence**: gandalf_ignore_instructions (37%)
  - Thinking harmful: 82次
  - Response harmful: 10次
  - 说明模型在思考阶段有大量有害意图，但最终输出被抑制

**主要模式**:
- **Thinking > Response**: 模型在思考时有有害倾向，但最终输出安全
- **Response > Thinking**: 模型思考安全，但最终输出有害内容

#### 3. 主要危害类别
1. Discrimination (歧视): 1,397次
2. Illegal (非法): 1,364次
3. Privacy (隐私): 1,184次
4. Violence (暴力): 819次
5. Hate Speech (仇恨言论): 456次

## 🚀 使用方法

### 运行完整分析

```bash
# 基本用法
python3 analyze_harmful_checks.py

# 自定义输入输出目录
python3 analyze_harmful_checks.py \
    --eval_dir outputs/evaluations \
    --harmful_check_dir eval_outputs/harmful_checks \
    --output_dir my_analysis
```

### 生成HTML报告

```bash
# 使用默认目录
python3 generate_harmful_check_html.py

# 查看报告
open harmful_check_analysis/harmful_check_report.html
```

## 📂 输出文件说明

分析完成后，会在 `harmful_check_analysis/` 目录下生成以下文件：

### 数据文件

1. **harmful_check_analysis.csv** (8.5KB)
   - 每个数据集的完整统计信息
   - 包含: total, harmful count, rates, severity分布, top harm categories
   - 可用Excel打开进行进一步分析

2. **thinking_vs_response.csv** (2.6KB)
   - Thinking vs Response差异分析
   - 包含: thinking_harmful, response_harmful, divergence_rate
   - 识别思考和输出不一致的数据集

3. **inconsistent_records.csv** (637KB)
   - 所有不一致记录的汇总
   - 包含: dataset, index, eval/HC判断, severity, harm categories
   - **371条记录**，每条都是Eval和HC判断不一致的具体案例

4. **inconsistent_records_detailed.json** (769KB)
   - 不一致记录的完整详情（JSON格式）
   - 包含完整的reasoning、response excerpt、harm categories
   - 适合程序化处理和深入分析

5. **summary_report.txt** (2.1KB)
   - 纯文本格式的汇总报告
   - 包含Top 10数据集、主要发现、统计数据

### 可视化图表 (PNG格式)

1. **thinking_vs_response_comparison.png** (453KB)
   - 横向对比Thinking和Response的有害率
   - 显示Top 30数据集（按divergence排序）

2. **inconsistency_heatmap.png** (418KB)
   - 不一致类型的热力图
   - 显示每个数据集的 "Eval+/HC-" 和 "Eval-/HC+" 数量

3. **eval_vs_hc_scatter.png** (246KB)
   - Eval vs HC的散点图
   - 对角线表示完全一致，偏离表示不一致

4. **severity_by_dataset.png** (266KB)
   - 按数据集的严重程度分布（堆叠柱状图）
   - 显示 low/medium/high/critical 的分布

5. **harm_categories_distribution.png** (246KB)
   - Top 20危害类别的横向柱状图
   - 显示最常见的危害类型

6. **inconsistency_types_pie.png** (113KB)
   - 不一致类型的饼图
   - 显示 "Eval+/HC-" vs "Eval-/HC+" 的比例

### 交互式报告

7. **harmful_check_report.html** (268KB)
   - 完整的交互式分析仪表板
   - 6个标签页：Overview, Thinking vs Response, Inconsistencies, Per-Dataset, Visualizations, Summary
   - 可搜索、可筛选的数据表
   - 嵌入所有可视化图表

## 🔍 如何解读结果

### 不一致记录 (Inconsistencies)

**Eval Harmful + HC Safe (89条)**
- Eval Response 认为有害，但 Harmful Check 认为安全
- 可能原因：
  - Eval过于敏感，将安全内容标记为有害
  - HC的更详细分析发现内容实际上是安全的

**Eval Safe + HC Harmful (282条)**
- Eval Response 认为安全，但 Harmful Check 认为有害
- 可能原因：
  - Eval遗漏了潜在的安全问题
  - HC的深度分析（thinking + response + safety compliance）发现了隐藏的危害

**建议**: 重点关注 "Eval Safe + HC Harmful" 的282条记录，这些可能是Eval Response遗漏的真正有害内容。

### Thinking vs Response Divergence

**High Thinking, Low Response** (如 gandalf_ignore_instructions)
- 模型在思考阶段有大量有害意图
- 但最终输出被成功抑制
- 说明安全对齐机制在输出层面有效

**Low Thinking, High Response**
- 模型思考过程看似安全
- 但最终输出包含有害内容
- 可能的问题：输出层面的安全控制不足

**建议**: 对于高divergence的数据集，需要审查是否存在越狱攻击或安全机制失效。

### 数据集风险评估

**高风险数据集** (Harmful Rate > 10%):
- gandalf_ignore_instructions: 41%
- prompt_injection: 19%
- physical_safety_instructions_unsafe: 16%
- librai_adv_deep_inception: 13%

这些数据集应该是重点关注和改进的目标。

## 💡 使用场景

### 1. 模型安全评估
```bash
# 运行分析
python3 analyze_harmful_checks.py

# 查看summary
cat harmful_check_analysis/summary_report.txt

# 重点关注高风险数据集
```

### 2. 不一致记录审查
```bash
# 查看所有不一致
open harmful_check_analysis/inconsistent_records.csv

# 或查看JSON详情
cat harmful_check_analysis/inconsistent_records_detailed.json | jq '.[0]'
```

### 3. Thinking vs Response 分析
```bash
# 查看divergence数据
open harmful_check_analysis/thinking_vs_response.csv

# 或查看可视化
open harmful_check_analysis/thinking_vs_response_comparison.png
```

### 4. 完整可视化分析
```bash
# 打开交互式HTML报告
open harmful_check_analysis/harmful_check_report.html
```

## 📈 与对比分析工具的关系

本工具是 `compare_evaluations.py` 的**补充**，专注于：
- **Harmful Check 的深度分析** (vs 简单对比)
- **记录级别的不一致检测** (vs 数据集级别统计)
- **Thinking vs Response 的专项分析** (新功能)

使用建议：
1. 先运行 `compare_evaluations.py` 了解整体对比
2. 再运行 `analyze_harmful_checks.py` 深入分析 Harmful Check 数据
3. 结合两个报告全面评估模型安全性

## 🔧 技术细节

### 记录匹配策略
- **方法**: 基于位置的匹配（position-based matching）
- **验证**: 通过 seed 字段验证对齐正确性
- **优势**: 简单、可靠、高效

### 数据处理
- 自动处理字符串/布尔值类型差异
- 处理缺失数据和错误记录
- 支持不同格式的输出（CSV, JSON, TXT, HTML）

### 可视化技术
- 使用 matplotlib 和 seaborn
- 支持中文字体（Arial Unicode MS, SimHei）
- 高分辨率输出（300 DPI）

## 🐛 常见问题

**Q: 为什么inconsistencies数量与单独统计的harmful数量不同？**
A: Inconsistencies只统计Eval和HC判断**不一致**的记录。两者都认为harmful或都认为safe的记录不计入inconsistencies。

**Q: Thinking harmful和Response harmful有什么区别？**
A:
- Thinking harmful: 模型在`<think_fast>`标签内的思考过程包含有害内容
- Response harmful: 模型的最终输出（用户可见部分）包含有害内容

**Q: Divergence rate如何计算？**
A: `(thinking_only_harmful + response_only_harmful) / total * 100`
- 只有thinking harmful但response safe的数量
- 加上只有response harmful但thinking safe的数量
- 除以总样本数

**Q: 如何找到特定数据集的不一致记录？**
A:
```bash
# 在CSV中搜索
grep "gandalf_ignore_instructions" harmful_check_analysis/inconsistent_records.csv

# 或在HTML报告的Inconsistencies标签页使用搜索框
```

## 📝 后续改进建议

1. **Case Study**: 对高不一致数据集进行详细的case study
2. **Root Cause Analysis**: 分析不一致的根本原因
3. **自动化修复建议**: 基于不一致模式提供改进建议
4. **时间序列分析**: 如果有多次评估，可以追踪变化趋势

## 📧 问题反馈

如果有任何问题或建议，请创建issue或联系开发团队。

---

**生成工具版本**: v1.0
**最后更新**: 2025-11-28
