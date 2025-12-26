"""
AIMD Studio - AI 辅助模块

提供 AI 驱动的智能功能：
- 自动补全实验步骤
- 智能生成变量描述
- 实验报告摘要生成
- 数据异常检测
- 协议优化建议
"""

from .assistant import AIAssistant
from .providers import OpenAIProvider, GeminiProvider, ClaudeProvider

__all__ = [
    "AIAssistant",
    "OpenAIProvider",
    "GeminiProvider", 
    "ClaudeProvider",
]
