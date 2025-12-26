"""
HTML 导出器
"""

from typing import Any
from .base import BaseExporter, ExportResult, ExportConfig


class HtmlExporter(BaseExporter):
    """HTML 格式导出 - 静态网页"""
    
    def export(
        self,
        data: dict[str, Any],
        aimd_content: str = None,
        output_path: str = None,
    ) -> ExportResult:
        try:
            html_content = self._generate_html(data, aimd_content)
            content = html_content.encode("utf-8")
            return self._save_or_return(content, output_path)
            
        except Exception as e:
            return ExportResult(success=False, error=str(e))
    
    def _generate_html(self, data: dict, aimd_content: str = None) -> str:
        """生成完整的 HTML 页面"""
        filtered = self._filter_data(data)
        
        # 基本信息
        info_items = ""
        for key, value in filtered.items():
            if not isinstance(value, (list, dict)):
                info_items += f"""
                <div class="info-item">
                    <span class="label">{key}</span>
                    <span class="value">{value}</span>
                </div>
                """
        
        # 表格数据
        tables_html = ""
        for key, value in filtered.items():
            if isinstance(value, list) and len(value) > 0 and isinstance(value[0], dict):
                headers = list(value[0].keys())
                header_row = "".join(f"<th>{h}</th>" for h in headers)
                data_rows = ""
                for item in value:
                    cells = "".join(f"<td>{item.get(h, '')}</td>" for h in headers)
                    data_rows += f"<tr>{cells}</tr>\n"
                
                tables_html += f"""
                <section class="table-section">
                    <h2>{key}</h2>
                    <div class="table-wrapper">
                        <table>
                            <thead><tr>{header_row}</tr></thead>
                            <tbody>{data_rows}</tbody>
                        </table>
                    </div>
                </section>
                """
        
        return f"""
<!DOCTYPE html>
<html lang="{self.config.language}">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{self.config.title}</title>
    <style>
        :root {{
            --primary: #2563eb;
            --bg: #f8fafc;
            --card-bg: #ffffff;
            --text: #1e293b;
            --text-muted: #64748b;
            --border: #e2e8f0;
        }}
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: var(--bg);
            color: var(--text);
            line-height: 1.6;
            padding: 2rem;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        header {{
            margin-bottom: 2rem;
        }}
        h1 {{
            font-size: 2rem;
            font-weight: 600;
            margin-bottom: 0.5rem;
        }}
        .meta {{
            color: var(--text-muted);
            font-size: 0.875rem;
        }}
        h2 {{
            font-size: 1.25rem;
            font-weight: 600;
            margin-bottom: 1rem;
            color: var(--primary);
        }}
        .card {{
            background: var(--card-bg);
            border-radius: 8px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        .info-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 1rem;
        }}
        .info-item {{
            display: flex;
            flex-direction: column;
            padding: 0.75rem;
            background: var(--bg);
            border-radius: 4px;
        }}
        .info-item .label {{
            font-size: 0.75rem;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}
        .info-item .value {{
            font-size: 1rem;
            font-weight: 500;
            margin-top: 0.25rem;
        }}
        .table-wrapper {{
            overflow-x: auto;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        th, td {{
            padding: 0.75rem;
            text-align: left;
            border-bottom: 1px solid var(--border);
        }}
        th {{
            font-weight: 600;
            background: var(--bg);
            position: sticky;
            top: 0;
        }}
        tr:hover {{
            background: var(--bg);
        }}
        footer {{
            margin-top: 3rem;
            text-align: center;
            color: var(--text-muted);
            font-size: 0.75rem;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>{self.config.title}</h1>
            <p class="meta">
                {f'作者: {self.config.author}' if self.config.author else ''}
                {f' · 日期: {self.config.date}' if self.config.date else ''}
                · 由 AIMD Studio 导出
            </p>
        </header>
        
        <section class="card">
            <h2>基本信息</h2>
            <div class="info-grid">
                {info_items}
            </div>
        </section>
        
        {tables_html}
        
        <footer>
            <p>Powered by AIMD Studio & Airalogy</p>
        </footer>
    </div>
</body>
</html>
        """


def export_html(
    data: dict[str, Any],
    output_path: str = None,
    config: ExportConfig = None,
) -> ExportResult:
    """导出为 HTML 格式"""
    exporter = HtmlExporter(config)
    return exporter.export(data, output_path=output_path)
