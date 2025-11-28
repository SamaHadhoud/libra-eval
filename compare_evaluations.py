#!/usr/bin/env python3
"""
比较和分析两个版本的evaluation结果
"""

import json
import os
from pathlib import Path
from collections import defaultdict, Counter
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Tuple

# 设置中文字体和样式
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False
sns.set_style("whitegrid")
sns.set_palette("husl")


class EvaluationComparator:
    def __init__(self, eval_dir: str, harmful_check_dir: str):
        self.eval_dir = Path(eval_dir)
        self.harmful_check_dir = Path(harmful_check_dir)
        self.eval_data = {}
        self.harmful_check_data = {}

    def load_jsonl(self, file_path: Path) -> List[Dict]:
        """加载JSONL文件"""
        data = []
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    data.append(json.loads(line.strip()))
                except json.JSONDecodeError:
                    continue
        return data

    def load_all_data(self):
        """加载所有数据"""
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

    def analyze_eval_response(self, dataset_name: str) -> Dict:
        """分析eval_response数据"""
        data = self.eval_data.get(dataset_name, [])
        if not data:
            return {}

        stats = {
            'total': len(data),
            'harmful_count': 0,
            'safe_count': 0,
            'risk_types': Counter(),
            'has_eval_response': 0
        }

        for item in data:
            eval_resp = item.get('eval_response', {})
            # 确保eval_resp是字典类型
            if not isinstance(eval_resp, dict):
                continue

            if eval_resp:
                stats['has_eval_response'] += 1
                is_harmful = eval_resp.get('is_harmful')

                # 处理字符串和布尔值
                if isinstance(is_harmful, str):
                    is_harmful = is_harmful.lower() == 'true'

                if is_harmful:
                    stats['harmful_count'] += 1
                else:
                    stats['safe_count'] += 1

                risk_type = eval_resp.get('risk_type_index', 'unknown')
                stats['risk_types'][risk_type] += 1

        return stats

    def analyze_harmful_check(self, dataset_name: str) -> Dict:
        """分析harmful_check数据"""
        data = self.harmful_check_data.get(dataset_name, [])
        if not data:
            return {}

        stats = {
            'total': len(data),
            'overall_harmful': 0,
            'overall_safe': 0,
            'thinking_harmful': 0,
            'response_harmful': 0,
            'severity': Counter(),
            'harm_categories': Counter(),
            'safety_compliant': 0,
            'has_harmful_check': 0
        }

        for item in data:
            harmful_check = item.get('harmful_check', {})
            if harmful_check:
                stats['has_harmful_check'] += 1

                # Overall harmful
                if harmful_check.get('overall_is_harmful'):
                    stats['overall_harmful'] += 1
                else:
                    stats['overall_safe'] += 1

                # Thinking process
                thinking = harmful_check.get('thinking_process_analysis', {})
                if thinking.get('is_harmful'):
                    stats['thinking_harmful'] += 1

                # Final response
                response = harmful_check.get('final_response_analysis', {})
                if response.get('is_harmful'):
                    stats['response_harmful'] += 1

                # Severity
                severity = harmful_check.get('severity', 'unknown')
                stats['severity'][severity] += 1

                # Harm categories
                categories = harmful_check.get('harm_categories', [])
                for cat in categories:
                    stats['harm_categories'][cat] += 1

                # Safety compliance
                safety = harmful_check.get('safety_compliance', {})
                if safety.get('follows_system_instructions'):
                    stats['safety_compliant'] += 1

        return stats

    def generate_dataset_comparison(self, dataset_name: str) -> pd.DataFrame:
        """生成单个数据集的对比"""
        eval_stats = self.analyze_eval_response(dataset_name)
        harmful_stats = self.analyze_harmful_check(dataset_name)

        comparison = {
            'Dataset': dataset_name,
            'Total_Eval': eval_stats.get('total', 0),
            'Total_HarmfulCheck': harmful_stats.get('total', 0),
            'Eval_Harmful': eval_stats.get('harmful_count', 0),
            'Eval_Safe': eval_stats.get('safe_count', 0),
            'HC_Harmful': harmful_stats.get('overall_harmful', 0),
            'HC_Safe': harmful_stats.get('overall_safe', 0),
            'HC_Thinking_Harmful': harmful_stats.get('thinking_harmful', 0),
            'HC_Response_Harmful': harmful_stats.get('response_harmful', 0),
            'HC_Safety_Compliant': harmful_stats.get('safety_compliant', 0),
        }

        # 计算百分比
        if eval_stats.get('total', 0) > 0:
            comparison['Eval_Harmful_Rate'] = f"{eval_stats['harmful_count'] / eval_stats['total'] * 100:.2f}%"
        else:
            comparison['Eval_Harmful_Rate'] = "N/A"

        if harmful_stats.get('total', 0) > 0:
            comparison['HC_Harmful_Rate'] = f"{harmful_stats['overall_harmful'] / harmful_stats['total'] * 100:.2f}%"
        else:
            comparison['HC_Harmful_Rate'] = "N/A"

        return comparison

    def generate_full_comparison(self) -> pd.DataFrame:
        """生成所有数据集的对比表"""
        all_datasets = set(self.eval_data.keys()) | set(self.harmful_check_data.keys())
        comparisons = []

        for dataset in sorted(all_datasets):
            comp = self.generate_dataset_comparison(dataset)
            comparisons.append(comp)

        return pd.DataFrame(comparisons)

    def plot_harmful_rate_comparison(self, df: pd.DataFrame, output_dir: Path):
        """绘制harmful rate对比图"""
        fig, ax = plt.subplots(figsize=(14, 8))

        # 准备数据
        datasets = df['Dataset'].tolist()
        eval_rates = []
        hc_rates = []

        for _, row in df.iterrows():
            eval_rate = row['Eval_Harmful_Rate']
            hc_rate = row['HC_Harmful_Rate']

            if eval_rate != "N/A":
                eval_rates.append(float(eval_rate.strip('%')))
            else:
                eval_rates.append(0)

            if hc_rate != "N/A":
                hc_rates.append(float(hc_rate.strip('%')))
            else:
                hc_rates.append(0)

        x = range(len(datasets))
        width = 0.35

        bars1 = ax.bar([i - width/2 for i in x], eval_rates, width, label='Eval Response', alpha=0.8)
        bars2 = ax.bar([i + width/2 for i in x], hc_rates, width, label='Harmful Check', alpha=0.8)

        ax.set_xlabel('Dataset', fontsize=12, fontweight='bold')
        ax.set_ylabel('Harmful Rate (%)', fontsize=12, fontweight='bold')
        ax.set_title('Harmful Rate Comparison: Eval Response vs Harmful Check', fontsize=14, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(datasets, rotation=90, ha='right')
        ax.legend()
        ax.grid(axis='y', alpha=0.3)

        plt.tight_layout()
        plt.savefig(output_dir / 'harmful_rate_comparison.png', dpi=300, bbox_inches='tight')
        plt.close()
        print(f"Saved: {output_dir / 'harmful_rate_comparison.png'}")

    def plot_risk_type_distribution(self, output_dir: Path):
        """绘制风险类型分布"""
        all_risk_types = Counter()

        for dataset_name in self.eval_data.keys():
            stats = self.analyze_eval_response(dataset_name)
            all_risk_types.update(stats.get('risk_types', {}))

        if not all_risk_types:
            return

        # 排序
        risk_types = dict(all_risk_types.most_common(15))

        fig, ax = plt.subplots(figsize=(12, 6))
        bars = ax.barh(list(risk_types.keys()), list(risk_types.values()), alpha=0.8)

        # 添加数值标签
        for bar in bars:
            width = bar.get_width()
            ax.text(width, bar.get_y() + bar.get_height()/2,
                   f'{int(width)}', ha='left', va='center', fontweight='bold')

        ax.set_xlabel('Count', fontsize=12, fontweight='bold')
        ax.set_ylabel('Risk Type', fontsize=12, fontweight='bold')
        ax.set_title('Top 15 Risk Types (Eval Response)', fontsize=14, fontweight='bold')
        ax.grid(axis='x', alpha=0.3)

        plt.tight_layout()
        plt.savefig(output_dir / 'risk_type_distribution.png', dpi=300, bbox_inches='tight')
        plt.close()
        print(f"Saved: {output_dir / 'risk_type_distribution.png'}")

    def plot_harm_categories(self, output_dir: Path):
        """绘制harm categories分布"""
        all_categories = Counter()

        for dataset_name in self.harmful_check_data.keys():
            stats = self.analyze_harmful_check(dataset_name)
            all_categories.update(stats.get('harm_categories', {}))

        if not all_categories:
            return

        categories = dict(all_categories.most_common(15))

        fig, ax = plt.subplots(figsize=(12, 6))
        bars = ax.barh(list(categories.keys()), list(categories.values()), alpha=0.8, color='coral')

        for bar in bars:
            width = bar.get_width()
            ax.text(width, bar.get_y() + bar.get_height()/2,
                   f'{int(width)}', ha='left', va='center', fontweight='bold')

        ax.set_xlabel('Count', fontsize=12, fontweight='bold')
        ax.set_ylabel('Harm Category', fontsize=12, fontweight='bold')
        ax.set_title('Top 15 Harm Categories (Harmful Check)', fontsize=14, fontweight='bold')
        ax.grid(axis='x', alpha=0.3)

        plt.tight_layout()
        plt.savefig(output_dir / 'harm_categories_distribution.png', dpi=300, bbox_inches='tight')
        plt.close()
        print(f"Saved: {output_dir / 'harm_categories_distribution.png'}")

    def plot_severity_distribution(self, output_dir: Path):
        """绘制severity分布"""
        all_severity = Counter()

        for dataset_name in self.harmful_check_data.keys():
            stats = self.analyze_harmful_check(dataset_name)
            all_severity.update(stats.get('severity', {}))

        if not all_severity:
            return

        fig, ax = plt.subplots(figsize=(10, 6))

        labels = list(all_severity.keys())
        sizes = list(all_severity.values())
        colors = ['#90EE90', '#FFD700', '#FF6347', '#8B0000']  # green, yellow, red, dark red

        wedges, texts, autotexts = ax.pie(sizes, labels=labels, autopct='%1.1f%%',
                                           colors=colors[:len(labels)], startangle=90)

        for text in texts:
            text.set_fontsize(12)
            text.set_fontweight('bold')

        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontsize(10)
            autotext.set_fontweight('bold')

        ax.set_title('Severity Distribution (Harmful Check)', fontsize=14, fontweight='bold')

        plt.tight_layout()
        plt.savefig(output_dir / 'severity_distribution.png', dpi=300, bbox_inches='tight')
        plt.close()
        print(f"Saved: {output_dir / 'severity_distribution.png'}")

    def plot_thinking_vs_response_harmful(self, output_dir: Path):
        """绘制thinking process vs final response harmful对比"""
        datasets = []
        thinking_harmful = []
        response_harmful = []

        for dataset_name in sorted(self.harmful_check_data.keys()):
            stats = self.analyze_harmful_check(dataset_name)
            total = stats.get('total', 0)
            if total > 0:
                datasets.append(dataset_name)
                thinking_harmful.append(stats.get('thinking_harmful', 0) / total * 100)
                response_harmful.append(stats.get('response_harmful', 0) / total * 100)

        if not datasets:
            return

        fig, ax = plt.subplots(figsize=(14, 8))

        x = range(len(datasets))
        width = 0.35

        bars1 = ax.bar([i - width/2 for i in x], thinking_harmful, width,
                       label='Thinking Process Harmful', alpha=0.8, color='lightcoral')
        bars2 = ax.bar([i + width/2 for i in x], response_harmful, width,
                       label='Final Response Harmful', alpha=0.8, color='darkred')

        ax.set_xlabel('Dataset', fontsize=12, fontweight='bold')
        ax.set_ylabel('Harmful Rate (%)', fontsize=12, fontweight='bold')
        ax.set_title('Thinking Process vs Final Response Harmful Rate', fontsize=14, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(datasets, rotation=90, ha='right')
        ax.legend()
        ax.grid(axis='y', alpha=0.3)

        plt.tight_layout()
        plt.savefig(output_dir / 'thinking_vs_response_harmful.png', dpi=300, bbox_inches='tight')
        plt.close()
        print(f"Saved: {output_dir / 'thinking_vs_response_harmful.png'}")

    def generate_summary_report(self, df: pd.DataFrame, output_dir: Path):
        """生成汇总报告"""
        report_path = output_dir / 'comparison_summary.txt'

        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("EVALUATION COMPARISON SUMMARY REPORT\n")
            f.write("=" * 80 + "\n\n")

            # Overall statistics
            f.write("1. OVERALL STATISTICS\n")
            f.write("-" * 80 + "\n")
            f.write(f"Total Datasets: {len(df)}\n\n")

            # Eval Response Stats
            total_eval = df['Total_Eval'].sum()
            total_eval_harmful = df['Eval_Harmful'].sum()
            f.write(f"Eval Response:\n")
            f.write(f"  Total Samples: {total_eval}\n")
            f.write(f"  Harmful: {total_eval_harmful} ({total_eval_harmful/total_eval*100:.2f}%)\n")
            f.write(f"  Safe: {df['Eval_Safe'].sum()} ({df['Eval_Safe'].sum()/total_eval*100:.2f}%)\n\n")

            # Harmful Check Stats
            total_hc = df['Total_HarmfulCheck'].sum()
            total_hc_harmful = df['HC_Harmful'].sum()
            f.write(f"Harmful Check:\n")
            f.write(f"  Total Samples: {total_hc}\n")
            f.write(f"  Overall Harmful: {total_hc_harmful} ({total_hc_harmful/total_hc*100:.2f}%)\n")
            f.write(f"  Overall Safe: {df['HC_Safe'].sum()} ({df['HC_Safe'].sum()/total_hc*100:.2f}%)\n")
            f.write(f"  Thinking Harmful: {df['HC_Thinking_Harmful'].sum()} ({df['HC_Thinking_Harmful'].sum()/total_hc*100:.2f}%)\n")
            f.write(f"  Response Harmful: {df['HC_Response_Harmful'].sum()} ({df['HC_Response_Harmful'].sum()/total_hc*100:.2f}%)\n")
            f.write(f"  Safety Compliant: {df['HC_Safety_Compliant'].sum()} ({df['HC_Safety_Compliant'].sum()/total_hc*100:.2f}%)\n\n")

            # Top 10 datasets by harmful rate
            f.write("\n2. TOP 10 DATASETS BY HARMFUL RATE (EVAL RESPONSE)\n")
            f.write("-" * 80 + "\n")

            df_sorted = df[df['Eval_Harmful_Rate'] != 'N/A'].copy()
            if not df_sorted.empty:
                df_sorted['Eval_Harmful_Rate_Numeric'] = df_sorted['Eval_Harmful_Rate'].str.rstrip('%').astype(float)
                df_sorted = df_sorted.sort_values('Eval_Harmful_Rate_Numeric', ascending=False).head(10)

                for idx, row in df_sorted.iterrows():
                    f.write(f"  {row['Dataset']}: {row['Eval_Harmful_Rate']}\n")

            f.write("\n3. TOP 10 DATASETS BY HARMFUL RATE (HARMFUL CHECK)\n")
            f.write("-" * 80 + "\n")

            df_sorted_hc = df[df['HC_Harmful_Rate'] != 'N/A'].copy()
            if not df_sorted_hc.empty:
                df_sorted_hc['HC_Harmful_Rate_Numeric'] = df_sorted_hc['HC_Harmful_Rate'].str.rstrip('%').astype(float)
                df_sorted_hc = df_sorted_hc.sort_values('HC_Harmful_Rate_Numeric', ascending=False).head(10)

                for idx, row in df_sorted_hc.iterrows():
                    f.write(f"  {row['Dataset']}: {row['HC_Harmful_Rate']}\n")

            # Risk types and harm categories
            f.write("\n4. RISK TYPES DISTRIBUTION (TOP 10)\n")
            f.write("-" * 80 + "\n")
            all_risk_types = Counter()
            for dataset_name in self.eval_data.keys():
                stats = self.analyze_eval_response(dataset_name)
                all_risk_types.update(stats.get('risk_types', {}))

            for risk_type, count in all_risk_types.most_common(10):
                f.write(f"  {risk_type}: {count}\n")

            f.write("\n5. HARM CATEGORIES DISTRIBUTION (TOP 10)\n")
            f.write("-" * 80 + "\n")
            all_categories = Counter()
            for dataset_name in self.harmful_check_data.keys():
                stats = self.analyze_harmful_check(dataset_name)
                all_categories.update(stats.get('harm_categories', {}))

            for category, count in all_categories.most_common(10):
                f.write(f"  {category}: {count}\n")

            f.write("\n" + "=" * 80 + "\n")

        print(f"Saved: {report_path}")

    def run_full_analysis(self, output_dir: str = './comparison_results'):
        """运行完整分析"""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)

        print("\n" + "="*80)
        print("STARTING FULL COMPARISON ANALYSIS")
        print("="*80 + "\n")

        # Load data
        self.load_all_data()

        # Generate comparison DataFrame
        print("\nGenerating comparison table...")
        df = self.generate_full_comparison()

        # Save to CSV
        csv_path = output_path / 'comparison_table.csv'
        df.to_csv(csv_path, index=False, encoding='utf-8-sig')
        print(f"Saved: {csv_path}")

        # Generate visualizations
        print("\nGenerating visualizations...")
        self.plot_harmful_rate_comparison(df, output_path)
        self.plot_risk_type_distribution(output_path)
        self.plot_harm_categories(output_path)
        self.plot_severity_distribution(output_path)
        self.plot_thinking_vs_response_harmful(output_path)

        # Generate summary report
        print("\nGenerating summary report...")
        self.generate_summary_report(df, output_path)

        print("\n" + "="*80)
        print(f"ANALYSIS COMPLETE! Results saved to: {output_path.absolute()}")
        print("="*80 + "\n")

        # Print quick summary
        print("QUICK SUMMARY:")
        print(f"  Total datasets analyzed: {len(df)}")
        print(f"  Eval samples: {df['Total_Eval'].sum()}")
        print(f"  Harmful Check samples: {df['Total_HarmfulCheck'].sum()}")
        print(f"\nFiles generated:")
        print(f"  - comparison_table.csv")
        print(f"  - harmful_rate_comparison.png")
        print(f"  - risk_type_distribution.png")
        print(f"  - harm_categories_distribution.png")
        print(f"  - severity_distribution.png")
        print(f"  - thinking_vs_response_harmful.png")
        print(f"  - comparison_summary.txt")
        print()


def main():
    eval_dir = '/Users/gaojunjie/code/libra-eval/outputs/evaluations'
    harmful_check_dir = '/Users/gaojunjie/code/libra-eval/eval_outputs/harmful_checks'
    output_dir = './comparison_results'

    comparator = EvaluationComparator(eval_dir, harmful_check_dir)
    comparator.run_full_analysis(output_dir)


if __name__ == '__main__':
    main()
