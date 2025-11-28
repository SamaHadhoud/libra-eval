# Evaluation Comparison Analysis

这是一个用于对比分析两个版本evaluation结果的工具集。

## 📊 数据来源

- **Eval Response**: `outputs/evaluations/` - 侧重于风险类型分类和基本有害性判断
- **Harmful Check**: `eval_outputs/harmful_checks/` - 提供详细的安全分析，包括思考过程和最终响应的独立评估

## 🎯 主要发现

### 整体统计
- **总数据集**: 68个
- **总样本数**: 12,675条

### Eval Response vs Harmful Check

| 指标 | Eval Response | Harmful Check |
|------|---------------|---------------|
| **Harmful Rate** | 1.47% (186/12,675) | 3.53% (447/12,675) |
| **Safe Rate** | 78.05% (9,893/12,675) | 96.47% (12,228/12,675) |
| **特殊分析** | - | Thinking Harmful: 2.07%<br>Response Harmful: 2.49% |
| **Safety Compliance** | - | 83.86% |

### 关键发现

1. **Harmful Check检测到更多潜在有害内容** (3.53% vs 1.47%)
   - 这说明Harmful Check提供了更细致的安全分析
   - 能够识别Eval Response可能遗漏的安全问题

2. **Thinking Process vs Final Response**
   - Thinking Process Harmful: 2.07%
   - Final Response Harmful: 2.49%
   - 说明模型在思考过程中可能有有害倾向，但最终响应可能更加有害

3. **高风险数据集识别**

   **Eval Response Top 3:**
   - librai_adv_few_shots: 30.50%
   - sorry_bench: 13.50%
   - librai_adv_refusal_suppression: 7.50%

   **Harmful Check Top 3:**
   - gandalf_ignore_instructions: 41.00%
   - prompt_injection: 19.00%
   - physical_safety_instructions_unsafe: 16.00%

4. **主要风险类型**
   - Privacy (隐私): 1,044次
   - Criminal Activities (犯罪活动): 877次
   - Hate/Toxicity (仇恨/毒性): 844次
   - Violence & Extremism (暴力与极端主义): 815次

5. **主要危害类别**
   - Discrimination (歧视): 1,334次
   - Illegal (非法): 1,291次
   - Privacy (隐私): 1,131次
   - Violence (暴力): 774次

## 🛠️ 使用方法

### 1. 运行对比分析

```bash
python3 compare_evaluations.py
```

这将生成以下文件：
- `comparison_results/comparison_table.csv` - 完整对比数据表
- `comparison_results/comparison_summary.txt` - 文本格式汇总报告
- `comparison_results/*.png` - 各种可视化图表

### 2. 生成HTML交互式报告

```bash
python3 generate_html_report.py
```

这将生成：
- `comparison_results/comparison_report.html` - 交互式HTML报告

### 3. 查看结果

**方式1: 在浏览器中打开HTML报告**
```bash
open comparison_results/comparison_report.html
```

**方式2: 查看CSV数据**
```bash
# 使用Excel、Numbers或任何表格软件打开
open comparison_results/comparison_table.csv
```

**方式3: 查看文本报告**
```bash
cat comparison_results/comparison_summary.txt
```

**方式4: 查看可视化图表**
```bash
open comparison_results/
```

## 📈 生成的文件说明

### CSV文件
- **comparison_table.csv**: 包含每个数据集的详细对比指标
  - Total_Eval / Total_HarmfulCheck: 样本总数
  - Eval_Harmful / HC_Harmful: 有害样本数
  - Eval_Safe / HC_Safe: 安全样本数
  - HC_Thinking_Harmful: 思考过程有害的样本数
  - HC_Response_Harmful: 最终响应有害的样本数
  - HC_Safety_Compliant: 符合安全规范的样本数
  - Eval_Harmful_Rate / HC_Harmful_Rate: 有害率百分比

### 可视化图表

1. **harmful_rate_comparison.png**: 对比两种评估方法的有害率
2. **risk_type_distribution.png**: Eval Response的风险类型分布
3. **harm_categories_distribution.png**: Harmful Check的危害类别分布
4. **severity_distribution.png**: 严重程度分布
5. **thinking_vs_response_harmful.png**: 思考过程 vs 最终响应的有害率对比

### HTML报告

交互式报告包含5个标签页：
1. **Overview**: 整体统计和关键发现
2. **Comparison**: 详细的数据集对比
3. **Visualizations**: 所有可视化图表
4. **Data Table**: 可搜索的完整数据表
5. **Summary**: 完整的文本报告

## 💡 解读建议

### 如何理解两个版本的差异？

1. **Eval Response (eval_response)**
   - 提供风险类型分类 (risk_type_index)
   - 给出简单的有害/安全判断 (is_harmful)
   - 包含分析说明 (analysis)

2. **Harmful Check (harmful_check)**
   - 分析思考过程是否有害 (thinking_process_analysis)
   - 分析最终响应是否有害 (final_response_analysis)
   - 检查安全合规性 (safety_compliance)
   - 提供严重程度评级 (severity)
   - 列出具体危害类别 (harm_categories)

### 两个版本各有什么优势？

**Eval Response的优势:**
- 提供结构化的风险分类
- 适合快速筛选和分类
- 有明确的风险类型标签

**Harmful Check的优势:**
- 更详细的安全分析
- 区分思考过程和最终输出
- 提供多维度的安全评估
- 能捕捉更多潜在的安全问题

### 如何使用这些结果？

1. **识别高风险数据集**: 关注harmful rate较高的数据集
2. **优化模型安全性**: 分析thinking process和final response的差异
3. **改进评估策略**: 对比两种方法的差异，找到互补点
4. **数据集质量评估**: 了解每个数据集的风险分布

## 🔧 自定义分析

如果需要自定义分析，可以修改 `compare_evaluations.py` 中的分析函数：

```python
# 添加新的统计指标
def analyze_custom_metric(self, dataset_name: str) -> Dict:
    # 你的自定义分析逻辑
    pass
```

## 📝 注意事项

1. 确保两个目录的数据集名称一致
2. 确保已安装必要的依赖: `matplotlib`, `seaborn`, `pandas`
3. 如果数据集很大，分析可能需要一些时间
4. HTML报告需要在浏览器中打开，图片路径是相对路径

## 🤝 建议的后续工作

1. **深入分析特定数据集**: 对harmful rate异常高的数据集进行case study
2. **改进评估方法**: 结合两种方法的优势，开发更全面的评估策略
3. **模型改进**: 根据分析结果，针对性地改进模型的安全性
4. **benchmark建立**: 使用这些数据建立安全评估的baseline

## 📧 问题反馈

如果有任何问题或建议，请创建issue或联系开发团队。
