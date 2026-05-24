import pytest
from unittest.mock import patch, MagicMock
from src.llm.claude_client import ClaudeClient


class TestClaudeClient:
    """ClaudeClient 单元测试"""

    def test_initialization(self):
        """测试客户端初始化"""
        client = ClaudeClient(model="claude-sonnet-4-20250514")
        assert client.model == "claude-sonnet-4-20250514"
        assert client.max_tokens == 4096
        assert client.temperature == 0.7

    def test_initialization_custom_params(self):
        """测试自定义参数初始化"""
        client = ClaudeClient(
            model="claude-sonnet-4-20250514",
            max_tokens=8192,
            temperature=0.5,
        )
        assert client.max_tokens == 8192
        assert client.temperature == 0.5

    @patch("src.llm.claude_client.Anthropic")
    def test_generate(self, mock_anthropic):
        """测试 generate 方法调用"""
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="测试回复")]
        mock_anthropic.return_value.messages.create.return_value = mock_response

        client = ClaudeClient()
        result = client.generate(
            system_prompt="你是专家",
            user_message="你好",
        )

        assert result == "测试回复"
        mock_anthropic.return_value.messages.create.assert_called_once()

    @patch("src.llm.claude_client.Anthropic")
    def test_generate_with_history(self, mock_anthropic):
        """测试带历史的生成"""
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="回复2")]
        mock_anthropic.return_value.messages.create.return_value = mock_response

        client = ClaudeClient()
        messages = [
            {"role": "user", "content": "你好"},
            {"role": "assistant", "content": "回复1"},
        ]
        result = client.generate_with_history(
            system_prompt="你是专家",
            messages=messages,
        )

        assert result == "回复2"