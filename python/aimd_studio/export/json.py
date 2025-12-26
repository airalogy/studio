"""
JSON 导出器
"""

import json
from typing import Any
from .base import BaseExporter, ExportResult, ExportConfig


class JsonExporter(BaseExporter):
    """JSON 格式导出"""
    
    def export(
        self,
        data: dict[str, Any],
        aimd_content: str = None,
        output_path: str = None,
    ) -> ExportResult:
        try:
            filtered = self._filter_data(data)
            
            output = {
                "metadata": {
                    "title": self.config.title,
                    "author": self.config.author,
                    "date": self.config.date,
                    "exported_by": "AIMD Studio",
                },
                "data": filtered,
            }
            
            content = json.dumps(output, ensure_ascii=False, indent=2).encode("utf-8")
            return self._save_or_return(content, output_path)
            
        except Exception as e:
            return ExportResult(success=False, error=str(e))


def export_json(
    data: dict[str, Any],
    output_path: str = None,
    config: ExportConfig = None,
) -> ExportResult:
    """导出为 JSON 格式"""
    exporter = JsonExporter(config)
    return exporter.export(data, output_path=output_path)
