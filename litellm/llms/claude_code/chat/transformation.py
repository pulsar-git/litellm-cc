"""ClaudeCode provider - Anthropic API with system prompt injection"""
import json
from typing import Dict, List, Optional

import litellm
from litellm.llms.anthropic.chat.transformation import AnthropicConfig
from litellm.secret_managers.main import get_secret_str
from litellm.types.llms.anthropic import AnthropicSystemMessageContent
from litellm.types.llms.openai import AllMessageValues


class ClaudeCodeConfig(AnthropicConfig):
    """
    ClaudeCode provider - Uses Anthropic Messages API with:
    - Automatic system prompt injection
    - Custom header support (Authorization: Bearer format)
    - Dedicated environment variables
    """

    SYSTEM_PROMPT = "You are Claude Code, Anthropic's official CLI for Claude."

    @property
    def custom_llm_provider(self) -> Optional[str]:
        return "claude_code"

    def get_supported_openai_params(self, model: str) -> List[str]:
        """
        Override to delegate to Anthropic's param support.
        This ensures ClaudeCode supports all Anthropic params (including reasoning_effort).
        """
        # Get params from parent but pass 'anthropic' as provider for support checks
        # This allows us to inherit all Anthropic capabilities
        from litellm.llms.anthropic.chat.transformation import AnthropicConfig

        # Create a temporary Anthropic config instance to get supported params
        anthropic_config = AnthropicConfig()
        return anthropic_config.get_supported_openai_params(model=model)

    def transform_request(
        self,
        model: str,
        messages: List[AllMessageValues],
        optional_params: dict,
        litellm_params: dict,
        headers: dict,
    ) -> dict:
        """
        Override to inject ClaudeCode system prompt before user system messages.
        Also strips cache_control from thinking blocks (not supported by Anthropic API).
        """
        # Get base transformation
        data = super().transform_request(
            model=model,
            messages=messages,
            optional_params=optional_params,
            litellm_params=litellm_params,
            headers=headers,
        )

        # Inject ClaudeCode system prompt at the beginning
        claude_code_system_msg = AnthropicSystemMessageContent(
            type="text",
            text=self.SYSTEM_PROMPT,
        )

        # Prepend to existing system messages
        if "system" in data and isinstance(data["system"], list):
            data["system"] = [claude_code_system_msg] + data["system"]
        else:
            data["system"] = [claude_code_system_msg]

        # Strip cache_control from thinking blocks in messages
        # Anthropic API error: "messages.X.content.Y.thinking.cache_control: Extra inputs are not permitted"
        if "messages" in data and isinstance(data["messages"], list):
            for message in data["messages"]:
                if isinstance(message, dict) and "content" in message:
                    content = message["content"]
                    if isinstance(content, list):
                        for i, block in enumerate(content):
                            if isinstance(block, dict) and block.get("type") == "thinking":
                                if "cache_control" in block:
                                    # Remove cache_control from thinking blocks
                                    content[i] = {k: v for k, v in block.items() if k != "cache_control"}

        # Fix thinking.enabled.budget_tokens if it's below Anthropic's minimum of 1024
        # Anthropic API error: "thinking.enabled.budget_tokens: Input should be greater than or equal to 1024"
        if "thinking" in data and isinstance(data["thinking"], dict):
            thinking_param = data["thinking"]
            if thinking_param.get("type") == "enabled":
                budget_tokens = thinking_param.get("budget_tokens", 0)
                if budget_tokens < 1024:
                    litellm.verbose_logger.warning(
                        f"ClaudeCode: Increasing thinking.budget_tokens from {budget_tokens} to 1024 (Anthropic minimum)"
                    )
                    thinking_param["budget_tokens"] = 1024

        return data

    def validate_environment(
        self,
        headers: dict,
        model: str,
        messages: List[AllMessageValues],
        optional_params: dict,
        litellm_params: dict,
        api_key: Optional[str] = None,
        api_base: Optional[str] = None,
    ) -> Dict:
        """
        Override to:
        1. Replace Anthropic's x-api-key header with Authorization: Bearer {key}
        2. Inject custom headers from environment or parameters

        Merge order: base headers <- env custom headers <- param extra_headers
        """
        # Get base Anthropic headers (includes x-api-key, beta headers, etc.)
        base_headers = super().validate_environment(
            headers=headers,
            model=model,
            messages=messages,
            optional_params=optional_params,
            litellm_params=litellm_params,
            api_key=api_key,
            api_base=api_base,
        )

        # Remove Anthropic's x-api-key header
        base_headers.pop("x-api-key", None)

        # Add OpenAI-style Authorization header
        if api_key:
            base_headers["authorization"] = f"Bearer {api_key}"

        # Add ClaudeCode-specific default headers
        claude_code_headers = {
            "anthropic-beta": "oauth-2025-04-20,interleaved-thinking-2025-05-14",
            "anthropic-dangerous-direct-browser-access": "true",
            "user-agent": "claude-cli/2.0.75 (external, cli)",
            "x-app": "cli",
        }

        # Load custom headers from environment
        env_custom_headers = self._get_custom_headers_from_env()

        # Get custom headers from parameters
        param_extra_headers = optional_params.get("extra_headers", {})

        # Merge (later values override earlier)
        # Order: base <- claude_code defaults <- env <- params
        merged_headers = {
            **base_headers,
            **claude_code_headers,
            **env_custom_headers,
            **param_extra_headers,
        }

        if env_custom_headers or param_extra_headers:
            litellm.verbose_logger.debug("ClaudeCode: Applied custom headers")

        return merged_headers

    def _get_custom_headers_from_env(self) -> Dict[str, str]:
        """Load custom headers from CLAUDE_CODE_CUSTOM_HEADERS env var (JSON format)."""
        custom_headers_str = get_secret_str("CLAUDE_CODE_CUSTOM_HEADERS")
        if not custom_headers_str:
            return {}

        try:
            custom_headers = json.loads(custom_headers_str)
            if not isinstance(custom_headers, dict):
                litellm.verbose_logger.warning(
                    "CLAUDE_CODE_CUSTOM_HEADERS must be a JSON object"
                )
                return {}
            return custom_headers
        except json.JSONDecodeError as e:
            litellm.verbose_logger.warning(
                f"Failed to parse CLAUDE_CODE_CUSTOM_HEADERS: {e}"
            )
            return {}

    @staticmethod
    def get_api_base(api_base: Optional[str] = None) -> Optional[str]:
        """Check CLAUDE_CODE_API_BASE before Anthropic default."""
        return (
            api_base
            or get_secret_str("CLAUDE_CODE_API_BASE")
            or "https://api.anthropic.com"
        )

    @staticmethod
    def get_api_key(api_key: Optional[str] = None) -> Optional[str]:
        """
        Check CLAUDE_CODE_API_KEY first.
        The key is formatted as 'Authorization: Bearer {key}' header
        by ClaudeCode's validate_environment() override method.
        """
        return api_key or get_secret_str("CLAUDE_CODE_API_KEY")
