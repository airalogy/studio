"""
AI Assistant - AIMD 智能助手

提供面向实验协议的 AI 辅助功能。
"""

from typing import Any, Optional
from .providers import BaseProvider, Message, OpenAIProvider


class AIAssistant:
    """AIMD 智能助手"""
    
    SYSTEM_PROMPT = """你是 AIMD Studio 的 AI 助手，专门帮助科研人员处理实验协议文档。

你的能力包括：
1. 根据实验上下文建议下一步操作
2. 为变量生成清晰的描述和标题
3. 检测数据中的异常值
4. 生成实验报告摘要
5. 优化实验协议结构

请用专业但易懂的语言回答，适当使用 Markdown 格式。"""
    
    def __init__(self, provider: BaseProvider = None):
        """
        初始化助手
        
        Args:
            provider: AI 服务提供商，默认使用 OpenAI
        """
        self.provider = provider or OpenAIProvider()
    
    async def suggest_next_step(
        self,
        current_step: str,
        completed_steps: list[str],
        context: dict[str, Any],
    ) -> str:
        """
        建议下一步操作
        
        Args:
            current_step: 当前步骤描述
            completed_steps: 已完成的步骤列表
            context: 当前实验数据上下文
        """
        messages = [
            Message(role="system", content=self.SYSTEM_PROMPT),
            Message(role="user", content=f"""
当前实验进度：
- 已完成步骤: {', '.join(completed_steps) if completed_steps else '无'}
- 当前步骤: {current_step}
- 当前数据: {self._format_context(context)}

请建议下一步应该做什么，并说明原因。
""")
        ]
        
        response = await self.provider.chat(messages)
        return response.content
    
    async def generate_description(
        self,
        var_name: str,
        var_type: str,
        context: dict[str, Any] = None,
    ) -> dict[str, str]:
        """
        为变量生成标题和描述
        
        Args:
            var_name: 变量名
            var_type: 变量类型
            context: 上下文信息
        
        Returns:
            {"title": "...", "description": "..."}
        """
        messages = [
            Message(role="system", content=self.SYSTEM_PROMPT),
            Message(role="user", content=f"""
请为以下实验变量生成中文标题和描述：

变量名: {var_name}
类型: {var_type}
上下文: {self._format_context(context) if context else '无'}

请以 JSON 格式返回：
{{"title": "简短的中文标题", "description": "详细的描述说明"}}
""")
        ]
        
        response = await self.provider.chat(messages, temperature=0.3)
        
        # 解析 JSON
        import json
        import re
        
        # 提取 JSON
        match = re.search(r'\{[^}]+\}', response.content)
        if match:
            return json.loads(match.group())
        
        return {"title": var_name, "description": ""}
    
    async def detect_anomalies(
        self,
        data: dict[str, Any],
        expected_ranges: dict[str, tuple] = None,
    ) -> list[dict]:
        """
        检测数据异常
        
        Args:
            data: 实验数据
            expected_ranges: 预期范围 {"field": (min, max)}
        
        Returns:
            异常列表 [{"field": "...", "value": ..., "issue": "..."}]
        """
        messages = [
            Message(role="system", content=self.SYSTEM_PROMPT),
            Message(role="user", content=f"""
请分析以下实验数据，检测可能的异常值：

数据: {self._format_context(data)}
预期范围: {expected_ranges or '未指定'}

请以 JSON 数组格式返回异常：
[{{"field": "字段名", "value": 当前值, "issue": "问题描述", "suggestion": "建议"}}]

如果没有异常，返回空数组 []
""")
        ]
        
        response = await self.provider.chat(messages, temperature=0.2)
        
        import json
        import re
        
        match = re.search(r'\[.*\]', response.content, re.DOTALL)
        if match:
            return json.loads(match.group())
        
        return []
    
    async def generate_summary(
        self,
        data: dict[str, Any],
        aimd_content: str = None,
    ) -> str:
        """
        生成实验报告摘要
        
        Args:
            data: 实验数据
            aimd_content: AIMD 文档内容
        """
        messages = [
            Message(role="system", content=self.SYSTEM_PROMPT),
            Message(role="user", content=f"""
请为以下实验数据生成一份简洁的摘要报告：

实验数据:
{self._format_context(data)}

{f'协议内容:\n{aimd_content[:2000]}...' if aimd_content else ''}

请生成：
1. 实验目的（1-2句）
2. 主要发现（3-5点）
3. 结论（1-2句）
""")
        ]
        
        response = await self.provider.chat(messages)
        return response.content
    
    async def optimize_protocol(
        self,
        aimd_content: str,
        issues: list[str] = None,
    ) -> str:
        """
        优化协议建议
        
        Args:
            aimd_content: AIMD 文档内容
            issues: 已知问题列表
        """
        messages = [
            Message(role="system", content=self.SYSTEM_PROMPT),
            Message(role="user", content=f"""
请分析以下 AIMD 协议并提供优化建议：

协议内容:
{aimd_content[:3000]}

{f'已知问题: {issues}' if issues else ''}

请从以下方面提供建议：
1. 步骤完整性
2. 变量定义清晰度
3. 检查点覆盖
4. 数据验证规则
5. 可读性改进
""")
        ]
        
        response = await self.provider.chat(messages)
        return response.content
    
    async def chat(self, user_message: str, context: dict[str, Any] = None) -> str:
        """
        通用对话
        
        Args:
            user_message: 用户消息
            context: 当前上下文
        """
        messages = [
            Message(role="system", content=self.SYSTEM_PROMPT),
        ]
        
        if context:
            messages.append(Message(
                role="system",
                content=f"当前实验数据上下文:\n{self._format_context(context)}"
            ))
        
        messages.append(Message(role="user", content=user_message))
        
        response = await self.provider.chat(messages)
        return response.content
    
    def _format_context(self, context: dict, max_items: int = 20) -> str:
        """格式化上下文数据"""
        if not context:
            return "{}"
        
        import json
        
        # 限制大小
        if len(context) > max_items:
            context = dict(list(context.items())[:max_items])
        
        # 截断长值
        formatted = {}
        for k, v in context.items():
            if isinstance(v, str) and len(v) > 200:
                formatted[k] = v[:200] + "..."
            elif isinstance(v, list) and len(v) > 5:
                formatted[k] = v[:5] + ["..."]
            else:
                formatted[k] = v
        
        return json.dumps(formatted, ensure_ascii=False, indent=2)
