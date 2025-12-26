"""
CSV 导出器
"""

import csv
import io
from typing import Any
from .base import BaseExporter, ExportResult, ExportConfig


class CsvExporter(BaseExporter):
    """CSV 格式导出 - 适合表格数据"""
    
    def export(
        self,
        data: dict[str, Any],
        aimd_content: str = None,
        output_path: str = None,
        table_field: str = None,  # 指定要导出的表格字段
    ) -> ExportResult:
        try:
            output = io.StringIO()
            
            if table_field and table_field in data:
                # 导出指定的表格字段
                table_data = data[table_field]
                if isinstance(table_data, list) and len(table_data) > 0:
                    writer = csv.DictWriter(output, fieldnames=table_data[0].keys())
                    writer.writeheader()
                    writer.writerows(table_data)
            else:
                # 导出所有标量字段
                filtered = self._filter_data(data)
                scalar_data = {
                    k: v for k, v in filtered.items() 
                    if not isinstance(v, (list, dict))
                }
                writer = csv.writer(output)
                writer.writerow(["字段", "值"])
                for key, value in scalar_data.items():
                    writer.writerow([key, value])
            
            content = output.getvalue().encode("utf-8-sig")  # BOM for Excel
            return self._save_or_return(content, output_path)
            
        except Exception as e:
            return ExportResult(success=False, error=str(e))


def export_csv(
    data: dict[str, Any],
    output_path: str = None,
    table_field: str = None,
    config: ExportConfig = None,
) -> ExportResult:
    """导出为 CSV 格式"""
    exporter = CsvExporter(config)
    return exporter.export(data, output_path=output_path, table_field=table_field)
