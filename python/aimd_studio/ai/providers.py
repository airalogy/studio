"""
AI Provider 抽象层

支持多种 AI 服务提供商。
"""

from abc import ABC, abstractmethod
from typing import Optional, AsyncIterator
from pydantic import BaseModel
import os


class Message(BaseModel):
    """聊天消息"""
    role: str  # system, user, assistant
    content: str


class AIResponse(BaseModel):
    """AI 响应"""
    content: str
    model: str
    usage: Optional[dict] = None


class BaseProvider(ABC):
    """AI Provider 基类"""
    
    def __init__(self, api_key: str = None, base_url: str = None):
        self.api_key = api_key
        self.base_url = base_url
    
    @abstractmethod
    async def chat(
        self,
        messages: list[Message],
        model: str = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> AIResponse:
        """发送聊天请求"""
        pass
    
    @abstractmethod
    async def chat_stream(
        self,
        messages: list[Message],
        model: str = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> AsyncIterator[str]:
        """流式聊天"""
        pass


class OpenAIProvider(BaseProvider):
    """OpenAI / OpenAI 兼容 API"""
    
    def __init__(
        self,
        api_key: str = None,
        base_url: str = None,
        default_model: str = "gpt-4o-mini",
    ):
        super().__init__(
            api_key=api_key or os.environ.get("OPENAI_API_KEY"),
            base_url=base_url or os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1"),
        )
        self.default_model = default_model
    
    async def chat(
        self,
        messages: list[Message],
        model: str = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> AIResponse:
        try:
            import httpx
        except ImportError:
            raise ImportError("需要安装 httpx: pip install httpx")
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model or self.default_model,
                    "messages": [m.model_dump() for m in messages],
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                },
                timeout=60,
            )
            response.raise_for_status()
            data = response.json()
            
            return AIResponse(
                content=data["choices"][0]["message"]["content"],
                model=data["model"],
                usage=data.get("usage"),
            )
    
    async def chat_stream(
        self,
        messages: list[Message],
        model: str = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> AsyncIterator[str]:
        try:
            import httpx
        except ImportError:
            raise ImportError("需要安装 httpx: pip install httpx")
        
        async with httpx.AsyncClient() as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model or self.default_model,
                    "messages": [m.model_dump() for m in messages],
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "stream": True,
                },
                timeout=60,
            ) as response:
                async for line in response.aiter_lines():
                    if line.startswith("data: ") and line != "data: [DONE]":
                        import json
                        data = json.loads(line[6:])
                        if data["choices"][0].get("delta", {}).get("content"):
                            yield data["choices"][0]["delta"]["content"]


class GeminiProvider(BaseProvider):
    """Google Gemini API"""
    
    def __init__(
        self,
        api_key: str = None,
        base_url: str = None,
        default_model: str = "gemini-2.0-flash",
    ):
        super().__init__(
            api_key=api_key or os.environ.get("GEMINI_API_KEY"),
            base_url=base_url or os.environ.get("GEMINI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta"),
        )
        self.default_model = default_model
    
    async def chat(
        self,
        messages: list[Message],
        model: str = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> AIResponse:
        try:
            import httpx
        except ImportError:
            raise ImportError("需要安装 httpx: pip install httpx")
        
        # 转换消息格式
        contents = []
        system_instruction = None
        
        for msg in messages:
            if msg.role == "system":
                system_instruction = msg.content
            else:
                contents.append({
                    "role": "user" if msg.role == "user" else "model",
                    "parts": [{"text": msg.content}]
                })
        
        model_name = model or self.default_model
        
        async with httpx.AsyncClient() as client:
            payload = {
                "contents": contents,
                "generationConfig": {
                    "temperature": temperature,
                    "maxOutputTokens": max_tokens,
                }
            }
            if system_instruction:
                payload["systemInstruction"] = {"parts": [{"text": system_instruction}]}
            
            response = await client.post(
                f"{self.base_url}/models/{model_name}:generateContent",
                params={"key": self.api_key},
                json=payload,
                timeout=60,
            )
            response.raise_for_status()
            data = response.json()
            
            return AIResponse(
                content=data["candidates"][0]["content"]["parts"][0]["text"],
                model=model_name,
                usage=data.get("usageMetadata"),
            )
    
    async def chat_stream(
        self,
        messages: list[Message],
        model: str = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> AsyncIterator[str]:
        # Gemini 流式实现
        # 简化版：先获取完整响应再 yield
        response = await self.chat(messages, model, temperature, max_tokens)
        yield response.content


class ClaudeProvider(BaseProvider):
    """Anthropic Claude API"""
    
    def __init__(
        self,
        api_key: str = None,
        base_url: str = None,
        default_model: str = "claude-3-5-sonnet-20241022",
    ):
        super().__init__(
            api_key=api_key or os.environ.get("ANTHROPIC_API_KEY"),
            base_url=base_url or "https://api.anthropic.com/v1",
        )
        self.default_model = default_model
    
    async def chat(
        self,
        messages: list[Message],
        model: str = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> AIResponse:
        try:
            import httpx
        except ImportError:
            raise ImportError("需要安装 httpx: pip install httpx")
        
        # 提取 system message
        system = None
        chat_messages = []
        for msg in messages:
            if msg.role == "system":
                system = msg.content
            else:
                chat_messages.append({"role": msg.role, "content": msg.content})
        
        async with httpx.AsyncClient() as client:
            payload = {
                "model": model or self.default_model,
                "messages": chat_messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
            }
            if system:
                payload["system"] = system
            
            response = await client.post(
                f"{self.base_url}/messages",
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=60,
            )
            response.raise_for_status()
            data = response.json()
            
            return AIResponse(
                content=data["content"][0]["text"],
                model=data["model"],
                usage=data.get("usage"),
            )
    
    async def chat_stream(
        self,
        messages: list[Message],
        model: str = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> AsyncIterator[str]:
        response = await self.chat(messages, model, temperature, max_tokens)
        yield response.content
