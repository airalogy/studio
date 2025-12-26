"""
Airalogy Mock - 本地模拟客户端

提供本地文件存储和记录管理，用于开发测试。
不依赖真实的 airalogy SDK，可独立运行。
"""

# 只导出本地客户端，不依赖 airalogy SDK
from .client import Airalogy, RecordSession

__version__ = "0.3.0"
__all__ = [
    "Airalogy",
    "RecordSession",
]
