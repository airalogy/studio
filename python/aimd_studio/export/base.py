"""
导出器基类
"""

from abc import ABC, abstractmethod
from typing import Any, Optional
from pathlib import Path
from pydantic import BaseModel
import json


class ExportConfig(BaseModel):
    """导出配置"""
    title: str = "实验报告"
    author: Optional[str] = None
    date: Optional[str] = None
    template: Optional[str] = None  # 自定义模板路径
    include_empty: bool = False     # 是否包含空值字段
    language: str = "zh"            # 语言 zh/en


class ExportResult(BaseModel):
    """导出结果"""
    success: bool
    output_path: Optional[str] = None
    output_bytes: Optional[bytes] = None
    error: Optional[str] = None
    

class BaseExporter(ABC):
    """导出器基类"""
    
    def __init__(self, config: ExportConfig = None):
        self.config = config or ExportConfig()
    
    @abstractmethod
    def export(
        self,
        data: dict[str, Any],
        aimd_content: str = None,
        output_path: str = None,
    ) -> ExportResult:
        """
        导出数据
        
        Args:
            data: 变量数据 (VarModel 的 dict 形式)
            aimd_content: 原始 AIMD 文档内容 (可选)
            output_path: 输出文件路径 (可选，不提供则返回 bytes)
        
        Returns:
            ExportResult
        """
        pass
    
    def _filter_data(self, data: dict) -> dict:
        """过滤数据，移除空值（如果配置要求）"""
        if self.config.include_empty:
            return data
        return {k: v for k, v in data.items() if v is not None and v != ""}
    
    def _save_or_return(self, content: bytes, output_path: str = None) -> ExportResult:
        """保存到文件或返回 bytes"""
        if output_path:
            Path(output_path).write_bytes(content)
            return ExportResult(success=True, output_path=output_path)
        return ExportResult(success=True, output_bytes=content)
