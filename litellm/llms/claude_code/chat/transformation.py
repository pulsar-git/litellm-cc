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
