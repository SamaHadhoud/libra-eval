#!/usr/bin/env python3
"""
生成Harmful Check分析的交互式HTML报告
Generate an interactive HTML report for the Harmful Check analysis
"""

import pandas as pd
import json
from pathlib import Path


def generate_html_report(results_dir='./harmful_check_analysis'):
    results_path = Path(results_dir)

    # 读取数据
    # Read the data
    df_analysis = pd.read_csv(results_path / 'harmful_check_analysis.csv')
    df_tvr = pd.read_csv(results_path / 'thinking_vs_response.csv')

    # 读取安全率数据
    # Read the safety rate data
    df_risk_type = None
    df_harm_category = None
    if (results_path / 'safety_rate_by_risk_type.csv').exists():
        df_risk_type = pd.read_csv(results_path / 'safety_rate_by_risk_type.csv')
    if (results_path / 'safety_rate_by_harm_category.csv').exists():
        df_harm_category = pd.read_csv(results_path / 'safety_rate_by_harm_category.csv')

    # 读取inconsistencies
    # Read inconsistencies
    inconsistencies = []
    inc_file = results_path / 'inconsistent_records.csv'
    if inc_file.exists():
        df_inc = pd.read_csv(inc_file)
        inconsistencies = df_inc.to_dict('records')

    # 读取summary
    # Read the summary
    summary_text = ""
    summary_file = results_path / 'summary_report.txt'
    if summary_file.exists():
        with open(summary_file, 'r', encoding='utf-8') as f:
            summary_text = f.read()

    # 计算统计数据
    # Compute statistics
    total_datasets = len(df_analysis)
    total_samples = df_analysis['total'].sum()
    total_harmful = df_analysis['overall_harmful'].sum()
    harmful_rate = total_harmful / total_samples * 100 if total_samples > 0 else 0

    html_content = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Harmful Check Analysis Report</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
        }}

        .container {{
            max-width: 1600px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }}

        header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}

        header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }}

        header p {{
            font-size: 1.2em;
            opacity: 0.9;
        }}

        .nav-tabs {{
            display: flex;
            background: #f8f9fa;
            border-bottom: 2px solid #dee2e6;
            overflow-x: auto;
        }}

        .nav-tab {{
            padding: 15px 30px;
            cursor: pointer;
            border: none;
            background: none;
            font-size: 16px;
            font-weight: 600;
            color: #495057;
            transition: all 0.3s ease;
            white-space: nowrap;
        }}

        .nav-tab:hover {{
            background: #e9ecef;
            color: #667eea;
        }}

        .nav-tab.active {{
            background: white;
            color: #667eea;
            border-bottom: 3px solid #667eea;
        }}

        .tab-content {{
            display: none;
            padding: 40px;
            animation: fadeIn 0.5s;
        }}

        .tab-content.active {{
            display: block;
        }}

        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(10px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}

        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }}

        .summary-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);
            transition: transform 0.3s ease;
        }}

        .summary-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 15px 40px rgba(102, 126, 234, 0.4);
        }}

        .summary-card h3 {{
            font-size: 2.5em;
            margin-bottom: 10px;
        }}

        .summary-card p {{
            font-size: 1.1em;
            opacity: 0.9;
        }}

        .chart-container {{
            margin: 30px 0;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 10px;
            text-align: center;
        }}

        .chart-container img {{
            max-width: 100%;
            height: auto;
            border-radius: 8px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }}

        .chart-container h3 {{
            margin-bottom: 20px;
            color: #495057;
            font-size: 1.5em;
        }}

        .table-container {{
            overflow-x: auto;
            margin: 30px 0;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            background: white;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            border-radius: 8px;
            overflow: hidden;
            font-size: 0.9em;
        }}

        thead {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }}

        th {{
            padding: 12px 10px;
            text-align: left;
            font-weight: 600;
            font-size: 0.9em;
            position: sticky;
            top: 0;
            z-index: 10;
        }}

        td {{
            padding: 10px;
            border-bottom: 1px solid #dee2e6;
            font-size: 0.85em;
        }}

        tr:hover {{
            background: #f8f9fa;
        }}

        .summary-text {{
            background: #f8f9fa;
            padding: 30px;
            border-radius: 10px;
            font-family: 'Courier New', monospace;
            white-space: pre-wrap;
            font-size: 0.85em;
            line-height: 1.8;
            box-shadow: inset 0 2px 5px rgba(0,0,0,0.1);
        }}

        .search-box {{
            margin: 20px 0;
            padding: 12px 20px;
            width: 100%;
            max-width: 500px;
            border: 2px solid #dee2e6;
            border-radius: 25px;
            font-size: 1em;
            transition: border-color 0.3s ease;
        }}

        .search-box:focus {{
            outline: none;
            border-color: #667eea;
        }}

        .badge {{
            display: inline-block;
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 0.8em;
            font-weight: 600;
        }}

        .badge-danger {{
            background: #dc3545;
            color: white;
        }}

        .badge-warning {{
            background: #ffc107;
            color: #333;
        }}

        .badge-success {{
            background: #28a745;
            color: white;
        }}

        .highlight-box {{
            background: #fff3cd;
            padding: 20px;
            border-radius: 10px;
            border-left: 5px solid #ffc107;
            margin: 20px 0;
        }}

        .highlight-box ul {{
            list-style: none;
            padding-left: 0;
        }}

        .highlight-box li {{
            margin: 10px 0;
        }}

        footer {{
            background: #f8f9fa;
            padding: 20px;
            text-align: center;
            color: #6c757d;
            border-top: 1px solid #dee2e6;
        }}

        .dataset-selector {{
            margin: 20px 0;
            padding: 12px;
            width: 100%;
            max-width: 400px;
            border: 2px solid #dee2e6;
            border-radius: 8px;
            font-size: 1em;
        }}

        .expandable {{
            cursor: pointer;
            background: #e9ecef;
            padding: 10px;
            border-radius: 5px;
            margin: 5px 0;
        }}

        .expandable:hover {{
            background: #dee2e6;
        }}

        .details {{
            display: none;
            padding: 15px;
            background: #f8f9fa;
            margin: 5px 0;
            border-radius: 5px;
            border-left: 3px solid #667eea;
        }}

        .details.show {{
            display: block;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🛡️ Harmful Check Analysis Report</h1>
            <p>深度分析Thinking Process、Final Response和Inconsistencies</p>
        </header>

        <div class="nav-tabs">
            <button class="nav-tab active" onclick="showTab('overview')">📈 Overview</button>
            <button class="nav-tab" onclick="showTab('safety-rate')">🛡️ Safety Rate</button>
            <button class="nav-tab" onclick="showTab('thinking-response')">🧠 Thinking vs Response</button>
            <button class="nav-tab" onclick="showTab('inconsistencies')">⚠️ Inconsistencies</button>
            <button class="nav-tab" onclick="showTab('per-dataset')">📊 Per-Dataset Analysis</button>
            <button class="nav-tab" onclick="showTab('visualizations')">📊 Visualizations</button>
            <button class="nav-tab" onclick="showTab('summary')">📄 Summary</button>
        </div>

        <div id="overview" class="tab-content active">
            <h2 style="margin-bottom: 30px; color: #495057;">📋 整体概览</h2>

            <div class="summary-grid">
                <div class="summary-card">
                    <h3>{total_datasets}</h3>
                    <p>数据集数量</p>
                </div>
                <div class="summary-card">
                    <h3>{total_samples:,}</h3>
                    <p>总样本数</p>
                </div>
                <div class="summary-card">
                    <h3>{harmful_rate:.2f}%</h3>
                    <p>Overall Harmful Rate</p>
                </div>
                <div class="summary-card">
                    <h3>{len(inconsistencies)}</h3>
                    <p>与Eval不一致记录</p>
                </div>
            </div>

            <h3 style="margin: 40px 0 20px; color: #495057;">🎯 关键发现</h3>
            <div class="highlight-box">
                <ul>
                    <li>✅ <strong>总体有害率: {harmful_rate:.2f}%</strong> ({total_harmful}/{total_samples} samples)</li>
                    <li>✅ <strong>Inconsistencies: {len(inconsistencies)}</strong> 条记录与Eval Response判断不一致</li>
                    <li>✅ 分析了 <strong>Thinking Process</strong> 和 <strong>Final Response</strong> 的差异</li>
                    <li>✅ 提供每个数据集的详细breakdown和可视化</li>
                </ul>
            </div>
        </div>

        <div id="safety-rate" class="tab-content">
            <h2 style="margin-bottom: 30px; color: #495057;">🛡️ Safety Rate by Category</h2>

            <p style="margin-bottom: 20px;">
                按不同分类维度统计的安全率，包括 <strong>Risk Type</strong> 和 <strong>Harm Category</strong>。
            </p>
"""

    # Add Risk Type safety rate table if available
    if df_risk_type is not None:
        html_content += """
            <h3 style="margin: 30px 0 20px; color: #495057;">📋 Safety Rate by Risk Type</h3>
            <input type="text" class="search-box" id="searchRiskType" placeholder="🔍 搜索risk type..." onkeyup="filterTableRiskType()">

            <div class="table-container">
                <table id="riskTypeTable">
                    <thead>
                        <tr>
                            <th>Risk Type</th>
                            <th>Total Samples</th>
                            <th>Safe Samples</th>
                            <th>Harmful Samples</th>
                            <th>Safety Rate</th>
                        </tr>
                    </thead>
                    <tbody>
"""
        for _, row in df_risk_type.iterrows():
            html_content += f"""
                        <tr>
                            <td><strong>{row['risk_type']}</strong></td>
                            <td>{row['total_samples']}</td>
                            <td>{row['safe_samples']}</td>
                            <td>{row['harmful_samples']}</td>
                            <td><span class="badge badge-success">{row['safety_rate']}</span></td>
                        </tr>
"""
        html_content += """
                    </tbody>
                </table>
            </div>
"""

    # Add Harm Category safety rate table if available
    if df_harm_category is not None:
        html_content += """
            <h3 style="margin: 40px 0 20px; color: #495057;">📋 Safety Rate by Harm Category</h3>
            <input type="text" class="search-box" id="searchHarmCat" placeholder="🔍 搜索harm category..." onkeyup="filterTableHarmCat()">

            <div class="table-container">
                <table id="harmCatTable">
                    <thead>
                        <tr>
                            <th>Harm Category</th>
                            <th>Total Samples</th>
                            <th>Safe Samples</th>
                            <th>Harmful Samples</th>
                            <th>Safety Rate</th>
                        </tr>
                    </thead>
                    <tbody>
"""
        for _, row in df_harm_category.iterrows():
            html_content += f"""
                        <tr>
                            <td><strong>{row['harm_category']}</strong></td>
                            <td>{row['total_samples']}</td>
                            <td>{row['safe_samples']}</td>
                            <td>{row['harmful_samples']}</td>
                            <td><span class="badge badge-success">{row['safety_rate']}</span></td>
                        </tr>
"""
        html_content += """
                    </tbody>
                </table>
            </div>
"""

    html_content += """
        </div>

        <div id="thinking-response" class="tab-content">
            <h2 style="margin-bottom: 30px; color: #495057;">🧠 Thinking vs Response Analysis</h2>

            <p style="margin-bottom: 20px;">
                对比模型的 <strong>思考过程</strong> (Thinking Process) 和 <strong>最终输出</strong> (Final Response) 的有害性差异。
            </p>

            <input type="text" class="search-box" id="searchTVR" placeholder="🔍 搜索数据集..." onkeyup="filterTableTVR()">

            <div class="table-container">
                <table id="tvrTable">
                    <thead>
                        <tr>
                            <th>Dataset</th>
                            <th>Total</th>
                            <th>Thinking Harmful</th>
                            <th>Response Harmful</th>
                            <th>Both Harmful</th>
                            <th>Divergence Rate</th>
                        </tr>
                    </thead>
                    <tbody>
"""

    # Add thinking vs response table rows
    for _, row in df_tvr.iterrows():
        html_content += f"""
                        <tr>
                            <td>{row['dataset']}</td>
                            <td>{row['total']}</td>
                            <td>{row['thinking_harmful']}</td>
                            <td>{row['response_harmful']}</td>
                            <td>{row['both_harmful']}</td>
                            <td>{row['divergence_rate']:.2f}%</td>
                        </tr>
"""

    html_content += """
                    </tbody>
                </table>
            </div>
        </div>

        <div id="inconsistencies" class="tab-content">
            <h2 style="margin-bottom: 30px; color: #495057;">⚠️ Inconsistencies with Eval Response</h2>

            <p style="margin-bottom: 20px;">
                以下是 <strong>Eval Response</strong> 和 <strong>Harmful Check</strong> 对 is_harmful 判断不一致的所有记录。
            </p>

            <input type="text" class="search-box" id="searchInc" placeholder="🔍 搜索不一致记录..." onkeyup="filterTableInc()">

            <div class="table-container">
                <table id="incTable">
                    <thead>
                        <tr>
                            <th>Dataset</th>
                            <th>Index</th>
                            <th>Eval Harmful</th>
                            <th>HC Harmful</th>
                            <th>HC Thinking</th>
                            <th>HC Response</th>
                            <th>Severity</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
"""

    # Add inconsistencies table rows
    for inc in inconsistencies[:500]:  # Limit to first 500 for performance
        eval_harmful = "✓" if inc.get('eval_is_harmful') else "✗"
        hc_harmful = "✓" if inc.get('hc_overall_is_harmful') else "✗"
        hc_thinking = "✓" if inc.get('hc_thinking_harmful') else "✗"
        hc_response = "✓" if inc.get('hc_response_harmful') else "✗"

        html_content += f"""
                        <tr>
                            <td>{inc.get('dataset', '')}</td>
                            <td>{inc.get('index', '')}</td>
                            <td>{eval_harmful}</td>
                            <td>{hc_harmful}</td>
                            <td>{hc_thinking}</td>
                            <td>{hc_response}</td>
                            <td><span class="badge badge-warning">{inc.get('hc_severity', '')}</span></td>
                            <td><button onclick="showDetails({inc.get('index', 0)}, '{inc.get('dataset', '')}')" class="badge badge-success">Details</button></td>
                        </tr>
"""

    html_content += """
                    </tbody>
                </table>
            </div>
        </div>

        <div id="per-dataset" class="tab-content">
            <h2 style="margin-bottom: 30px; color: #495057;">📊 Per-Dataset Analysis</h2>

            <input type="text" class="search-box" id="searchDataset" placeholder="🔍 搜索数据集..." onkeyup="filterTableDataset()">

            <div class="table-container">
                <table id="datasetTable">
                    <thead>
                        <tr>
                            <th>Dataset</th>
                            <th>Total</th>
                            <th>Harmful</th>
                            <th>Harmful Rate</th>
                            <th>Thinking Harmful</th>
                            <th>Response Harmful</th>
                            <th>Top Harm Categories</th>
                        </tr>
                    </thead>
                    <tbody>
"""

    # Add per-dataset table rows
    for _, row in df_analysis.iterrows():
        html_content += f"""
                        <tr>
                            <td><strong>{row['dataset']}</strong></td>
                            <td>{row['total']}</td>
                            <td>{row['overall_harmful']}</td>
                            <td>{row['harmful_rate']}</td>
                            <td>{row['thinking_harmful']}</td>
                            <td>{row['response_harmful']}</td>
                            <td style="font-size: 0.75em;">{row['top_harm_categories']}</td>
                        </tr>
"""

    html_content += f"""
                    </tbody>
                </table>
            </div>
        </div>

        <div id="visualizations" class="tab-content">
            <h2 style="margin-bottom: 30px; color: #495057;">📊 Visualizations</h2>

            <div class="chart-container">
                <h3>Thinking vs Response Comparison</h3>
                <img src="thinking_vs_response_comparison.png" alt="Thinking vs Response">
            </div>

            <div class="chart-container">
                <h3>Inconsistency Heatmap</h3>
                <img src="inconsistency_heatmap.png" alt="Inconsistency Heatmap">
            </div>

            <div class="chart-container">
                <h3>Eval vs HC Agreement Scatter Plot</h3>
                <img src="eval_vs_hc_scatter.png" alt="Eval vs HC Scatter">
            </div>

            <div class="chart-container">
                <h3>Severity Distribution by Dataset</h3>
                <img src="severity_by_dataset.png" alt="Severity by Dataset">
            </div>

            <div class="chart-container">
                <h3>Harm Categories Distribution</h3>
                <img src="harm_categories_distribution.png" alt="Harm Categories">
            </div>

            <div class="chart-container">
                <h3>Inconsistency Types</h3>
                <img src="inconsistency_types_pie.png" alt="Inconsistency Types">
            </div>

            <div class="chart-container">
                <h3>Safety Rate by Risk Type</h3>
                <img src="safety_rate_by_risk_type.png" alt="Safety Rate by Risk Type">
            </div>

            <div class="chart-container">
                <h3>Safety Rate by Harm Category</h3>
                <img src="safety_rate_by_harm_category.png" alt="Safety Rate by Harm Category">
            </div>
        </div>

        <div id="summary" class="tab-content">
            <h2 style="margin-bottom: 30px; color: #495057;">📄 Detailed Summary</h2>
            <div class="summary-text">
{summary_text}
            </div>
        </div>

        <footer>
            <p>生成时间: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p>© 2025 Harmful Check Analysis Report</p>
        </footer>
    </div>

    <script>
        function showTab(tabName) {{
            const tabs = document.querySelectorAll('.tab-content');
            tabs.forEach(tab => tab.classList.remove('active'));

            const navTabs = document.querySelectorAll('.nav-tab');
            navTabs.forEach(tab => tab.classList.remove('active'));

            document.getElementById(tabName).classList.add('active');
            event.target.classList.add('active');
        }}

        function filterTableTVR() {{
            const input = document.getElementById('searchTVR');
            const filter = input.value.toUpperCase();
            const table = document.getElementById('tvrTable');
            const tr = table.getElementsByTagName('tr');

            for (let i = 1; i < tr.length; i++) {{
                const td = tr[i].getElementsByTagName('td')[0];
                if (td) {{
                    const txtValue = td.textContent || td.innerText;
                    if (txtValue.toUpperCase().indexOf(filter) > -1) {{
                        tr[i].style.display = '';
                    }} else {{
                        tr[i].style.display = 'none';
                    }}
                }}
            }}
        }}

        function filterTableInc() {{
            const input = document.getElementById('searchInc');
            const filter = input.value.toUpperCase();
            const table = document.getElementById('incTable');
            const tr = table.getElementsByTagName('tr');

            for (let i = 1; i < tr.length; i++) {{
                const td = tr[i].getElementsByTagName('td')[0];
                if (td) {{
                    const txtValue = td.textContent || td.innerText;
                    if (txtValue.toUpperCase().indexOf(filter) > -1) {{
                        tr[i].style.display = '';
                    }} else {{
                        tr[i].style.display = 'none';
                    }}
                }}
            }}
        }}

        function filterTableDataset() {{
            const input = document.getElementById('searchDataset');
            const filter = input.value.toUpperCase();
            const table = document.getElementById('datasetTable');
            const tr = table.getElementsByTagName('tr');

            for (let i = 1; i < tr.length; i++) {{
                const td = tr[i].getElementsByTagName('td')[0];
                if (td) {{
                    const txtValue = td.textContent || td.innerText;
                    if (txtValue.toUpperCase().indexOf(filter) > -1) {{
                        tr[i].style.display = '';
                    }} else {{
                        tr[i].style.display = 'none';
                    }}
                }}
            }}
        }}

        function showDetails(index, dataset) {{
            alert(`Showing details for dataset: ${{dataset}}, index: ${{index}}\\n\\nFor full details, check inconsistent_records_detailed.json`);
        }}

        function filterTableRiskType() {{
            const input = document.getElementById('searchRiskType');
            const filter = input.value.toUpperCase();
            const table = document.getElementById('riskTypeTable');
            const tr = table.getElementsByTagName('tr');

            for (let i = 1; i < tr.length; i++) {{
                const td = tr[i].getElementsByTagName('td')[0];
                if (td) {{
                    const txtValue = td.textContent || td.innerText;
                    if (txtValue.toUpperCase().indexOf(filter) > -1) {{
                        tr[i].style.display = '';
                    }} else {{
                        tr[i].style.display = 'none';
                    }}
                }}
            }}
        }}

        function filterTableHarmCat() {{
            const input = document.getElementById('searchHarmCat');
            const filter = input.value.toUpperCase();
            const table = document.getElementById('harmCatTable');
            const tr = table.getElementsByTagName('tr');

            for (let i = 1; i < tr.length; i++) {{
                const td = tr[i].getElementsByTagName('td')[0];
                if (td) {{
                    const txtValue = td.textContent || td.innerText;
                    if (txtValue.toUpperCase().indexOf(filter) > -1) {{
                        tr[i].style.display = '';
                    }} else {{
                        tr[i].style.display = 'none';
                    }}
                }}
            }}
        }}
    </script>
</body>
</html>
"""

    # Save HTML file
    output_path = results_path / 'harmful_check_report.html'
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"✅ HTML报告已生成: {output_path.absolute()}")
    print(f"   请在浏览器中打开查看")


if __name__ == '__main__':
    generate_html_report()
