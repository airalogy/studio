"""
AIMD Studio - Python 后端模块

为 AIMD Studio VS Code Extension 提供：
- 数据导出 (export)
- AI 辅助 (ai)
- 自动计算 (assigner) - 基于 airalogy SDK
- 本地服务 (server)
"""

__version__ = "0.1.0"

from airalogy.assigner import assigner, AssignerResult, DefaultAssigner
from airalogy.models import CheckValue, StepValue
from airalogy import types

__all__ = [
    "assigner", "AssignerResult", "DefaultAssigner",
    "CheckValue", "StepValue", "types",
]
