#!/usr/bin/env python3
"""
从 test_results.json 提取任务分数并生成可视化
"""

import json
import argparse
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt


def load_results(json_path):
    """加载 JSON 文件，提取任务和分数"""
    with open(json_path, 'r') as f:
        data = json.load(f)

    tasks = []
    for task in data['tasks']:
        tasks.append({
            'Task Name': task['task_name'],
            'Score': task.get('score'),
            'Status': task['status']
        })

    df = pd.DataFrame(tasks)

    # 按分数排序
    df_sorted = df.sort_values('Score', ascending=True)

    # 提取元数据
    summary = data.get('summary', {})

    return df_sorted, summary


def create_table(df, output_dir):
    """生成 Tab 分隔的表格和 Markdown 表格"""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # 保存 TSV（Tab 分隔，便于复制到飞书）
    tsv_path = output_dir / 'results_table.tsv'
    df.to_csv(tsv_path, sep='\t', index=False)
    print(f"✓ TSV 表格已保存到: {tsv_path} (可直接复制到飞书)")

    # 同时生成横向版本（转置）
    # 创建转置DataFrame：第一行是任务名，第二行是分数，第三行是状态
    df_transposed = pd.DataFrame({
        task['Task Name']: [task['Score'], task['Status']]
        for _, task in df.iterrows()
    }, index=['Score', 'Status'])

    tsv_transposed_path = output_dir / 'results_table_horizontal.tsv'
    df_transposed.to_csv(tsv_transposed_path, sep='\t')
    print(f"✓ 横向 TSV 表格已保存到: {tsv_transposed_path}")

    # 保存 Markdown（手动生成，不依赖 tabulate）
    md_path = output_dir / 'results_table.md'
    with open(md_path, 'w') as f:
        f.write("# Task Scores\n\n")
        f.write("| Task Name | Score | Status |\n")
        f.write("|-----------|-------|--------|\n")
        for _, row in df.iterrows():
            score_str = f"{row['Score']:.3f}" if pd.notna(row['Score']) else "N/A"
            f.write(f"| {row['Task Name']} | {score_str} | {row['Status']} |\n")
    print(f"✓ Markdown 表格已保存到: {md_path}")

    return tsv_path, tsv_transposed_path, md_path


def create_chart(df, summary, output_dir):
    """生成条形图（过滤掉 NaN 值）"""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # 过滤掉 score 为 NaN 的任务
    df_valid = df[df['Score'].notna()].copy()

    if len(df_valid) == 0:
        print("⚠️  没有有效的分数数据，跳过图表生成")
        return None

    print(f"ℹ️  过滤后有 {len(df_valid)} 个任务有有效分数（跳过了 {len(df) - len(df_valid)} 个 NaN 值）")

    # 设置图表大小（根据任务数量动态调整）
    n_tasks = len(df_valid)
    fig_height = max(12, n_tasks * 0.3)  # 至少12英寸，每个任务0.3英寸

    fig, ax = plt.subplots(figsize=(14, fig_height))

    # 颜色：失败=红色，通过=蓝色
    colors = ['red' if status == 'failed' else 'steelblue'
              for status in df_valid['Status']]

    # 绘制水平条形图
    bars = ax.barh(df_valid['Task Name'], df_valid['Score'], color=colors, alpha=0.7)

    # 添加分数标签
    for i, (task, score) in enumerate(zip(df_valid['Task Name'], df_valid['Score'])):
        label = f'{score:.3f}'
        ax.text(score + 0.01, i, label, va='center', fontsize=8)

    # 添加参考线
    ax.axvline(x=0.5, color='gray', linestyle='--', alpha=0.5, linewidth=1, label='0.5 threshold')
    ax.axvline(x=0.7, color='orange', linestyle='--', alpha=0.5, linewidth=1, label='0.7 threshold')
    ax.axvline(x=0.9, color='green', linestyle='--', alpha=0.5, linewidth=1, label='0.9 threshold')

    # 设置标题和标签
    model_name = summary.get('model', 'Unknown')
    n_samples = summary.get('n_samples_per_task', 'N/A')
    total_tasks = summary.get('total_tasks', len(df))
    passed_tasks = summary.get('passed_tasks', sum(df['Status'] == 'passed'))

    ax.set_xlabel('Score (Safety Rate)', fontsize=13, fontweight='bold')
    ax.set_title(f'Task Scores - Model: {model_name}\n'
                 f'({n_samples} samples/task, {passed_tasks}/{total_tasks} passed)',
                 fontsize=15, fontweight='bold', pad=20)
    ax.set_xlim(0, 1.05)
    ax.legend(loc='lower right', fontsize=10)
    ax.grid(axis='x', alpha=0.3, linestyle=':')

    # 设置 y 轴字体大小
    ax.tick_params(axis='y', labelsize=9)
    ax.tick_params(axis='x', labelsize=11)

    plt.tight_layout()

    # 保存图表
    chart_path = output_dir / 'results_chart.png'
    plt.savefig(chart_path, dpi=300, bbox_inches='tight')
    print(f"✓ 图表已保存到: {chart_path}")

    return chart_path


def print_summary(df, summary):
    """打印摘要统计"""
    print("\n" + "="*70)
    print("任务分数摘要")
    print("="*70)

    total = len(df)
    passed = sum(df['Status'] == 'passed')
    failed = sum(df['Status'] == 'failed')

    print(f"总任务数: {total}")
    print(f"通过: {passed} ({passed/total*100:.1f}%)")
    print(f"失败: {failed} ({failed/total*100:.1f}%)")

    # 分数统计（只统计有效分数）
    scores = df['Score'].dropna()
    valid_count = len(scores)
    nan_count = total - valid_count

    if valid_count > 0:
        print(f"\n有效分数: {valid_count} 个")
        if nan_count > 0:
            print(f"无效分数 (NaN): {nan_count} 个")
        print(f"\n分数统计 (仅有效分数):")
        print(f"  平均分: {scores.mean():.4f}")
        print(f"  中位数: {scores.median():.4f}")
        print(f"  最高分: {scores.max():.4f}")
        print(f"  最低分: {scores.min():.4f}")

    # 显示失败的任务
    failed_tasks = df[df['Status'] == 'failed']
    if len(failed_tasks) > 0:
        print(f"\n失败的任务:")
        for _, task in failed_tasks.iterrows():
            score_str = f"{task['Score']:.3f}" if task['Score'] is not None else "N/A"
            print(f"  - {task['Task Name']}: {score_str}")

    # 显示低分任务 (< 0.7)
    low_score_tasks = df[df['Score'] < 0.7]
    if len(low_score_tasks) > 0:
        print(f"\n低分任务 (< 0.7):")
        for _, task in low_score_tasks.iterrows():
            print(f"  - {task['Task Name']}: {task['Score']:.3f}")

    print("="*70 + "\n")


def main():
    parser = argparse.ArgumentParser(description='从 test_results.json 提取并可视化任务分数')
    parser.add_argument('--input', default='outputs/test_results.json',
                       help='输入的 JSON 文件路径（默认: outputs/test_results.json）')
    parser.add_argument('--output', default='outputs',
                       help='输出目录（默认: outputs）')
    parser.add_argument('--no-chart', action='store_true',
                       help='不生成图表')

    args = parser.parse_args()

    print(f"读取数据: {args.input}")
    df, summary = load_results(args.input)

    print(f"\n加载了 {len(df)} 个任务的结果")

    # 打印摘要
    print_summary(df, summary)

    # 生成表格
    print("生成表格...")
    create_table(df, args.output)

    # 生成图表
    if not args.no_chart:
        print("生成图表...")
        create_chart(df, summary, args.output)

    print("\n✓ 所有文件已生成完成！")


if __name__ == '__main__':
    main()
