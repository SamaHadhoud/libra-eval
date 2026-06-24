#!/usr/bin/env python3
"""
Harmful Check Analysis Tool
专门分析harmful_check数据，包括：
A tool dedicated to analyzing harmful_check data, including:
1. Thinking vs Response差异分析
1. Thinking vs Response divergence analysis
2. 每个数据集的详细表现
2. Detailed performance for each dataset
3. 与eval_response的is_harmful判断不一致的记录识别
3. Identification of records inconsistent with the is_harmful judgment of eval_response
"""

import json
from pathlib import Path
from collections import Counter
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Tuple
import argparse

# 设置中文字体和样式
# Set the Chinese font and style
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False
sns.set_style("whitegrid")
sns.set_palette("husl")


class HarmfulCheckAnalyzer:
    def __init__(self, eval_dir: str, harmful_check_dir: str):
        self.eval_dir = Path(eval_dir)
        self.harmful_check_dir = Path(harmful_check_dir)
        self.eval_data = {}
        self.harmful_check_data = {}
        self.inconsistencies = []
        self.thinking_vs_response_data = []

    def load_jsonl(self, file_path: Path) -> List[Dict]:
        """加载JSONL文件
        Load a JSONL file"""
        data = []
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    data.append(json.loads(line.strip()))
                except json.JSONDecodeError:
                    continue
        return data

    def load_all_data(self):
        """加载所有数据
        Load all data"""
        print("Loading evaluation data...")
        for file in self.eval_dir.glob("*.jsonl"):
            dataset_name = file.stem.replace("_200_K2-Plus-Instruct", "")
            self.eval_data[dataset_name] = self.load_jsonl(file)

        print("Loading harmful check data...")
        for file in self.harmful_check_dir.glob("*.jsonl"):
            dataset_name = file.stem.replace("_200_K2-Plus-Instruct", "")
            self.harmful_check_data[dataset_name] = self.load_jsonl(file)

        print(f"Loaded {len(self.eval_data)} evaluation datasets")
        print(f"Loaded {len(self.harmful_check_data)} harmful check datasets")

    def match_records_and_detect_inconsistencies(self):
        """匹配记录并检测不一致
        Match records and detect inconsistencies"""
        print("\nDetecting inconsistencies between Eval and Harmful Check...")

        for dataset_name in sorted(self.eval_data.keys()):
            if dataset_name not in self.harmful_check_data:
                continue

            eval_records = self.eval_data[dataset_name]
            hc_records = self.harmful_check_data[dataset_name]

            if len(eval_records) != len(hc_records):
                print(f"Warning: {dataset_name} has different record counts")
                continue

            for i, (eval_rec, hc_rec) in enumerate(zip(eval_records, hc_records)):
                # 提取is_harmful标志
                # Extract the is_harmful flag
                eval_resp = eval_rec.get('eval_response', {})
                if not isinstance(eval_resp, dict):
                    continue

                eval_harmful = eval_resp.get('is_harmful')

                # 处理字符串和布尔值
                # Handle string and boolean values
                if isinstance(eval_harmful, str):
                    eval_harmful = eval_harmful.lower() == 'true'

                # 获取harmful_check数据
                # Get the harmful_check data
                hc = hc_rec.get('harmful_check', {})
                if not isinstance(hc, dict):
                    continue

                hc_harmful = hc.get('overall_is_harmful')

                # 检测不一致
                # Detect inconsistency
                if eval_harmful is not None and hc_harmful is not None:
                    if eval_harmful != hc_harmful:
                        # 记录不一致
                        # Record the inconsistency
                        inconsistency = {
                            'dataset': dataset_name,
                            'index': i,
                            'seed': eval_rec.get('seed', ''),
                            'eval_is_harmful': eval_harmful,
                            'hc_overall_is_harmful': hc_harmful,
                            'hc_thinking_harmful': hc.get('thinking_process_analysis', {}).get('is_harmful', False),
                            'hc_response_harmful': hc.get('final_response_analysis', {}).get('is_harmful', False),
                            'eval_risk_type': eval_resp.get('risk_type_index', 'unknown'),
                            'hc_harm_categories': hc.get('harm_categories', []),
                            'hc_severity': hc.get('severity', 'unknown'),
                            'response_excerpt': hc_rec.get('response', '')[:200],
                            'hc_summary': hc.get('summary', ''),
                            'hc_thinking_reasoning': hc.get('thinking_process_analysis', {}).get('reasoning', ''),
                            'hc_response_reasoning': hc.get('final_response_analysis', {}).get('reasoning', '')
                        }
                        self.inconsistencies.append(inconsistency)

        print(f"Found {len(self.inconsistencies)} inconsistent records")

    def analyze_thinking_vs_response(self):
        """分析Thinking Process vs Final Response的差异
        Analyze the divergence between Thinking Process and Final Response"""
        print("\nAnalyzing Thinking vs Response divergence...")

        for dataset_name in sorted(self.harmful_check_data.keys()):
            hc_records = self.harmful_check_data[dataset_name]

            stats = {
                'dataset': dataset_name,
                'total': len(hc_records),
                'thinking_harmful': 0,
                'response_harmful': 0,
                'both_harmful': 0,
                'divergence_thinking_only': 0,  # 只有thinking harmful | Only thinking is harmful
                'divergence_response_only': 0,  # 只有response harmful | Only response is harmful
                'divergence_rate': 0.0
            }

            for rec in hc_records:
                hc = rec.get('harmful_check', {})
                if not isinstance(hc, dict):
                    continue

                thinking_harmful = hc.get('thinking_process_analysis', {}).get('is_harmful', False)
                response_harmful = hc.get('final_response_analysis', {}).get('is_harmful', False)

                if thinking_harmful:
                    stats['thinking_harmful'] += 1
                if response_harmful:
                    stats['response_harmful'] += 1
                if thinking_harmful and response_harmful:
                    stats['both_harmful'] += 1

                # 检测divergence
                # Detect divergence
                if thinking_harmful and not response_harmful:
                    stats['divergence_thinking_only'] += 1
                elif response_harmful and not thinking_harmful:
                    stats['divergence_response_only'] += 1

            # 计算divergence rate
            # Compute the divergence rate
            total_divergence = stats['divergence_thinking_only'] + stats['divergence_response_only']
            if stats['total'] > 0:
                stats['divergence_rate'] = (total_divergence / stats['total']) * 100

            self.thinking_vs_response_data.append(stats)

        print(f"Analyzed {len(self.thinking_vs_response_data)} datasets for thinking vs response divergence")

    def analyze_per_dataset(self) -> pd.DataFrame:
        """生成每个数据集的详细分析
        Generate a detailed analysis for each dataset"""
        print("\nGenerating per-dataset analysis...")

        results = []

        for dataset_name in sorted(self.harmful_check_data.keys()):
            hc_records = self.harmful_check_data[dataset_name]

            stats = {
                'dataset': dataset_name,
                'total': len(hc_records),
                'overall_harmful': 0,
                'overall_safe': 0,
                'thinking_harmful': 0,
                'response_harmful': 0,
                'safety_compliant': 0,
                'severity_low': 0,
                'severity_medium': 0,
                'severity_high': 0,
                'severity_critical': 0,
                'harm_categories': Counter()
            }

            for rec in hc_records:
                hc = rec.get('harmful_check', {})
                if not isinstance(hc, dict):
                    continue

                # Overall harmful
                if hc.get('overall_is_harmful'):
                    stats['overall_harmful'] += 1
                else:
                    stats['overall_safe'] += 1

                # Thinking/Response harmful
                if hc.get('thinking_process_analysis', {}).get('is_harmful'):
                    stats['thinking_harmful'] += 1
                if hc.get('final_response_analysis', {}).get('is_harmful'):
                    stats['response_harmful'] += 1

                # Safety compliance
                if hc.get('safety_compliance', {}).get('follows_system_instructions'):
                    stats['safety_compliant'] += 1

                # Severity
                severity = hc.get('severity', '').lower()
                if severity == 'low':
                    stats['severity_low'] += 1
                elif severity == 'medium':
                    stats['severity_medium'] += 1
                elif severity == 'high':
                    stats['severity_high'] += 1
                elif severity == 'critical':
                    stats['severity_critical'] += 1

                # Harm categories
                for cat in hc.get('harm_categories', []):
                    stats['harm_categories'][cat] += 1

            # 计算百分比
            # Compute percentages
            if stats['total'] > 0:
                stats['harmful_rate'] = f"{stats['overall_harmful'] / stats['total'] * 100:.2f}%"
                stats['thinking_harmful_rate'] = f"{stats['thinking_harmful'] / stats['total'] * 100:.2f}%"
                stats['response_harmful_rate'] = f"{stats['response_harmful'] / stats['total'] * 100:.2f}%"
                stats['safety_compliance_rate'] = f"{stats['safety_compliant'] / stats['total'] * 100:.2f}%"
            else:
                stats['harmful_rate'] = "N/A"
                stats['thinking_harmful_rate'] = "N/A"
                stats['response_harmful_rate'] = "N/A"
                stats['safety_compliance_rate'] = "N/A"

            # Top害类别（转换为字符串）
            # Top harm categories (converted to a string)
            top_categories = stats['harm_categories'].most_common(3)
            stats['top_harm_categories'] = ', '.join([f"{cat}({count})" for cat, count in top_categories])

            # 移除Counter对象以便导出CSV
            # Remove the Counter object so it can be exported to CSV
            del stats['harm_categories']

            results.append(stats)

        return pd.DataFrame(results)

    def _normalize_harm_category(self, category: str) -> str:
        """清洗harm_category字符串
        Clean up the harm_category string"""
        import re

        if not category:
            return "unknown"

        # 移除括号及内容
        # Remove parentheses and their content
        cleaned = re.sub(r'\s*\([^)]*\)', '', category)

        # 转小写并去除前后空格
        # Convert to lowercase and strip leading/trailing whitespace
        cleaned = cleaned.strip().lower()

        # 处理常见变体
        # Handle common variants
        replacements = {
            'illegal_activities': 'illegal',
            'illegal_activity': 'illegal',
            'illegal activities': 'illegal',
            'discrimination/bias': 'discrimination',
            'hate_speech_attempted': 'hate_speech',
            'sexual_content': 'sexual',
        }

        return replacements.get(cleaned, cleaned)

    def analyze_safety_rate_by_risk_type(self) -> pd.DataFrame:
        """计算每个risk_type的安全率
        Compute the safety rate for each risk_type"""
        from collections import defaultdict

        # 统计数据：{risk_type: {'total': N, 'safe': M}}
        # Statistics: {risk_type: {'total': N, 'safe': M}}
        stats = defaultdict(lambda: {'total': 0, 'safe': 0})

        # 遍历所有数据集
        # Iterate over all datasets
        for dataset_name in sorted(self.eval_data.keys()):
            if dataset_name not in self.harmful_check_data:
                continue

            eval_records = self.eval_data[dataset_name]
            hc_records = self.harmful_check_data[dataset_name]

            if len(eval_records) != len(hc_records):
                print(f"Warning: {dataset_name} record count mismatch")
                continue

            # 遍历每条记录
            # Iterate over each record
            for eval_rec, hc_rec in zip(eval_records, hc_records):
                # 获取risk_type
                # Get the risk_type
                eval_resp = eval_rec.get('eval_response', {})
                if not isinstance(eval_resp, dict):
                    continue

                risk_type = eval_resp.get('risk_type_index', 'unknown')

                # 跳过"none"和"unknown"分类
                # Skip the "none" and "unknown" categories
                if risk_type.lower() in ['none', 'unknown']:
                    continue

                # 获取安全标志
                # Get the safety flag
                hc = hc_rec.get('harmful_check', {})
                if not isinstance(hc, dict):
                    continue

                is_harmful = hc.get('overall_is_harmful', False)

                # 更新统计
                # Update statistics
                stats[risk_type]['total'] += 1
                if not is_harmful:
                    stats[risk_type]['safe'] += 1

        # 转换为DataFrame
        # Convert to a DataFrame
        results = []
        for risk_type, data in sorted(stats.items()):
            total = data['total']
            safe = data['safe']
            harmful = total - safe
            safety_rate = (safe / total * 100) if total > 0 else 0

            results.append({
                'risk_type': risk_type,
                'total_samples': total,
                'safe_samples': safe,
                'harmful_samples': harmful,
                'safety_rate': f"{safety_rate:.2f}%",
                'safety_rate_numeric': safety_rate  # 用于排序和绘图 | Used for sorting and plotting
            })

        df = pd.DataFrame(results)
        df = df.sort_values('safety_rate_numeric', ascending=False)

        return df

    def analyze_safety_rate_by_risk_type_eval_version(self) -> pd.DataFrame:
        """计算每个risk_type的安全率 - 使用 eval_response.is_harmful
        Compute the safety rate for each risk_type - using eval_response.is_harmful"""
        from collections import defaultdict

        # 统计数据：{risk_type: {'total': N, 'safe': M}}
        # Statistics: {risk_type: {'total': N, 'safe': M}}
        stats = defaultdict(lambda: {'total': 0, 'safe': 0})

        # 遍历所有数据集
        # Iterate over all datasets
        for dataset_name in sorted(self.eval_data.keys()):
            eval_records = self.eval_data[dataset_name]

            # 遍历每条记录
            # Iterate over each record
            for eval_rec in eval_records:
                # 获取risk_type
                # Get the risk_type
                eval_resp = eval_rec.get('eval_response', {})
                if not isinstance(eval_resp, dict):
                    continue

                risk_type = eval_resp.get('risk_type_index', 'unknown')

                # 跳过"none"和"unknown"分类
                # Skip the "none" and "unknown" categories
                if risk_type.lower() in ['none', 'unknown']:
                    continue

                # 获取安全标志（使用 eval_response 的判断）
                # Get the safety flag (using the judgment of eval_response)
                is_harmful = eval_resp.get('is_harmful', False)

                # 处理字符串形式的布尔值
                # Handle boolean values in string form
                if isinstance(is_harmful, str):
                    is_harmful = is_harmful.lower() == 'true'

                # 更新统计
                # Update statistics
                stats[risk_type]['total'] += 1
                if not is_harmful:
                    stats[risk_type]['safe'] += 1

        # 转换为DataFrame（与原函数相同的格式）
        # Convert to a DataFrame (same format as the original function)
        results = []
        for risk_type, data in sorted(stats.items()):
            total = data['total']
            safe = data['safe']
            harmful = total - safe
            safety_rate = (safe / total * 100) if total > 0 else 0

            results.append({
                'risk_type': risk_type,
                'total_samples': total,
                'safe_samples': safe,
                'harmful_samples': harmful,
                'safety_rate': f"{safety_rate:.2f}%",
                'safety_rate_numeric': safety_rate
            })

        df = pd.DataFrame(results)
        df = df.sort_values('safety_rate_numeric', ascending=False)

        return df

    def analyze_safety_rate_by_harm_category(self, top_n: int = 30) -> pd.DataFrame:
        """计算每个harm_category的安全率
        Compute the safety rate for each harm_category"""
        from collections import defaultdict

        # 统计数据：{category: {'total': N, 'safe': M}}
        # Statistics: {category: {'total': N, 'safe': M}}
        stats = defaultdict(lambda: {'total': 0, 'safe': 0})

        # 遍历所有harmful_check数据
        # Iterate over all harmful_check data
        for dataset_name in self.harmful_check_data.keys():
            hc_records = self.harmful_check_data[dataset_name]

            for rec in hc_records:
                hc = rec.get('harmful_check', {})
                if not isinstance(hc, dict):
                    continue

                # 获取harm_categories（数组）
                # Get harm_categories (an array)
                categories = hc.get('harm_categories', [])
                if not categories:
                    # 如果没有分类，标记为"uncategorized"
                    # If there is no category, mark it as "uncategorized"
                    categories = ['uncategorized']

                # 获取安全标志
                # Get the safety flag
                is_harmful = hc.get('overall_is_harmful', False)

                # 为每个分类更新统计
                # Update statistics for each category
                for raw_category in categories:
                    # 归一化分类名称
                    # Normalize the category name
                    category = self._normalize_harm_category(raw_category)

                    # 跳过"none"和"uncategorized"分类
                    # Skip the "none" and "uncategorized" categories
                    if category.lower() in ['none', 'uncategorized', 'unknown']:
                        continue

                    stats[category]['total'] += 1
                    if not is_harmful:
                        stats[category]['safe'] += 1

        # 按总数排序，取Top N
        # Sort by total count and take the Top N
        sorted_categories = sorted(stats.items(),
                                  key=lambda x: x[1]['total'],
                                  reverse=True)[:top_n]

        # 转换为DataFrame
        # Convert to a DataFrame
        results = []
        for category, data in sorted_categories:
            total = data['total']
            safe = data['safe']
            harmful = total - safe
            safety_rate = (safe / total * 100) if total > 0 else 0

            results.append({
                'harm_category': category,
                'total_samples': total,
                'safe_samples': safe,
                'harmful_samples': harmful,
                'safety_rate': f"{safety_rate:.2f}%",
                'safety_rate_numeric': safety_rate
            })

        df = pd.DataFrame(results)
        df = df.sort_values('safety_rate_numeric', ascending=False)

        return df

    def generate_visualizations(self, output_dir: Path):
        """生成所有可视化图表
        Generate all visualization charts"""
        print("\nGenerating visualizations...")

        # 1. Thinking vs Response Comparison
        self._plot_thinking_vs_response(output_dir)

        # 2. Inconsistency Heatmap
        self._plot_inconsistency_heatmap(output_dir)

        # 3. Eval vs HC Scatter
        self._plot_eval_vs_hc_scatter(output_dir)

        # 4. Severity by Dataset
        self._plot_severity_by_dataset(output_dir)

        # 5. Harm Categories Distribution
        self._plot_harm_categories(output_dir)

        # 6. Inconsistency Types Pie Chart
        self._plot_inconsistency_types(output_dir)

        # 7. Safety Rate by Risk Type
        self._plot_safety_rate_by_risk_type(output_dir)

        # 8. Safety Rate by Harm Category
        self._plot_safety_rate_by_harm_category(output_dir)

    def _plot_thinking_vs_response(self, output_dir: Path):
        """Thinking vs Response对比图
        Thinking vs Response comparison chart"""
        if not self.thinking_vs_response_data:
            return

        df = pd.DataFrame(self.thinking_vs_response_data)
        df = df.sort_values('divergence_rate', ascending=False).head(30)

        fig, ax = plt.subplots(figsize=(16, 10))

        x = range(len(df))
        width = 0.35

        thinking_rates = (df['thinking_harmful'] / df['total'] * 100).values
        response_rates = (df['response_harmful'] / df['total'] * 100).values

        bars1 = ax.bar([i - width/2 for i in x], thinking_rates, width,
                       label='Thinking Harmful', alpha=0.8, color='lightcoral')
        bars2 = ax.bar([i + width/2 for i in x], response_rates, width,
                       label='Final Response Harmful', alpha=0.8, color='darkred')

        ax.set_xlabel('Dataset', fontsize=12, fontweight='bold')
        ax.set_ylabel('Harmful Rate (%)', fontsize=12, fontweight='bold')
        ax.set_title('Thinking Process vs Final Response Harmful Rate (Top 30 by Divergence)',
                     fontsize=14, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(df['dataset'].values, rotation=90, ha='right')
        ax.legend()
        ax.grid(axis='y', alpha=0.3)

        plt.tight_layout()
        plt.savefig(output_dir / 'thinking_vs_response_comparison.png', dpi=300, bbox_inches='tight')
        plt.close()
        print(f"  ✓ Saved: thinking_vs_response_comparison.png")

    def _plot_inconsistency_heatmap(self, output_dir: Path):
        """不一致性热力图
        Inconsistency heatmap"""
        if not self.inconsistencies:
            print("  ⚠ No inconsistencies to plot")
            return

        # 统计每个数据集的不一致类型
        # Count the inconsistency types for each dataset
        datasets = list(set(inc['dataset'] for inc in self.inconsistencies))
        datasets.sort()

        eval_pos_hc_neg = []  # Eval harmful, HC safe
        eval_neg_hc_pos = []  # Eval safe, HC harmful

        for dataset in datasets:
            ep_hn = sum(1 for inc in self.inconsistencies
                       if inc['dataset'] == dataset and inc['eval_is_harmful'] and not inc['hc_overall_is_harmful'])
            en_hp = sum(1 for inc in self.inconsistencies
                       if inc['dataset'] == dataset and not inc['eval_is_harmful'] and inc['hc_overall_is_harmful'])

            eval_pos_hc_neg.append(ep_hn)
            eval_neg_hc_pos.append(en_hp)

        fig, ax = plt.subplots(figsize=(16, 6))

        data = [eval_pos_hc_neg, eval_neg_hc_pos]
        im = ax.imshow(data, cmap='YlOrRd', aspect='auto')

        ax.set_xticks(range(len(datasets)))
        ax.set_yticks([0, 1])
        ax.set_xticklabels(datasets, rotation=90, ha='right')
        ax.set_yticklabels(['Eval Harmful + HC Safe', 'Eval Safe + HC Harmful'])

        plt.colorbar(im, ax=ax, label='Count')

        ax.set_title('Inconsistency Heatmap by Dataset', fontsize=14, fontweight='bold')

        plt.tight_layout()
        plt.savefig(output_dir / 'inconsistency_heatmap.png', dpi=300, bbox_inches='tight')
        plt.close()
        print(f"  ✓ Saved: inconsistency_heatmap.png")

    def _plot_eval_vs_hc_scatter(self, output_dir: Path):
        """Eval vs HC散点图
        Eval vs HC scatter plot"""
        datasets = []
        eval_rates = []
        hc_rates = []

        for dataset_name in sorted(self.eval_data.keys()):
            if dataset_name not in self.harmful_check_data:
                continue

            eval_records = self.eval_data[dataset_name]
            hc_records = self.harmful_check_data[dataset_name]

            # 计算eval harmful rate
            # Compute the eval harmful rate
            eval_harmful_count = 0
            for rec in eval_records:
                eval_resp = rec.get('eval_response', {})
                if isinstance(eval_resp, dict):
                    is_harmful = eval_resp.get('is_harmful')
                    if isinstance(is_harmful, str):
                        is_harmful = is_harmful.lower() == 'true'
                    if is_harmful:
                        eval_harmful_count += 1

            # 计算hc harmful rate
            # Compute the hc harmful rate
            hc_harmful_count = sum(1 for rec in hc_records
                                  if isinstance(rec.get('harmful_check'), dict)
                                  and rec.get('harmful_check', {}).get('overall_is_harmful'))

            if len(eval_records) > 0:
                eval_rate = eval_harmful_count / len(eval_records) * 100
                hc_rate = hc_harmful_count / len(hc_records) * 100

                datasets.append(dataset_name)
                eval_rates.append(eval_rate)
                hc_rates.append(hc_rate)

        fig, ax = plt.subplots(figsize=(12, 10))

        ax.scatter(eval_rates, hc_rates, alpha=0.6, s=100, edgecolors='black', linewidth=0.5)

        # 添加对角线
        # Add the diagonal line
        max_val = max(max(eval_rates), max(hc_rates))
        ax.plot([0, max_val], [0, max_val], 'r--', alpha=0.5, label='Perfect Agreement')

        ax.set_xlabel('Eval Response Harmful Rate (%)', fontsize=12, fontweight='bold')
        ax.set_ylabel('Harmful Check Harmful Rate (%)', fontsize=12, fontweight='bold')
        ax.set_title('Eval Response vs Harmful Check Agreement', fontsize=14, fontweight='bold')
        ax.legend()
        ax.grid(alpha=0.3)

        plt.tight_layout()
        plt.savefig(output_dir / 'eval_vs_hc_scatter.png', dpi=300, bbox_inches='tight')
        plt.close()
        print(f"  ✓ Saved: eval_vs_hc_scatter.png")

    def _plot_severity_by_dataset(self, output_dir: Path):
        """按数据集的严重程度分布
        Severity distribution by dataset"""
        severity_data = []

        for dataset_name in sorted(self.harmful_check_data.keys()):
            hc_records = self.harmful_check_data[dataset_name]

            severities = {'low': 0, 'medium': 0, 'high': 0, 'critical': 0}

            for rec in hc_records:
                hc = rec.get('harmful_check', {})
                if isinstance(hc, dict):
                    severity = hc.get('severity', '').lower()
                    if severity in severities:
                        severities[severity] += 1

            total = sum(severities.values())
            if total > 0:
                severity_data.append({
                    'dataset': dataset_name,
                    **severities,
                    'total': total
                })

        # 按总数排序，取前20
        # Sort by total count and take the top 20
        severity_data.sort(key=lambda x: x['total'], reverse=True)
        severity_data = severity_data[:20]

        if not severity_data:
            print("  ⚠ No severity data to plot")
            return

        df = pd.DataFrame(severity_data)

        fig, ax = plt.subplots(figsize=(14, 8))

        bottom_low = [0] * len(df)
        bottom_medium = df['low'].values
        bottom_high = (df['low'] + df['medium']).values
        bottom_critical = (df['low'] + df['medium'] + df['high']).values

        ax.bar(df['dataset'], df['low'], label='Low', color='#90EE90')
        ax.bar(df['dataset'], df['medium'], bottom=bottom_medium, label='Medium', color='#FFD700')
        ax.bar(df['dataset'], df['high'], bottom=bottom_high, label='High', color='#FF6347')
        ax.bar(df['dataset'], df['critical'], bottom=bottom_critical, label='Critical', color='#8B0000')

        ax.set_xlabel('Dataset', fontsize=12, fontweight='bold')
        ax.set_ylabel('Count', fontsize=12, fontweight='bold')
        ax.set_title('Severity Distribution by Dataset (Top 20)', fontsize=14, fontweight='bold')
        ax.set_xticklabels(df['dataset'], rotation=90, ha='right')
        ax.legend()
        ax.grid(axis='y', alpha=0.3)

        plt.tight_layout()
        plt.savefig(output_dir / 'severity_by_dataset.png', dpi=300, bbox_inches='tight')
        plt.close()
        print(f"  ✓ Saved: severity_by_dataset.png")

    def _plot_harm_categories(self, output_dir: Path):
        """危害类别分布
        Harm category distribution"""
        all_categories = Counter()

        for dataset_name in self.harmful_check_data.keys():
            hc_records = self.harmful_check_data[dataset_name]

            for rec in hc_records:
                hc = rec.get('harmful_check', {})
                if isinstance(hc, dict):
                    for cat in hc.get('harm_categories', []):
                        all_categories[cat] += 1

        if not all_categories:
            print("  ⚠ No harm categories to plot")
            return

        categories = dict(all_categories.most_common(20))

        fig, ax = plt.subplots(figsize=(12, 8))
        bars = ax.barh(list(categories.keys()), list(categories.values()), alpha=0.8, color='coral')

        for bar in bars:
            width = bar.get_width()
            ax.text(width, bar.get_y() + bar.get_height()/2,
                   f'{int(width)}', ha='left', va='center', fontweight='bold')

        ax.set_xlabel('Count', fontsize=12, fontweight='bold')
        ax.set_ylabel('Harm Category', fontsize=12, fontweight='bold')
        ax.set_title('Top 20 Harm Categories Distribution', fontsize=14, fontweight='bold')
        ax.grid(axis='x', alpha=0.3)

        plt.tight_layout()
        plt.savefig(output_dir / 'harm_categories_distribution.png', dpi=300, bbox_inches='tight')
        plt.close()
        print(f"  ✓ Saved: harm_categories_distribution.png")

    def _plot_inconsistency_types(self, output_dir: Path):
        """不一致类型饼图
        Inconsistency type pie chart"""
        if not self.inconsistencies:
            print("  ⚠ No inconsistencies to plot")
            return

        eval_pos_hc_neg = sum(1 for inc in self.inconsistencies
                             if inc['eval_is_harmful'] and not inc['hc_overall_is_harmful'])
        eval_neg_hc_pos = sum(1 for inc in self.inconsistencies
                             if not inc['eval_is_harmful'] and inc['hc_overall_is_harmful'])

        fig, ax = plt.subplots(figsize=(10, 8))

        labels = ['Eval Harmful + HC Safe', 'Eval Safe + HC Harmful']
        sizes = [eval_pos_hc_neg, eval_neg_hc_pos]
        colors = ['#FFD700', '#FF6347']

        wedges, texts, autotexts = ax.pie(sizes, labels=labels, autopct='%1.1f%%',
                                           colors=colors, startangle=90)

        for text in texts:
            text.set_fontsize(12)
            text.set_fontweight('bold')

        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontsize(11)
            autotext.set_fontweight('bold')

        ax.set_title('Inconsistency Types Distribution', fontsize=14, fontweight='bold')

        plt.tight_layout()
        plt.savefig(output_dir / 'inconsistency_types_pie.png', dpi=300, bbox_inches='tight')
        plt.close()
        print(f"  ✓ Saved: inconsistency_types_pie.png")

    def _plot_safety_rate_by_risk_type(self, output_dir: Path):
        """可视化risk_type的安全率
        Visualize the safety rate of risk_type"""
        df = self.analyze_safety_rate_by_risk_type()

        # 过滤掉样本数太少的（<5）
        # Filter out those with too few samples (<5)
        df = df[df['total_samples'] >= 5]

        # 按安全率排序
        # Sort by safety rate
        df = df.sort_values('safety_rate_numeric', ascending=True)

        if df.empty:
            print("  ⚠ No risk_type data to plot")
            return

        fig, ax = plt.subplots(figsize=(14, 8))

        # 创建堆叠柱状图
        # Create a stacked bar chart
        x = range(len(df))
        safe = df['safe_samples'].values
        harmful = df['harmful_samples'].values
        labels = df['risk_type'].values

        bars1 = ax.barh(x, safe, label='Safe', color='#90EE90', alpha=0.8)
        bars2 = ax.barh(x, harmful, left=safe, label='Harmful',
                        color='#FF6347', alpha=0.8)

        # 添加安全率标签
        # Add safety rate labels
        for i, (s, h, rate) in enumerate(zip(safe, harmful,
                                             df['safety_rate_numeric'])):
            total = s + h
            # 在柱子中间显示安全率
            # Display the safety rate in the middle of the bar
            ax.text(total / 2, i, f'{rate:.1f}%',
                   ha='center', va='center',
                   fontweight='bold', fontsize=10)

        ax.set_yticks(x)
        ax.set_yticklabels(labels)
        ax.set_xlabel('Sample Count', fontsize=12, fontweight='bold')
        ax.set_ylabel('Risk Type', fontsize=12, fontweight='bold')
        ax.set_title('Safety Rate by Risk Type',
                    fontsize=14, fontweight='bold')
        ax.legend()
        ax.grid(axis='x', alpha=0.3)

        plt.tight_layout()
        plt.savefig(output_dir / 'safety_rate_by_risk_type.png',
                   dpi=300, bbox_inches='tight')
        plt.close()
        print(f"  ✓ Saved: safety_rate_by_risk_type.png")

    def _plot_safety_rate_by_harm_category(self, output_dir: Path):
        """可视化harm_category的安全率
        Visualize the safety rate of harm_category"""
        df = self.analyze_safety_rate_by_harm_category(top_n=25)

        # 按安全率排序（从低到高）
        # Sort by safety rate (from low to high)
        df = df.sort_values('safety_rate_numeric', ascending=True)

        if df.empty:
            print("  ⚠ No harm_category data to plot")
            return

        fig, ax = plt.subplots(figsize=(14, 10))

        # 创建颜色映射（安全率低=红色，高=绿色）
        # Create a color mapping (low safety rate = red, high = green)
        colors = []
        for rate in df['safety_rate_numeric']:
            if rate >= 95:
                colors.append('#90EE90')  # 浅绿 | Light green
            elif rate >= 90:
                colors.append('#FFD700')  # 金色 | Gold
            elif rate >= 80:
                colors.append('#FFA500')  # 橙色 | Orange
            else:
                colors.append('#FF6347')  # 红色 | Red

        bars = ax.barh(range(len(df)), df['safety_rate_numeric'],
                       color=colors, alpha=0.8, edgecolor='black', linewidth=0.5)

        # 添加数值标签
        # Add value labels
        for i, (rate, total) in enumerate(zip(df['safety_rate_numeric'],
                                              df['total_samples'])):
            ax.text(rate + 1, i, f'{rate:.1f}% (n={total})',
                   va='center', fontsize=9)

        ax.set_yticks(range(len(df)))
        ax.set_yticklabels(df['harm_category'])
        ax.set_xlabel('Safety Rate (%)', fontsize=12, fontweight='bold')
        ax.set_ylabel('Harm Category', fontsize=12, fontweight='bold')
        ax.set_title('Safety Rate by Harm Category (Top 25, Lowest First)',
                    fontsize=14, fontweight='bold')
        ax.set_xlim(0, 105)
        ax.grid(axis='x', alpha=0.3)

        # 添加颜色图例
        # Add a color legend
        from matplotlib.patches import Patch
        legend_elements = [
            Patch(facecolor='#90EE90', label='≥95%'),
            Patch(facecolor='#FFD700', label='90-95%'),
            Patch(facecolor='#FFA500', label='80-90%'),
            Patch(facecolor='#FF6347', label='<80%')
        ]
        ax.legend(handles=legend_elements, loc='lower right')

        plt.tight_layout()
        plt.savefig(output_dir / 'safety_rate_by_harm_category.png',
                   dpi=300, bbox_inches='tight')
        plt.close()
        print(f"  ✓ Saved: safety_rate_by_harm_category.png")

    def export_data(self, output_dir: Path):
        """导出数据
        Export data"""
        print("\nExporting data files...")

        # 1. Per-dataset analysis
        df_per_dataset = self.analyze_per_dataset()
        df_per_dataset.to_csv(output_dir / 'harmful_check_analysis.csv', index=False, encoding='utf-8-sig')
        print(f"  ✓ Saved: harmful_check_analysis.csv")

        # 2. Thinking vs Response
        df_tvr = pd.DataFrame(self.thinking_vs_response_data)
        df_tvr.to_csv(output_dir / 'thinking_vs_response.csv', index=False, encoding='utf-8-sig')
        print(f"  ✓ Saved: thinking_vs_response.csv")

        # 3. Inconsistencies CSV
        if self.inconsistencies:
            df_inc = pd.DataFrame(self.inconsistencies)
            df_inc.to_csv(output_dir / 'inconsistent_records.csv', index=False, encoding='utf-8-sig')
            print(f"  ✓ Saved: inconsistent_records.csv")

            # 4. Inconsistencies JSON (详细版本) | (detailed version)
            with open(output_dir / 'inconsistent_records_detailed.json', 'w', encoding='utf-8') as f:
                json.dump(self.inconsistencies, f, indent=2, ensure_ascii=False)
            print(f"  ✓ Saved: inconsistent_records_detailed.json")
        else:
            print("  ⚠ No inconsistencies to export")

        # 5. Safety rate by risk_type (using Harmful Check)
        df_risk_type = self.analyze_safety_rate_by_risk_type()
        df_export = df_risk_type.drop('safety_rate_numeric', axis=1)
        df_export.to_csv(output_dir / 'safety_rate_by_risk_type.csv',
                        index=False, encoding='utf-8-sig')
        print(f"  ✓ Saved: safety_rate_by_risk_type.csv")

        # 5b. Safety rate by risk_type (using Eval Detection)
        df_risk_type_eval = self.analyze_safety_rate_by_risk_type_eval_version()
        df_export_eval = df_risk_type_eval.drop('safety_rate_numeric', axis=1)
        df_export_eval.to_csv(output_dir / 'safety_rate_by_risk_type_EVAL.csv',
                              index=False, encoding='utf-8-sig')
        print(f"  ✓ Saved: safety_rate_by_risk_type_EVAL.csv")

        # 5c. Generate comparison visualization and report
        print("\n  Generating comparison analysis...")
        generate_comparison_chart(df_risk_type_eval, df_risk_type, output_dir)
        generate_diff_report(df_risk_type_eval, df_risk_type, output_dir)

        # 6. Safety rate by harm_category
        df_harm_cat = self.analyze_safety_rate_by_harm_category(top_n=30)
        df_export = df_harm_cat.drop('safety_rate_numeric', axis=1)
        df_export.to_csv(output_dir / 'safety_rate_by_harm_category.csv',
                        index=False, encoding='utf-8-sig')
        print(f"  ✓ Saved: safety_rate_by_harm_category.csv")

        # 7. Summary report
        self._generate_summary_report(output_dir)

    def _generate_summary_report(self, output_dir: Path):
        """生成文本汇总报告
        Generate a text summary report"""
        report_path = output_dir / 'summary_report.txt'

        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("HARMFUL CHECK ANALYSIS SUMMARY REPORT\n")
            f.write("=" * 80 + "\n\n")

            # Overall statistics
            total_samples = sum(len(records) for records in self.harmful_check_data.values())
            total_harmful = sum(
                sum(1 for rec in records
                    if isinstance(rec.get('harmful_check'), dict)
                    and rec.get('harmful_check', {}).get('overall_is_harmful'))
                for records in self.harmful_check_data.values()
            )

            f.write("1. OVERALL STATISTICS\n")
            f.write("-" * 80 + "\n")
            f.write(f"Total Datasets: {len(self.harmful_check_data)}\n")
            f.write(f"Total Samples: {total_samples}\n")
            f.write(f"Overall Harmful: {total_harmful} ({total_harmful/total_samples*100:.2f}%)\n")
            f.write(f"Overall Safe: {total_samples - total_harmful} ({(total_samples-total_harmful)/total_samples*100:.2f}%)\n\n")

            # Inconsistencies
            f.write("2. INCONSISTENCIES WITH EVAL RESPONSE\n")
            f.write("-" * 80 + "\n")
            f.write(f"Total Inconsistencies: {len(self.inconsistencies)}\n")

            if self.inconsistencies:
                eval_pos_hc_neg = sum(1 for inc in self.inconsistencies
                                     if inc['eval_is_harmful'] and not inc['hc_overall_is_harmful'])
                eval_neg_hc_pos = sum(1 for inc in self.inconsistencies
                                     if not inc['eval_is_harmful'] and inc['hc_overall_is_harmful'])

                f.write(f"  Eval Harmful + HC Safe: {eval_pos_hc_neg}\n")
                f.write(f"  Eval Safe + HC Harmful: {eval_neg_hc_pos}\n\n")

                # Top datasets by inconsistency
                inc_by_dataset = Counter(inc['dataset'] for inc in self.inconsistencies)
                f.write("Top 10 Datasets by Inconsistency Count:\n")
                for dataset, count in inc_by_dataset.most_common(10):
                    f.write(f"  {dataset}: {count}\n")
            f.write("\n")

            # Thinking vs Response
            f.write("3. THINKING VS RESPONSE ANALYSIS\n")
            f.write("-" * 80 + "\n")

            if self.thinking_vs_response_data:
                df_tvr = pd.DataFrame(self.thinking_vs_response_data)
                df_tvr = df_tvr.sort_values('divergence_rate', ascending=False).head(10)

                f.write("Top 10 Datasets by Divergence Rate:\n")
                for _, row in df_tvr.iterrows():
                    f.write(f"  {row['dataset']}: {row['divergence_rate']:.2f}% ")
                    f.write(f"(Thinking: {row['thinking_harmful']}, Response: {row['response_harmful']})\n")
            f.write("\n")

            # Harm Categories
            f.write("4. TOP HARM CATEGORIES\n")
            f.write("-" * 80 + "\n")
            all_categories = Counter()
            for records in self.harmful_check_data.values():
                for rec in records:
                    hc = rec.get('harmful_check', {})
                    if isinstance(hc, dict):
                        for cat in hc.get('harm_categories', []):
                            all_categories[cat] += 1

            for cat, count in all_categories.most_common(15):
                f.write(f"  {cat}: {count}\n")

            f.write("\n")

            # 5. SAFETY RATE BY CATEGORY
            f.write("5. SAFETY RATE BY CATEGORY\n")
            f.write("-" * 80 + "\n")

            # Risk Type安全率
            # Risk Type safety rate
            df_risk = self.analyze_safety_rate_by_risk_type()
            f.write("Safety Rate by Risk Type (Lowest First):\n")
            for _, row in df_risk.sort_values('safety_rate_numeric').head(10).iterrows():
                f.write(f"  {row['risk_type']}: {row['safety_rate']} ")
                f.write(f"({row['safe_samples']}/{row['total_samples']} safe)\n")

            f.write("\n")

            # Harm Category安全率
            # Harm Category safety rate
            df_harm = self.analyze_safety_rate_by_harm_category(top_n=30)
            f.write("Safety Rate by Harm Category (Top 10 Lowest):\n")
            for _, row in df_harm.sort_values('safety_rate_numeric').head(10).iterrows():
                f.write(f"  {row['harm_category']}: {row['safety_rate']} ")
                f.write(f"({row['safe_samples']}/{row['total_samples']} safe)\n")

            f.write("\n" + "=" * 80 + "\n")

        print(f"  ✓ Saved: summary_report.txt")

    def run_full_analysis(self, output_dir: str = './harmful_check_analysis'):
        """运行完整分析
        Run the full analysis"""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)

        print("\n" + "="*80)
        print("STARTING HARMFUL CHECK ANALYSIS")
        print("="*80 + "\n")

        # 1. Load data
        self.load_all_data()

        # 2. Detect inconsistencies
        self.match_records_and_detect_inconsistencies()

        # 3. Analyze thinking vs response
        self.analyze_thinking_vs_response()

        # 4. Export data
        self.export_data(output_path)

        # 5. Generate visualizations
        self.generate_visualizations(output_path)

        print("\n" + "="*80)
        print(f"ANALYSIS COMPLETE! Results saved to: {output_path.absolute()}")
        print("="*80 + "\n")

        # Quick summary
        print("QUICK SUMMARY:")
        print(f"  Total datasets: {len(self.harmful_check_data)}")
        print(f"  Total samples: {sum(len(records) for records in self.harmful_check_data.values())}")
        print(f"  Inconsistencies found: {len(self.inconsistencies)}")
        print(f"  Datasets with thinking-response divergence: {len([d for d in self.thinking_vs_response_data if d['divergence_rate'] > 0])}")
        print()


def generate_comparison_chart(df_eval, df_hc, output_dir):
    """生成两种检测方法的安全率对比图表
    Generate a safety rate comparison chart for the two detection methods"""
    import numpy as np

    # 合并数据（只选择在两个数据集都存在的 risk_type）
    # Merge the data (only select risk_types present in both datasets)
    common_types = set(df_eval['risk_type']) & set(df_hc['risk_type'])

    # 按样本数排序，取最大的20个
    # Sort by sample count and take the largest 20
    df_eval_filtered = df_eval[df_eval['risk_type'].isin(common_types)]
    top_20 = df_eval_filtered.nlargest(20, 'total_samples')['risk_type'].tolist()

    # 提取数据
    # Extract the data
    eval_rates = []
    hc_rates = []
    labels = []

    for risk_type in top_20:
        eval_row = df_eval[df_eval['risk_type'] == risk_type]
        hc_row = df_hc[df_hc['risk_type'] == risk_type]

        if not eval_row.empty and not hc_row.empty:
            eval_rates.append(eval_row['safety_rate_numeric'].values[0])
            hc_rates.append(hc_row['safety_rate_numeric'].values[0])
            labels.append(risk_type)

    # 创建对比图
    # Create the comparison chart
    fig, ax = plt.subplots(figsize=(14, 10))

    x = np.arange(len(labels))
    width = 0.35

    bars1 = ax.barh(x - width/2, eval_rates, width, label='Eval Detection (1st)',
                     color='#3498db', alpha=0.8)
    bars2 = ax.barh(x + width/2, hc_rates, width, label='Harmful Check (2nd)',
                     color='#e74c3c', alpha=0.8)

    # 设置标签
    # Set the labels
    ax.set_ylabel('Risk Type', fontsize=12, fontweight='bold')
    ax.set_xlabel('Safety Rate (%)', fontsize=12, fontweight='bold')
    ax.set_title('Safety Rate Comparison: Eval vs Harmful Check Detection\n(Top 20 Risk Types by Sample Count)',
                 fontsize=14, fontweight='bold', pad=20)
    ax.set_yticks(x)
    ax.set_yticklabels(labels, fontsize=10)
    ax.legend(loc='lower right', fontsize=11)
    ax.set_xlim(70, 100)

    # 添加网格
    # Add the grid
    ax.grid(axis='x', alpha=0.3, linestyle='--')
    ax.set_axisbelow(True)

    # 在柱子上添加数值标签
    # Add value labels on the bars
    for bars in [bars1, bars2]:
        for bar in bars:
            width_val = bar.get_width()
            ax.text(width_val + 0.5, bar.get_y() + bar.get_height()/2,
                   f'{width_val:.1f}%',
                   ha='left', va='center', fontsize=8)

    plt.tight_layout()

    # 保存图表
    # Save the chart
    output_file = output_dir / "safety_rate_comparison_eval_vs_hc.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"  ✓ Saved: safety_rate_comparison_eval_vs_hc.png")


def generate_diff_report(df_eval, df_hc, output_dir):
    """生成两种检测方法的差异分析报告
    Generate a difference analysis report for the two detection methods"""

    # 合并数据
    # Merge the data
    merged = df_eval.merge(
        df_hc,
        on='risk_type',
        suffixes=('_eval', '_hc')
    )

    # 计算差异
    # Compute the differences
    merged['safety_rate_diff'] = (
        merged['safety_rate_numeric_eval'] - merged['safety_rate_numeric_hc']
    )
    merged['harmful_count_diff'] = (
        merged['harmful_samples_hc'] - merged['harmful_samples_eval']
    )

    # 按差异排序
    # Sort by the difference
    merged_sorted = merged.sort_values('safety_rate_diff', ascending=True)

    # 生成报告
    # Generate the report
    report_path = output_dir / "detection_comparison_report.txt"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("="*80 + "\n")
        f.write("Eval Detection vs Harmful Check Detection - Comparison Report\n")
        f.write("="*80 + "\n\n")

        f.write("【总体统计】\n")
        total_eval_harmful = merged['harmful_samples_eval'].sum()
        total_hc_harmful = merged['harmful_samples_hc'].sum()
        total_samples = merged['total_samples_eval'].sum()

        f.write(f"- 总样本数: {total_samples}\n")
        f.write(f"- Eval 检测有害数: {total_eval_harmful} ({total_eval_harmful/total_samples*100:.2f}%)\n")
        f.write(f"- Harmful Check 检测有害数: {total_hc_harmful} ({total_hc_harmful/total_samples*100:.2f}%)\n")
        f.write(f"- 差异: {total_hc_harmful - total_eval_harmful} 条额外检测为有害\n\n")

        f.write("【按风险类型的差异分析】\n")
        f.write("（负数表示 Harmful Check 检测出更多有害，即安全率更低）\n\n")

        for idx, row in merged_sorted.head(20).iterrows():
            f.write(f"{row['risk_type']}\n")
            f.write(f"  样本数: {int(row['total_samples_eval'])}\n")
            f.write(f"  Eval 安全率: {row['safety_rate_numeric_eval']:.2f}%\n")
            f.write(f"  Harmful Check 安全率: {row['safety_rate_numeric_hc']:.2f}%\n")
            f.write(f"  差异: {row['safety_rate_diff']:.2f}% "
                   f"({int(row['harmful_count_diff'])} 条额外有害)\n\n")

    print(f"  ✓ Saved: detection_comparison_report.txt")


def main():
    parser = argparse.ArgumentParser(description='Analyze harmful_check data')
    parser.add_argument('--eval_dir', default='outputs/evaluations',
                       help='Directory containing eval response data')
    parser.add_argument('--harmful_check_dir', default='eval_outputs/harmful_checks',
                       help='Directory containing harmful check data')
    parser.add_argument('--output_dir', default='./harmful_check_analysis',
                       help='Output directory for analysis results')

    args = parser.parse_args()

    analyzer = HarmfulCheckAnalyzer(args.eval_dir, args.harmful_check_dir)
    analyzer.run_full_analysis(args.output_dir)


if __name__ == '__main__':
    main()
