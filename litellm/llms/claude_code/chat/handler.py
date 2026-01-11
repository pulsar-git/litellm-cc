"""ClaudeCode chat completion handler"""
import copy
import json
from typing import Callable, Optional, Union

import httpx

from litellm.llms.anthropic.chat.handler import AnthropicChatCompletion, make_sync_call
from litellm.llms.anthropic.common_utils import AnthropicError, process_anthropic_headers
from litellm.llms.custom_httpx.http_handler import HTTPHandler, _get_httpx_client
from litellm.types.utils import LlmProviders, ModelResponse
from litellm.utils import ProviderConfigManager


class ClaudeCodeChatCompletion(AnthropicChatCompletion):
    """
    ClaudeCode chat completion handler.

    Extends AnthropicChatCompletion to use ClaudeCodeConfig for header validation.
    """

    def completion(
        self,
        model: str,
        messages: list,
        api_base: str,
        custom_llm_provider: str,
        custom_prompt_dict: dict,
        model_response: ModelResponse,
        print_verbose: Callable,
        encoding,
        api_key,
        logging_obj,
        optional_params: dict,
        timeout: Union[float, httpx.Timeout],
        litellm_params: dict,
        acompletion=None,
        logger_fn=None,
        headers={},
        client=None,
    ):
        """
        Override completion to use ClaudeCodeConfig for header validation.
        """
        from litellm.litellm_core_utils.streaming_handler import CustomStreamWrapper

        optional_params = copy.deepcopy(optional_params)
        stream = optional_params.pop("stream", None)
        json_mode: bool = optional_params.pop("json_mode", False)
        is_vertex_request: bool = optional_params.pop("is_vertex_request", False)
        _is_function_call = False
        messages = copy.deepcopy(messages)

        # Get ClaudeCodeConfig for header validation
        config = ProviderConfigManager.get_provider_chat_config(
            model=model,
            provider=LlmProviders(custom_llm_provider),
        )
        if config is None:
            raise ValueError(
                f"Provider config not found for model: {model} and provider: {custom_llm_provider}"
            )

        # Use ClaudeCodeConfig for header validation
        headers = config.validate_environment(
            api_key=api_key,
            headers=headers,
            model=model,
            messages=messages,
            optional_params={**optional_params, "is_vertex_request": is_vertex_request},
            litellm_params=litellm_params,
        )

        data = config.transform_request(
            model=model,
            messages=messages,
            optional_params={**optional_params, "is_vertex_request": is_vertex_request},
            litellm_params=litellm_params,
            headers=headers,
        )

        ## LOGGING
        logging_obj.pre_call(
            input=messages,
            api_key=api_key,
            additional_args={
                "complete_input_dict": data,
                "api_base": api_base,
                "headers": headers,
            },
        )

        if acompletion is True:
            if stream is True:
                data["stream"] = stream
                return self.acompletion_stream_function(
                    model=model,
                    messages=messages,
                    data=data,
                    api_base=api_base,
                    custom_prompt_dict=custom_prompt_dict,
                    api_key=api_key,
                    headers=headers,
                    model_response=model_response,
                    print_verbose=print_verbose,
                    encoding=encoding,
                    logging_obj=logging_obj,
                    stream=stream,
                    _is_function_call=_is_function_call,
                    optional_params=optional_params,
                    timeout=timeout,
                    litellm_params=litellm_params,
                    logger_fn=logger_fn,
                    client=client,
                    json_mode=json_mode,
                )
            else:
                return self.acompletion_function(
                    model=model,
                    messages=messages,
                    data=data,
                    api_base=api_base,
                    custom_prompt_dict=custom_prompt_dict,
                    headers=headers,
                    model_response=model_response,
                    print_verbose=print_verbose,
                    encoding=encoding,
                    api_key=api_key,
                    logging_obj=logging_obj,
                    optional_params=optional_params,
                    stream=False,
                    _is_function_call=_is_function_call,
                    timeout=timeout,
                    litellm_params=litellm_params,
                    provider_config=config,
                    logger_fn=logger_fn,
                    client=client,
                    json_mode=json_mode,
                )
        else:
            # Sync completion
            if stream is True:
                # Streaming sync call
                data["stream"] = stream
                completion_stream, response_headers = make_sync_call(
                    client=client,
                    api_base=api_base,
                    headers=headers,
                    data=json.dumps(data),
                    model=model,
                    messages=messages,
                    logging_obj=logging_obj,
                    timeout=timeout,
                    json_mode=json_mode,
                )
                return CustomStreamWrapper(
                    completion_stream=completion_stream,
                    model=model,
                    custom_llm_provider="claude_code",
                    logging_obj=logging_obj,
                    _response_headers=process_anthropic_headers(response_headers),
                )
            else:
                # Non-streaming sync call
                if client is None or not isinstance(client, HTTPHandler):
                    client = _get_httpx_client(params={"timeout": timeout})

                try:
                    response = client.post(
                        api_base,
                        headers=headers,
                        data=json.dumps(data),
                        timeout=timeout,
                    )
                except Exception as e:
                    status_code = getattr(e, "status_code", 500)
                    error_headers = getattr(e, "headers", None)
                    error_text = getattr(e, "text", str(e))
                    error_response = getattr(e, "response", None)
                    if error_headers is None and error_response:
                        error_headers = getattr(error_response, "headers", None)
                    if error_response and hasattr(error_response, "text"):
                        error_text = getattr(error_response, "text", error_text)
                    raise AnthropicError(
                        message=error_text,
                        status_code=status_code,
                        headers=error_headers,
                    )

        return config.transform_response(
            model=model,
            raw_response=response,
            model_response=model_response,
            logging_obj=logging_obj,
            api_key=api_key,
            request_data=data,
            messages=messages,
            optional_params=optional_params,
            litellm_params=litellm_params,
            encoding=encoding,
            json_mode=json_mode,
        )
