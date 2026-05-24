import os
from typing import Optional
from anthropic import Anthropic, APIError, APIConnectionError, RateLimitError
from dotenv import load_dotenv

load_dotenv()


class ClaudeClient:
    """Claude API 客户端封装"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-sonnet-4-20250514",
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ):
        self.client = Anthropic(api_key=api_key or os.getenv("ANTHROPIC_API_KEY"))
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature

    def generate(
        self,
        system_prompt: str,
        user_message: str,
        temperature: Optional[float] = None,
    ) -> str:
        """生成文本回复"""
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=temperature or self.temperature,
                system=system_prompt,
                messages=[{"role": "user", "content": user_message}],
            )
            return response.content[0].text
        except RateLimitError as e:
            raise RuntimeError(f"API rate limit exceeded: {e}") from e
        except APIConnectionError as e:
            raise RuntimeError(f"API connection error: {e}") from e
        except APIError as e:
            raise RuntimeError(f"API error: {e}") from e

    def generate_with_history(
        self,
        system_prompt: str,
        messages: list[dict],
        temperature: Optional[float] = None,
    ) -> str:
        """生成带对话历史的回复"""
        formatted_messages = []
        for msg in messages:
            formatted_messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=temperature or self.temperature,
                system=system_prompt,
                messages=formatted_messages,
            )
            return response.content[0].text
        except RateLimitError as e:
            raise RuntimeError(f"API rate limit exceeded: {e}") from e
        except APIConnectionError as e:
            raise RuntimeError(f"API connection error: {e}") from e
        except APIError as e:
            raise RuntimeError(f"API error: {e}") from e