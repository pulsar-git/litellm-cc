# ClaudeCode Provider for LiteLLM

This document describes the ClaudeCode provider implementation for LiteLLM.

## Overview

ClaudeCode is a custom LiteLLM provider that wraps the Anthropic API with specific customizations for Claude Code (Anthropic's official CLI for Claude). It inherits all functionality from the Anthropic provider while adding:

- **System prompt injection**: Automatically prepends "You are Claude Code, Anthropic's official CLI for Claude." to every request
- **Custom authentication**: Uses `Authorization: Bearer {token}` instead of Anthropic's `x-api-key` header
- **Custom headers**: Includes Claude Code-specific headers for OAuth authentication
- **Model prefix**: Uses `claude-code/` prefix for routing (e.g., `claude-code/claude-opus-4-5-20251101`)

## Features

✅ **System Prompt Injection**: Every request gets the Claude Code system prompt prepended before user messages
✅ **OAuth-Style Authentication**: Uses `Authorization: Bearer {key}` header instead of `x-api-key`
✅ **Custom Headers**: Automatically adds Claude Code-specific headers
✅ **Dedicated Credentials**: `CLAUDE_CODE_API_KEY` and `CLAUDE_CODE_API_BASE` environment variables
✅ **Model Prefix**: `claude-code/*` format for routing
✅ **Route All Anthropic Models**: Optionally route all Anthropic models to ClaudeCode via environment variable
✅ **Full Anthropic Compatibility**: Inherits all Anthropic features (streaming, tools, vision, thinking, etc.)
✅ **UI Integration**: Available in LiteLLM proxy dashboard with model dropdown support

## Installation

The ClaudeCode provider is included in LiteLLM. No additional installation is required.

## Environment Variables

- `CLAUDE_CODE_API_KEY` - API key (required) - OAuth token from Claude Code
- `CLAUDE_CODE_API_BASE` - API base URL (optional, defaults to `https://api.anthropic.com`)
- `CLAUDE_CODE_CUSTOM_HEADERS` - JSON object with custom headers (optional)
- `LITELLM_CLAUDE_CODE_DISABLE_URL_SUFFIX` - Disable auto-appending `/v1/messages` (optional)
- `LITELLM_ROUTE_ANTHROPIC_TO_CLAUDE_CODE` - Route all Anthropic models to ClaudeCode (optional, set to `True`)

## Usage

### UI configuration to route anthropic to claude_code
Model Name: claude_code/*
LiteLLM Model Name: claude_code/*

### Basic Usage

```python
import litellm
import os

os.environ["CLAUDE_CODE_API_KEY"] = "sk-ant-oat01-..."

response = litellm.completion(
    model="claude-code/claude-opus-4-5-20251101",
    messages=[{"role": "user", "content": "Hello!"}]
)

print(response.choices[0].message.content)
```

### With Custom Headers

```python
import os
import json

# Set custom headers via environment variable
os.environ["CLAUDE_CODE_CUSTOM_HEADERS"] = json.dumps({
    "X-Custom-Header": "value"
})

# Or pass via extra_headers parameter
response = litellm.completion(
    model="claude-code/claude-3-5-sonnet-20241022",
    messages=[{"role": "user", "content": "Hello!"}],
    extra_headers={
        "X-Custom-Header": "value"
    }
)
```

### Routing All Anthropic Models to ClaudeCode

You can route **all standard Anthropic models** (without the `claude-code/` prefix) to the ClaudeCode provider by setting an environment variable:

```python
import litellm
import os

# Enable routing: all Anthropic models → ClaudeCode provider
os.environ["LITELLM_ROUTE_ANTHROPIC_TO_CLAUDE_CODE"] = "True"
os.environ["CLAUDE_CODE_API_KEY"] = "sk-ant-oat01-..."

# Now you can use standard Anthropic model names
response = litellm.completion(
    model="claude-3-5-sonnet-20241022",  # No claude-code/ prefix needed!
    messages=[{"role": "user", "content": "Hello!"}]
)

print(response.choices[0].message.content)
# This request will:
# 1. Route to ClaudeCode provider (not Anthropic)
# 2. Include ClaudeCode system prompt
# 3. Use Authorization: Bearer header
# 4. Include all ClaudeCode custom headers
```

**Use cases:**
- Migrate existing Anthropic code to ClaudeCode without changing model names
- Use ClaudeCode as a drop-in replacement for Anthropic API
- Apply ClaudeCode features (system prompt, OAuth auth) to all Claude models

**How it works:**
- When `LITELLM_ROUTE_ANTHROPIC_TO_CLAUDE_CODE=True`, any model in `litellm.anthropic_models` gets routed to `claude_code` provider
- The `claude-code/` prefix still works and always routes to ClaudeCode
- Anthropic text completion models are not affected (still route to `anthropic_text`)

### Async Usage

```python
import litellm
import asyncio
import os

os.environ["CLAUDE_CODE_API_KEY"] = "sk-ant-oat01-..."

async def main():
    response = await litellm.acompletion(
        model="claude-code/claude-haiku-4-5-20251001",
        messages=[{"role": "user", "content": "Hello!"}]
    )
    print(response.choices[0].message.content)

asyncio.run(main())
```

### Streaming

```python
import litellm
import os

os.environ["CLAUDE_CODE_API_KEY"] = "sk-ant-oat01-..."

response = litellm.completion(
    model="claude-code/claude-sonnet-4-5-20250929",
    messages=[{"role": "user", "content": "Write a poem"}],
    stream=True
)

for chunk in response:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="")
```

## Available Models

The following models are available with the `claude-code/` prefix:

- `claude-code/claude-opus-4-5-20251101` - Claude Opus 4.5
- `claude-code/claude-haiku-4-5-20251001` - Claude Haiku 4.5
- `claude-code/claude-sonnet-4-5-20250929` - Claude Sonnet 4.5
- `claude-code/claude-opus-4-1-20250805` - Claude Opus 4.1
- `claude-code/claude-opus-4-20250514` - Claude Opus 4
- `claude-code/claude-sonnet-4-20250514` - Claude Sonnet 4
- `claude-code/claude-3-7-sonnet-20250219` - Claude Sonnet 3.7
- `claude-code/claude-3-5-haiku-20241022` - Claude Haiku 3.5
- `claude-code/claude-3-haiku-20240307` - Claude Haiku 3

You can also use the wildcard `claude-code/*` to allow all Claude Code models.

## API Request Format

### Headers Sent

When using ClaudeCode provider, the following headers are automatically included:

```http
authorization: Bearer sk-ant-oat01-...
anthropic-version: 2023-06-01
anthropic-beta: oauth-2025-04-20,interleaved-thinking-2025-05-14
anthropic-dangerous-direct-browser-access: true
user-agent: claude-cli/2.0.75 (external, cli)
x-app: cli
content-type: application/json
accept: application/json
```

**Note**: The `x-api-key` header used by standard Anthropic provider is **NOT** included.

### Request Body

```json
{
  "model": "claude-opus-4-5-20251101",
  "messages": [
    {
      "role": "user",
      "content": [{"type": "text", "text": "Hello!"}]
    }
  ],
  "system": [
    {
      "type": "text",
      "text": "You are Claude Code, Anthropic's official CLI for Claude."
    }
  ],
  "max_tokens": 1024
}
```

## UI Integration

### Adding ClaudeCode Provider in the Dashboard

1. Navigate to the LiteLLM proxy dashboard UI
2. Go to "Models and Endpoints" page
3. Click "Add Model"
4. Select "Claude Code" from the provider dropdown
5. Enter your API key (OAuth token)
6. (Optional) Enter custom API base URL
7. Select a model from the dropdown or use "All Claude Code Models (Wildcard)"
8. Save the model

### Provider Configuration

The ClaudeCode provider appears in the UI with:
- **Display Name**: "Claude Code"
- **Provider Key**: `ClaudeCode`
- **Backend Identifier**: `claude_code`
- **Logo**: Anthropic logo (reused)

### Model Dropdown

When you select "Claude Code" as the provider, the model dropdown shows:
- "All Claude Code Models (Wildcard)" - Uses `claude-code/*`
- Individual models listed above

**Important**: To see models in the UI, ensure the proxy is started with:
```bash
export LITELLM_LOCAL_MODEL_COST_MAP=True
```

## Configuration File (config.yaml)

```yaml
model_list:
  - model_name: claude-code-opus
    litellm_params:
      model: claude-code/claude-opus-4-5-20251101
      api_key: os.environ/CLAUDE_CODE_API_KEY

  - model_name: claude-code-haiku
    litellm_params:
      model: claude-code/claude-haiku-4-5-20251001
      api_key: os.environ/CLAUDE_CODE_API_KEY

  # Wildcard to allow all ClaudeCode models
  - model_name: claude-code/*
    litellm_params:
      model: claude-code/*
      api_key: os.environ/CLAUDE_CODE_API_KEY
```

## Implementation Details

### File Structure

```
litellm/
├── llms/
│   └── claude_code/
│       ├── __init__.py
│       └── chat/
│           ├── __init__.py
│           ├── handler.py          # ClaudeCodeChatCompletion
│           └── transformation.py   # ClaudeCodeConfig
├── types/utils.py                  # LlmProviders.CLAUDE_CODE enum
├── __init__.py                     # claude_code_key variable
├── main.py                         # Routing logic
├── utils.py                        # Provider config map
└── litellm_core_utils/
    └── get_llm_provider_logic.py  # Model prefix detection
```

### Key Classes

#### `ClaudeCodeConfig` (transformation.py)

Inherits from `AnthropicConfig` and overrides:

- `custom_llm_provider` - Returns `"claude_code"`
- `transform_request()` - Injects system prompt before user messages and strips `cache_control` from thinking blocks
- `validate_environment()` - Removes `x-api-key`, adds `Authorization: Bearer`, adds custom headers
- `get_api_key()` - Checks `CLAUDE_CODE_API_KEY`
- `get_api_base()` - Checks `CLAUDE_CODE_API_BASE`
- `get_supported_openai_params()` - Delegates to Anthropic to inherit all parameter support (including `reasoning_effort`)

#### `ClaudeCodeChatCompletion` (handler.py)

Inherits from `AnthropicChatCompletion` and overrides:

- `completion()` - Uses `ClaudeCodeConfig` for header validation and request transformation

### Model Routing

1. User calls: `litellm.completion(model="claude-code/claude-opus-4-5-20251101", ...)`
2. `get_llm_provider_logic.py` detects `claude-code/` prefix → routes to `claude_code` provider
3. `main.py` calls `claude_code_chat_completions.completion()`
4. Handler strips prefix: `claude-opus-4-5-20251101`
5. `ClaudeCodeConfig.transform_request()` injects system prompt
6. `ClaudeCodeConfig.validate_environment()` sets custom headers
7. Request sent to `https://api.anthropic.com/v1/messages`

## Testing

### Unit Tests

Run the test suite:

```bash
pytest tests/llm_translation/test_claude_code.py -v
```

Tests cover:
- Model prefix detection
- System prompt injection (empty system and with user system messages)
- Authorization header format (Bearer token)
- x-api-key header removal
- Custom headers from environment variable
- Custom headers from parameters
- Header precedence (params > env > base)
- API key/base environment variables

### Manual Testing

```bash
# Test basic completion
python test_cc.py

# Test with debug output
python test_cc_debug.py

# Test with curl
bash test_cc_curl.sh
```

## Differences from Standard Anthropic Provider

| Feature | Anthropic Provider | ClaudeCode Provider |
|---------|-------------------|---------------------|
| Model Prefix | `claude-*` | `claude-code/*` |
| Auth Header | `x-api-key: {key}` | `authorization: Bearer {key}` |
| API Key Env | `ANTHROPIC_API_KEY` | `CLAUDE_CODE_API_KEY` |
| API Base Env | `ANTHROPIC_API_BASE` | `CLAUDE_CODE_API_BASE` |
| System Prompt | User-defined only | Auto-injected + user-defined |
| Custom Headers | Standard Anthropic | OAuth + CLI headers |
| Provider ID | `anthropic` | `claude_code` |

## Troubleshooting

### Models not appearing in UI

1. Ensure proxy is started with:
   ```bash
   export LITELLM_LOCAL_MODEL_COST_MAP=True
   ```

2. Verify models are in the pricing file:
   ```bash
   python3 -c "
   import litellm
   models = {k: v for k, v in litellm.model_cost.items() if 'claude-code/' in k}
   print(f'Found {len(models)} claude-code models')
   "
   ```

### Authentication errors

If you see `invalid x-api-key` or authentication errors:
- Ensure you're using `CLAUDE_CODE_API_KEY` not `ANTHROPIC_API_KEY`
- Verify your token is an OAuth token (starts with `sk-ant-oat01-`)
- Check that the token has proper permissions

### Model not found errors

If you see `model: <name>` not found errors:
- Verify the model name is correct (check available models list)
- Ensure you're using the `claude-code/` prefix
- Try fetching current models from the API:
  ```bash
  python models.py
  ```

### Pydantic serialization warnings

The warning about "Expected 10 fields but got 5" is benign and comes from the base Anthropic provider. It doesn't affect functionality.

### Cache control in thinking blocks

ClaudeCode automatically strips `cache_control` from thinking blocks before sending to Anthropic API, as the API doesn't support caching within thinking blocks. This happens transparently in the `transform_request()` method.

### Thinking budget_tokens minimum

ClaudeCode automatically enforces Anthropic's minimum `budget_tokens` of 1024 for the `thinking` parameter. If a lower value is provided (e.g., `reasoning_effort="minimal"` maps to 128), it will be automatically increased to 1024 with a warning logged.

## Contributing

When making changes to the ClaudeCode provider:

1. **Don't modify Anthropic files** - Only override in ClaudeCode classes
2. **Run tests** - Ensure all 13 tests pass
3. **Test both sync and async** - Verify completion and acompletion work
4. **Test UI integration** - Ensure models appear in dropdown
5. **Update this documentation** - Keep CLAUDE_CODE.md current

## License

Same as LiteLLM - Apache 2.0

## Support

For issues specific to ClaudeCode provider:
- GitHub Issues: https://github.com/BerriAI/litellm/issues

For Claude Code CLI questions:
- Anthropic Documentation: https://docs.anthropic.com/
