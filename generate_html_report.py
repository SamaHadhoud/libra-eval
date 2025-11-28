#!/usr/bin/env python3
"""
生成交互式HTML报告
"""

import pandas as pd
import json
from pathlib import Path

def generate_html_report():
    results_dir = Path('./comparison_results')

    # 读取CSV数据
    df = pd.read_csv(results_dir / 'comparison_table.csv')

    # 读取summary文本
    with open(results_dir / 'comparison_summary.txt', 'r', encoding='utf-8') as f:
        summary_text = f.read()

    html_content = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Evaluation Comparison Report</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }

        header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }

        header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }

        header p {
            font-size: 1.2em;
            opacity: 0.9;
        }

        .nav-tabs {
            display: flex;
            background: #f8f9fa;
            border-bottom: 2px solid #dee2e6;
            overflow-x: auto;
        }

        .nav-tab {
            padding: 15px 30px;
            cursor: pointer;
            border: none;
            background: none;
            font-size: 16px;
            font-weight: 600;
            color: #495057;
            transition: all 0.3s ease;
            white-space: nowrap;
        }

        .nav-tab:hover {
            background: #e9ecef;
            color: #667eea;
        }

        .nav-tab.active {
            background: white;
            color: #667eea;
            border-bottom: 3px solid #667eea;
        }

        .tab-content {
            display: none;
            padding: 40px;
            animation: fadeIn 0.5s;
        }

        .tab-content.active {
            display: block;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .summary-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }

        .summary-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);
            transition: transform 0.3s ease;
        }

        .summary-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 15px 40px rgba(102, 126, 234, 0.4);
        }

        .summary-card h3 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }

        .summary-card p {
            font-size: 1.1em;
            opacity: 0.9;
        }

        .chart-container {
            margin: 30px 0;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 10px;
            text-align: center;
        }

        .chart-container img {
            max-width: 100%;
            height: auto;
            border-radius: 8px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }

        .chart-container h3 {
            margin-bottom: 20px;
            color: #495057;
            font-size: 1.5em;
        }

        .table-container {
            overflow-x: auto;
            margin: 30px 0;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            background: white;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            border-radius: 8px;
            overflow: hidden;
        }

        thead {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }

        th {
            padding: 15px;
            text-align: left;
            font-weight: 600;
            font-size: 0.95em;
            position: sticky;
            top: 0;
            z-index: 10;
        }

        td {
            padding: 12px 15px;
            border-bottom: 1px solid #dee2e6;
            font-size: 0.9em;
        }

        tr:hover {
            background: #f8f9fa;
        }

        .summary-text {
            background: #f8f9fa;
            padding: 30px;
            border-radius: 10px;
            font-family: 'Courier New', monospace;
            white-space: pre-wrap;
            font-size: 0.9em;
            line-height: 1.8;
            box-shadow: inset 0 2px 5px rgba(0,0,0,0.1);
        }

        .highlight {
            color: #667eea;
            font-weight: bold;
        }

        .badge {
            display: inline-block;
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 0.85em;
            font-weight: 600;
        }

        .badge-success {
            background: #28a745;
            color: white;
        }

        .badge-warning {
            background: #ffc107;
            color: #333;
        }

        .badge-danger {
            background: #dc3545;
            color: white;
        }

        .comparison-highlight {
            display: flex;
            justify-content: space-around;
            margin: 40px 0;
            flex-wrap: wrap;
        }

        .comparison-item {
            flex: 1;
            min-width: 250px;
            margin: 10px;
            padding: 30px;
            background: white;
            border-radius: 10px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            text-align: center;
        }

        .comparison-item h4 {
            color: #667eea;
            font-size: 1.2em;
            margin-bottom: 15px;
        }

        .comparison-item .value {
            font-size: 2em;
            font-weight: bold;
            color: #333;
            margin-bottom: 10px;
        }

        .comparison-item .description {
            color: #6c757d;
            font-size: 0.9em;
        }

        footer {
            background: #f8f9fa;
            padding: 20px;
            text-align: center;
            color: #6c757d;
            border-top: 1px solid #dee2e6;
        }

        .search-box {
            margin: 20px 0;
            padding: 12px 20px;
            width: 100%;
            max-width: 500px;
            border: 2px solid #dee2e6;
            border-radius: 25px;
            font-size: 1em;
            transition: border-color 0.3s ease;
        }

        .search-box:focus {
            outline: none;
            border-color: #667eea;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>📊 Evaluation Comparison Report</h1>
            <p>对比分析：Eval Response vs Harmful Check</p>
        </header>

        <div class="nav-tabs">
            <button class="nav-tab active" onclick="showTab('overview')">📈 Overview</button>
            <button class="nav-tab" onclick="showTab('comparison')">⚖️ Comparison</button>
            <button class="nav-tab" onclick="showTab('visualizations')">📊 Visualizations</button>
            <button class="nav-tab" onclick="showTab('data')">📋 Data Table</button>
            <button class="nav-tab" onclick="showTab('summary')">📄 Summary</button>
        </div>

        <div id="overview" class="tab-content active">
            <h2 style="margin-bottom: 30px; color: #495057;">📋 整体统计</h2>

            <div class="summary-grid">
                <div class="summary-card">
                    <h3>68</h3>
                    <p>总数据集数量</p>
                </div>
                <div class="summary-card">
                    <h3>12,675</h3>
                    <p>总样本数量</p>
                </div>
                <div class="summary-card">
                    <h3>1.47%</h3>
                    <p>Eval Response Harmful Rate</p>
                </div>
                <div class="summary-card">
                    <h3>3.53%</h3>
                    <p>Harmful Check Harmful Rate</p>
                </div>
            </div>

            <div class="comparison-highlight">
                <div class="comparison-item">
                    <h4>🔍 Eval Response</h4>
                    <div class="value">186</div>
                    <div class="description">标记为 Harmful (1.47%)</div>
                    <div class="description" style="margin-top: 10px; color: #28a745;">
                        9,893 Safe (78.05%)
                    </div>
                </div>

                <div class="comparison-item">
                    <h4>🛡️ Harmful Check</h4>
                    <div class="value">447</div>
                    <div class="description">标记为 Harmful (3.53%)</div>
                    <div class="description" style="margin-top: 10px; color: #28a745;">
                        12,228 Safe (96.47%)
                    </div>
                </div>
            </div>

            <h3 style="margin: 40px 0 20px; color: #495057;">🎯 关键发现</h3>
            <div style="background: #fff3cd; padding: 20px; border-radius: 10px; border-left: 5px solid #ffc107;">
                <ul style="list-style: none; padding-left: 0;">
                    <li style="margin: 10px 0;">✅ <strong>Harmful Check检测到更多潜在有害内容</strong> (3.53% vs 1.47%)</li>
                    <li style="margin: 10px 0;">✅ <strong>Thinking Process Harmful Rate: 2.07%</strong></li>
                    <li style="margin: 10px 0;">✅ <strong>Final Response Harmful Rate: 2.49%</strong></li>
                    <li style="margin: 10px 0;">✅ <strong>Safety Compliance: 83.86%</strong> 的样本遵守了系统指令</li>
                </ul>
            </div>
        </div>

        <div id="comparison" class="tab-content">
            <h2 style="margin-bottom: 30px; color: #495057;">⚖️ 详细对比</h2>

            <h3 style="margin: 30px 0 20px; color: #495057;">Top 10 数据集 - Eval Response Harmful Rate</h3>
            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>排名</th>
                            <th>数据集</th>
                            <th>Harmful Rate</th>
                            <th>状态</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr><td>1</td><td>librai_adv_few_shots</td><td>30.50%</td><td><span class="badge badge-danger">High</span></td></tr>
                        <tr><td>2</td><td>sorry_bench</td><td>13.50%</td><td><span class="badge badge-warning">Medium</span></td></tr>
                        <tr><td>3</td><td>librai_adv_refusal_suppression</td><td>7.50%</td><td><span class="badge badge-warning">Medium</span></td></tr>
                        <tr><td>4</td><td>prompt_injection</td><td>6.00%</td><td><span class="badge badge-warning">Medium</span></td></tr>
                        <tr><td>5</td><td>physical_safety_instructions_unsafe</td><td>5.00%</td><td><span class="badge badge-warning">Medium</span></td></tr>
                        <tr><td>6</td><td>librai_adv_persona_modulation</td><td>5.00%</td><td><span class="badge badge-warning">Medium</span></td></tr>
                        <tr><td>7</td><td>librai_adv_deep_inception</td><td>4.50%</td><td><span class="badge badge-warning">Medium</span></td></tr>
                        <tr><td>8</td><td>librai_adv_do_anything_now</td><td>3.50%</td><td><span class="badge badge-warning">Medium</span></td></tr>
                        <tr><td>9</td><td>jailbench</td><td>3.50%</td><td><span class="badge badge-warning">Medium</span></td></tr>
                        <tr><td>10</td><td>hypothesis_stereotypes</td><td>2.50%</td><td><span class="badge badge-success">Low</span></td></tr>
                    </tbody>
                </table>
            </div>

            <h3 style="margin: 30px 0 20px; color: #495057;">Top 10 数据集 - Harmful Check Harmful Rate</h3>
            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>排名</th>
                            <th>数据集</th>
                            <th>Harmful Rate</th>
                            <th>状态</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr><td>1</td><td>gandalf_ignore_instructions</td><td>41.00%</td><td><span class="badge badge-danger">High</span></td></tr>
                        <tr><td>2</td><td>prompt_injection</td><td>19.00%</td><td><span class="badge badge-danger">High</span></td></tr>
                        <tr><td>3</td><td>physical_safety_instructions_unsafe</td><td>16.00%</td><td><span class="badge badge-danger">High</span></td></tr>
                        <tr><td>4</td><td>librai_adv_deep_inception</td><td>13.00%</td><td><span class="badge badge-warning">Medium</span></td></tr>
                        <tr><td>5</td><td>sorry_bench</td><td>12.00%</td><td><span class="badge badge-warning">Medium</span></td></tr>
                        <tr><td>6</td><td>librai_adv_persona_modulation</td><td>8.50%</td><td><span class="badge badge-warning">Medium</span></td></tr>
                        <tr><td>7</td><td>hypothesis_stereotypes</td><td>8.00%</td><td><span class="badge badge-warning">Medium</span></td></tr>
                        <tr><td>8</td><td>librai_adv_refusal_suppression</td><td>8.00%</td><td><span class="badge badge-warning">Medium</span></td></tr>
                        <tr><td>9</td><td>cyberattack_assistance</td><td>7.58%</td><td><span class="badge badge-warning">Medium</span></td></tr>
                        <tr><td>10</td><td>jailbench</td><td>7.50%</td><td><span class="badge badge-warning">Medium</span></td></tr>
                    </tbody>
                </table>
            </div>

            <h3 style="margin: 30px 0 20px; color: #495057;">📊 Risk Types & Harm Categories</h3>
            <div class="comparison-highlight">
                <div class="comparison-item">
                    <h4>Top Risk Types</h4>
                    <div style="text-align: left; margin-top: 15px;">
                        <div style="margin: 8px 0;">1. None: <strong>2,919</strong></div>
                        <div style="margin: 8px 0;">2. Privacy: <strong>1,044</strong></div>
                        <div style="margin: 8px 0;">3. Criminal Activities: <strong>877</strong></div>
                        <div style="margin: 8px 0;">4. Hate/Toxicity: <strong>844</strong></div>
                        <div style="margin: 8px 0;">5. Violence & Extremism: <strong>815</strong></div>
                    </div>
                </div>

                <div class="comparison-item">
                    <h4>Top Harm Categories</h4>
                    <div style="text-align: left; margin-top: 15px;">
                        <div style="margin: 8px 0;">1. Discrimination: <strong>1,334</strong></div>
                        <div style="margin: 8px 0;">2. Illegal: <strong>1,291</strong></div>
                        <div style="margin: 8px 0;">3. Privacy: <strong>1,131</strong></div>
                        <div style="margin: 8px 0;">4. Violence: <strong>774</strong></div>
                        <div style="margin: 8px 0;">5. Hate Speech: <strong>441</strong></div>
                    </div>
                </div>
            </div>
        </div>

        <div id="visualizations" class="tab-content">
            <h2 style="margin-bottom: 30px; color: #495057;">📊 可视化分析</h2>

            <div class="chart-container">
                <h3>Harmful Rate 对比</h3>
                <img src="harmful_rate_comparison.png" alt="Harmful Rate Comparison">
            </div>

            <div class="chart-container">
                <h3>Risk Type 分布</h3>
                <img src="risk_type_distribution.png" alt="Risk Type Distribution">
            </div>

            <div class="chart-container">
                <h3>Harm Categories 分布</h3>
                <img src="harm_categories_distribution.png" alt="Harm Categories Distribution">
            </div>

            <div class="chart-container">
                <h3>Severity 分布</h3>
                <img src="severity_distribution.png" alt="Severity Distribution">
            </div>

            <div class="chart-container">
                <h3>Thinking Process vs Final Response</h3>
                <img src="thinking_vs_response_harmful.png" alt="Thinking vs Response">
            </div>
        </div>

        <div id="data" class="tab-content">
            <h2 style="margin-bottom: 30px; color: #495057;">📋 完整数据表</h2>

            <input type="text" class="search-box" id="searchBox" placeholder="🔍 搜索数据集..." onkeyup="filterTable()">

            <div class="table-container">
"""

    # 添加数据表
    html_content += "<table id='dataTable'>\n<thead>\n<tr>\n"
    for col in df.columns:
        html_content += f"<th>{col}</th>\n"
    html_content += "</tr>\n</thead>\n<tbody>\n"

    for _, row in df.iterrows():
        html_content += "<tr>\n"
        for val in row:
            html_content += f"<td>{val}</td>\n"
        html_content += "</tr>\n"

    html_content += """
            </tbody>
        </table>
    </div>
</div>

<div id="summary" class="tab-content">
    <h2 style="margin-bottom: 30px; color: #495057;">📄 详细报告</h2>
    <div class="summary-text">
""" + summary_text + """
    </div>
</div>

<footer>
    <p>生成时间: """ + pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S') + """</p>
    <p>© 2025 Evaluation Comparison Report</p>
</footer>
</div>

<script>
    function showTab(tabName) {
        // Hide all tabs
        const tabs = document.querySelectorAll('.tab-content');
        tabs.forEach(tab => tab.classList.remove('active'));

        // Remove active from all nav tabs
        const navTabs = document.querySelectorAll('.nav-tab');
        navTabs.forEach(tab => tab.classList.remove('active'));

        // Show selected tab
        document.getElementById(tabName).classList.add('active');
        event.target.classList.add('active');
    }

    function filterTable() {
        const input = document.getElementById('searchBox');
        const filter = input.value.toUpperCase();
        const table = document.getElementById('dataTable');
        const tr = table.getElementsByTagName('tr');

        for (let i = 1; i < tr.length; i++) {
            const td = tr[i].getElementsByTagName('td')[0];
            if (td) {
                const txtValue = td.textContent || td.innerText;
                if (txtValue.toUpperCase().indexOf(filter) > -1) {
                    tr[i].style.display = '';
                } else {
                    tr[i].style.display = 'none';
                }
            }
        }
    }
</script>
</body>
</html>
"""

    # 保存HTML文件
    output_path = results_dir / 'comparison_report.html'
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"✅ HTML报告已生成: {output_path.absolute()}")
    print(f"   请在浏览器中打开查看")

if __name__ == '__main__':
    generate_html_report()
