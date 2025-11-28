# 有害性检查分析LaTeX报告使用指南

本目录包含从有害性检查分析结果生成的完整LaTeX技术报告，适配IEEE/ACM会议双栏格式，使用专业的中文学术写作风格。

## 📁 文件结构

```
latex_output/
├── harmful_check_latex_report.tex  # 主文档（完整报告）
├── key_statistics.txt              # 关键统计数据摘要
├── terminology.txt                 # 中英文术语对照表
├── tables/                         # 独立表格文件
│   ├── table1_inconsistency_top10.tex
│   ├── table2_divergence_top10.tex
│   ├── table3_harm_categories.tex
│   ├── table4_safety_by_risk.tex
│   └── table5_safety_by_category.tex
└── figures/                        # 独立图表环境
    ├── figure1.tex  (不一致类型饼图)
    ├── figure2.tex  (Eval vs HC散点图)
    ├── figure3.tex  (思考响应对比)
    ├── figure4.tex  (不一致性热力图)
    ├── figure5.tex  (危害类别分布)
    └── figure6.tex  (安全率可视化)
```

## 🚀 快速开始

### 方式1：使用完整文档

**推荐用于快速集成**

1. 打开您的IEEE/ACM会议论文LaTeX模板
2. 复制 `harmful_check_latex_report.tex` 的内容
3. 粘贴到您的主文档中（在 `\begin{document}` 和 `\end{document}` 之间）
4. 确保 `harmful_check_analysis/` 图片文件夹与LaTeX文档在同一目录
5. 编译文档（推荐使用XeLaTeX）

### 方式2：使用独立表格和图表

**推荐用于灵活定制**

您可以单独引入需要的表格或图表：

```latex
% 在您的文档中引入特定表格
\input{tables/table1_inconsistency_top10.tex}

% 或引入特定图表
\input{figures/figure3.tex}
```

## 📦 所需LaTeX宏包

确保您的LaTeX文档包含以下宏包：

```latex
\usepackage{booktabs}      % 专业表格线条
\usepackage{graphicx}      % 插入图片
\usepackage{xcolor}        % 颜色标注
\usepackage{siunitx}       % 数字格式化
\usepackage{ctex}          % 中文支持（推荐）
% 或者
\usepackage{CJK}           % 中文支持（传统方案）
```

**注意**：大多数IEEE/ACM模板已包含 `booktabs` 和 `graphicx`，请检查避免重复。

## 🔧 编译方法

### 使用XeLaTeX（推荐）

XeLaTeX对中文支持最好，推荐使用：

```bash
xelatex your_document.tex
xelatex your_document.tex  # 运行两次以生成交叉引用
```

### 使用PDFLaTeX + CJK

如果必须使用PDFLaTeX：

```bash
pdflatex your_document.tex
pdflatex your_document.tex
```

确保使用 `\usepackage{CJK}` 并添加：
```latex
\begin{CJK}{UTF8}{gbsn}
% 文档内容
\end{CJK}
```

## 📊 内容结构

生成的报告包含以下章节：

1. **摘要** - 研究发现的高层次概述
2. **引言** - 背景、研究动机和主要贡献
3. **方法论** - 数据集、评估流程和分析维度
4. **实验结果** - 5个子章节
   - 整体统计数据
   - 不一致性分析
   - 思考与响应差异
   - 危害类别分布
   - 安全率分析
5. **讨论** - 关键发现的解释和安全改进建议
6. **结论** - 总结和未来工作方向

### 表格列表

| 表格 | 标签 | 内容 | 格式 |
|-----|------|------|------|
| 表1 | `tab:inconsistency_top10` | 不一致记录Top 10数据集 | 单栏 |
| 表2 | `tab:divergence_top10` | 思考响应差异Top 10 | 单栏 |
| 表3 | `tab:harm_categories` | 主要危害类别Top 15 | 跨栏 |
| 表4 | `tab:safety_by_risk` | 按风险类型安全率 | 跨栏 |
| 表5 | `tab:safety_by_category` | 按类别安全率（最低10项） | 单栏 |

### 图表列表

| 图表 | 标签 | 内容 | 格式 |
|-----|------|------|------|
| 图1 | `fig:inconsistency_pie` | 不一致类型饼图 | 单栏 |
| 图2 | `fig:eval_hc_scatter` | Eval vs HC散点图 | 单栏 |
| 图3 | `fig:thinking_response_comparison` | 思考响应对比柱状图 | 跨栏 |
| 图4 | `fig:inconsistency_heatmap` | 不一致性热力图 | 跨栏 |
| 图5 | `fig:harm_categories_dist` | 危害类别分布 | 跨栏 |
| 图6 | `fig:safety_by_category_vis` | 安全率可视化 | 跨栏 |

## 🎨 自定义和修改

### 修改表格

所有表格都使用 `booktabs` 宏包的专业样式。如果需要修改：

1. 打开 `tables/` 目录中的对应文件
2. 修改表格内容或格式
3. 重新编译文档

### 修改图表尺寸

图表尺寸可以通过修改 `\includegraphics` 的 `width` 参数调整：

```latex
% 单栏图表
\includegraphics[width=\columnwidth]{...}

% 跨栏图表 (可调整系数)
\includegraphics[width=0.8\textwidth]{...}  % 80%宽度
\includegraphics[width=0.9\textwidth]{...}  % 90%宽度
```

### 修改中文表述

所有中文文本都可以直接编辑。主要章节内容在 `harmful_check_latex_report.tex` 中，使用任何文本编辑器即可修改。

## 📌 交叉引用

文档中包含完整的交叉引用系统。在正文中可以这样引用：

```latex
如表\ref{tab:inconsistency_top10}所示，...
如图\ref{fig:thinking_response_comparison}所示，...
```

## 🔍 关键数据快速查找

使用 `key_statistics.txt` 可以快速查找关键统计数字：

- 整体有害率: 3.75%
- 不一致记录总数: 371条
- gandalf_ignore_instructions差异率: 37.00%
- security类别安全率: 23.64% (最低)

## 📖 术语对照

`terminology.txt` 提供了完整的危害类别和风险类型中英文对照，确保文档中术语使用一致。

## ⚠️ 常见问题

### Q1: 编译时找不到图片文件？

**A**: 确保 `harmful_check_analysis/` 文件夹与LaTeX文档在同一目录。图片路径是相对路径。

### Q2: 中文显示为乱码或方框？

**A**:
- 使用XeLaTeX编译器（推荐）
- 确保包含了 `\usepackage{ctex}`
- 检查LaTeX编辑器的文件编码设置为UTF-8

### Q3: 表格太宽，超出单栏宽度？

**A**:
- 使用 `\small` 或 `\footnotesize` 缩小字体
- 调整列宽或列数
- 考虑使用跨栏表格 `table*` 环境

### Q4: 如何只使用部分表格或图表？

**A**: 使用 `\input{}` 命令引入需要的文件，例如：
```latex
\input{tables/table1_inconsistency_top10.tex}
```

### Q5: 参考文献如何添加？

**A**: 文档末尾提供了参考文献模板。根据您使用的参考文献管理方式（BibTeX或手动）进行修改：

```latex
\bibitem{ref1}
作者名. 大型语言模型安全性研究综述. 期刊名, 2024.
```

## 📧 技术支持

如果遇到问题：
1. 检查LaTeX编译错误日志
2. 确认所有宏包已安装
3. 验证图片文件路径正确
4. 尝试使用XeLaTeX重新编译

## 📝 引用格式

如果您在论文中使用了本分析报告的内容，建议引用格式：

```
有害性检查分析技术报告, 大型语言模型安全性评估, 2025.
```

---

**生成日期**: 2025-11-28
**版本**: 1.0
**兼容格式**: IEEE/ACM会议双栏格式
**语言**: 中文学术写作风格
