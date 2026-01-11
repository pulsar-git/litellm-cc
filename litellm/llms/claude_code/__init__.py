from typing import Type
from .chat.transformation import ClaudeCodeConfig
from .chat.handler import ClaudeCodeChatCompletion

__all__ = ["ClaudeCodeConfig", "ClaudeCodeChatCompletion"]


def get_claude_code_config() -> Type[ClaudeCodeConfig]:
    return ClaudeCodeConfig
