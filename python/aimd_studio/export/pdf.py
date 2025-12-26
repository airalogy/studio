"""
PDF 导出器
"""

from typing import Any
from .base import BaseExporter, ExportResult, ExportConfig


class PdfExporter(BaseExporter):
    """PDF 格式导出 - 实验报告"""
    
    def export(
        self,
        data: dict[str, Any],
        aimd_content: str = None,
        output_path: str = None,
    ) -> ExportResult:
        try:
            # 延迟导入
            try:
                from weasyprint import HTML, CSS
            except ImportError:
                return ExportResult(
                    success=False,
                    error="需要安装 weasyprint: pip install weasyprint"
                )
            
            # 生成 HTML
            html_content = self._generate_html(data, aimd_content)
            
            # 转换为 PDF
            html = HTML(string=html_content)
            css = CSS(string=self._get_pdf_css())
            
            if output_path:
                html.write_pdf(output_path, stylesheets=[css])
                return ExportResult(success=True, output_path=output_path)
            else:
                content = html.write_pdf(stylesheets=[css])
                return ExportResult(success=True, output_bytes=content)
                
        except Exception as e:
            return ExportResult(success=False, error=str(e))
    
    def _generate_html(self, data: dict, aimd_content: str = None) -> str:
        """生成 HTML 内容"""
        filtered = self._filter_data(data)
        
        # 基本信息表格
        info_rows = ""
        for key, value in filtered.items():
            if not isinstance(value, (list, dict)):
                info_rows += f"<tr><td>{key}</td><td>{value}</td></tr>\n"
        
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
                <h2>{key}</h2>
                <table>
                    <thead><tr>{header_row}</tr></thead>
                    <tbody>{data_rows}</tbody>
                </table>
                """
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>{self.config.title}</title>
        </head>
        <body>
            <h1>{self.config.title}</h1>
            <p class="meta">
                {f'作者: {self.config.author}' if self.config.author else ''}
                {f' | 日期: {self.config.date}' if self.config.date else ''}
            </p>
            
            <h2>基本信息</h2>
            <table>
                <thead><tr><th>字段</th><th>值</th></tr></thead>
                <tbody>{info_rows}</tbody>
            </table>
            
            {tables_html}
            
            <footer>
                <p>由 AIMD Studio 导出</p>
            </footer>
        </body>
        </html>
        """
    
    def _get_pdf_css(self) -> str:
        """PDF 样式"""
        return """
        @page {
            size: A4;
            margin: 2cm;
        }
        body {
            font-family: "Noto Sans SC", "Microsoft YaHei", sans-serif;
            font-size: 10pt;
            line-height: 1.6;
        }
        h1 {
            color: #333;
            border-bottom: 2px solid #333;
            padding-bottom: 10px;
        }
        h2 {
            color: #555;
            margin-top: 20px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 10px 0;
        }
        th, td {
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }
        th {
            background-color: #f5f5f5;
            font-weight: bold;
        }
        tr:nth-child(even) {
            background-color: #fafafa;
        }
        .meta {
            color: #666;
            font-size: 9pt;
        }
        footer {
            margin-top: 30px;
            text-align: center;
            color: #999;
            font-size: 8pt;
        }
        """


def export_pdf(
    data: dict[str, Any],
    output_path: str = None,
    config: ExportConfig = None,
) -> ExportResult:
    """导出为 PDF 格式"""
    exporter = PdfExporter(config)
    return exporter.export(data, output_path=output_path)
