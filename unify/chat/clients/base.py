# global
import requests
# noinspection PyProtectedMember
from openai._types import Headers, Query, Body
from openai.types.chat import (
    ChatCompletionToolParam,
    ChatCompletionToolChoiceOptionParam,
    ChatCompletionMessageParam,
    ChatCompletionStreamOptionsParam,
)
from openai.types.chat.completion_create_params import ResponseFormat
from abc import ABC, abstractmethod
from typing import Mapping, Dict, List, Optional, Union, Iterable
from typing_extensions import Self

# local
from unify import BASE_URL
from unify.types import Prompt
# noinspection PyProtectedMember
from unify.utils.helpers import _validate_api_key, _default


class _Client(ABC):
    """Base Abstract class for interacting with the Unify chat completions endpoint."""

    def __init__(
            self,
            *,
            system_message: Optional[str],
            messages: Optional[
                Union[List[ChatCompletionMessageParam],
                      Dict[str, List[ChatCompletionMessageParam]]]],
            frequency_penalty: Optional[float],
            logit_bias: Optional[Dict[str, int]],
            logprobs: Optional[bool],
            top_logprobs: Optional[int],
            max_completion_tokens: Optional[int],
            n: Optional[int],
            presence_penalty: Optional[float],
            response_format: Optional[ResponseFormat],
            seed: Optional[int],
            stop: Union[Optional[str], List[str]],
            stream: Optional[bool],
            stream_options: Optional[ChatCompletionStreamOptionsParam],
            temperature: Optional[float],
            top_p: Optional[float],
            tools: Optional[Iterable[ChatCompletionToolParam]],
            tool_choice: Optional[ChatCompletionToolChoiceOptionParam],
            parallel_tool_calls: Optional[bool],
            # platform arguments
            use_custom_keys: bool,
            tags: Optional[List[str]],
            drop_params: Optional[bool],
            region: Optional[str] = None,
            log_query_body: Optional[bool],
            log_response_body: Optional[bool],
            api_key: Optional[str],
            # python client arguments
            return_full_completion: bool,
            cache: bool,
            # passthrough arguments
            extra_headers: Optional[Headers],
            extra_query: Optional[Query],
            **kwargs,
    ) -> None:  # noqa: DAR101, DAR401
        self._api_key = _validate_api_key(api_key)
        self._system_message = None
        self.set_system_message(system_message)
        self._messages = None
        self.set_messages(messages)
        self._frequency_penalty = None
        self.set_frequency_penalty(frequency_penalty)
        self._logit_bias = None
        self.set_logit_bias(logit_bias)
        self._logprobs = None
        self.set_logprobs(logprobs)
        self._top_logprobs = None
        self.set_top_logprobs(top_logprobs)
        self._max_completion_tokens = None
        self.set_max_completion_tokens(max_completion_tokens)
        self._n = None
        self.set_n(n)
        self._presence_penalty = None
        self.set_presence_penalty(presence_penalty)
        self._response_format = None
        self.set_response_format(response_format)
        self._seed = None
        self.set_seed(seed)
        self._stop = None
        self.set_stop(stop)
        self._stream = None
        self.set_stream(stream)
        self._stream_options = None
        self.set_stream_options(stream_options)
        self._temperature = None
        self.set_temperature(temperature)
        self._top_p = None
        self.set_top_p(top_p)
        self._tools = None
        self.set_tools(tools)
        self._tool_choice = None
        self.set_tool_choice(tool_choice)
        self._parallel_tool_calls = None
        self.set_parallel_tool_calls(parallel_tool_calls)
        # platform arguments
        self._use_custom_keys = None
        self.set_use_custom_keys(use_custom_keys)
        self._tags = None
        self.set_tags(tags)
        self._drop_params = None
        self.set_drop_params(drop_params)
        self._region = None
        self.set_region(region)
        self._log_query_body = None
        self.set_log_query_body(log_query_body)
        self._log_response_body = None
        self.set_log_response_body(log_response_body)
        # python client arguments
        self._return_full_completion = None
        self.set_return_full_completion(return_full_completion)
        self._cache = None
        self.set_cache(cache)
        # passthrough arguments
        self._extra_headers = None
        self.set_extra_headers(extra_headers)
        self._extra_query = None
        self.set_extra_query(extra_query)
        self._extra_body = None
        self.set_extra_body(kwargs)

    # Properties #
    # -----------#

    @property
    def system_message(self) -> Optional[str]:
        """
        Get the default system message, if set.

        Returns:
            The default system message.
        """
        return self._system_message

    @property
    def messages(self) -> Optional[
        Union[List[ChatCompletionMessageParam],
              Dict[str, List[ChatCompletionMessageParam]]]]:
        """
        Get the default messages, if set.

        Returns:
            The default messages.
        """
        return self._messages

    @property
    def frequency_penalty(self) -> Optional[float]:
        """
        Get the default frequency penalty, if set.

        Returns:
            The default frequency penalty.
        """
        return self._frequency_penalty

    @property
    def logit_bias(self) -> Optional[Dict[str, int]]:
        """
        Get the default logit bias, if set.

        Returns:
            The default logit bias.
        """
        return self._logit_bias

    @property
    def logprobs(self) -> Optional[bool]:
        """
        Get the default logprobs, if set.

        Returns:
            The default logprobs.
        """
        return self._logprobs

    @property
    def top_logprobs(self) -> Optional[int]:
        """
        Get the default top logprobs, if set.

        Returns:
            The default top logprobs.
        """
        return self._top_logprobs

    @property
    def max_completion_tokens(self) -> Optional[int]:
        """
        Get the default max tokens, if set.

        Returns:
            The default max tokens.
        """
        return self._max_completion_tokens

    @property
    def n(self) -> Optional[int]:
        """
        Get the default n, if set.

        Returns:
            The default n value.
        """
        return self._n

    @property
    def presence_penalty(self) -> Optional[float]:
        """
        Get the default presence penalty, if set.

        Returns:
            The default presence penalty.
        """
        return self._presence_penalty

    @property
    def response_format(self) -> Optional[ResponseFormat]:
        """
        Get the default response format, if set.

        Returns:
            The default response format.
        """
        return self._response_format

    @property
    def seed(self) -> Optional[int]:
        """
        Get the default seed value, if set.

        Returns:
            The default seed value.
        """
        return self._seed

    @property
    def stop(self) -> Union[Optional[str], List[str]]:
        """
        Get the default stop value, if set.

        Returns:
            The default stop value.
        """
        return self._stop

    @property
    def stream(self) -> Optional[bool]:
        """
         Get the default stream bool, if set.

         Returns:
             The default stream bool.
         """
        return self._stream

    @property
    def stream_options(self) -> Optional[ChatCompletionStreamOptionsParam]:
        """
         Get the default stream options, if set.

         Returns:
             The default stream options.
         """
        return self._stream_options

    @property
    def temperature(self) -> Optional[float]:
        """
         Get the default temperature, if set.

         Returns:
             The default temperature.
         """
        return self._temperature

    @property
    def top_p(self) -> Optional[float]:
        """
         Get the default top p value, if set.

         Returns:
             The default top p value.
         """
        return self._top_p

    @property
    def tools(self) -> Optional[Iterable[ChatCompletionToolParam]]:
        """
         Get the default tools, if set.

         Returns:
             The default tools.
         """
        return self._tools

    @property
    def tool_choice(self) -> Optional[ChatCompletionToolChoiceOptionParam]:
        """
         Get the default tool choice, if set.

         Returns:
             The default tool choice.
         """
        return self._tool_choice

    @property
    def parallel_tool_calls(self) -> Optional[bool]:
        """
         Get the default parallel tool calls bool, if set.

         Returns:
             The default parallel tool calls bool.
         """
        return self._parallel_tool_calls

    @property
    def use_custom_keys(self) -> bool:
        """
         Get the default use custom keys bool, if set.

         Returns:
             The default use custom keys bool.
         """
        return self._use_custom_keys

    @property
    def tags(self) -> Optional[List[str]]:
        """
         Get the default tags, if set.

         Returns:
             The default tags.
         """
        return self._tags

    @property
    def drop_params(self) -> Optional[bool]:
        """
         Get the default drop_params bool, if set.

         Returns:
             The default drop_params bool.
         """
        return self._drop_params

    @property
    def region(self) -> Optional[str]:
        """
         Get the default region, if set.

         Returns:
             The default region.
         """
        return self._region

    @property
    def log_query_body(self) -> Optional[bool]:
        """
         Get the default log query body bool, if set.

         Returns:
             The default log query body bool.
         """
        return self._log_query_body

    @property
    def log_response_body(self) -> Optional[bool]:
        """
         Get the default log response body bool, if set.

         Returns:
             The default log response body bool.
         """
        return self._log_response_body

    @property
    def return_full_completion(self) -> bool:
        """
          Get the default return full completion bool.

          Returns:
              The default return full completion bool.
          """
        return self._return_full_completion

    @property
    def cache(self) -> bool:
        """
          Get default the cache bool.

          Returns:
              The default cache bool.
          """
        return self._cache

    @property
    def extra_headers(self) -> Optional[Headers]:
        """
         Get the default extra headers, if set.

         Returns:
             The default extra headers.
         """
        return self._extra_headers

    @property
    def extra_query(self) -> Optional[Query]:
        """
         Get the default extra query, if set.

         Returns:
             The default extra query.
         """
        return self._extra_query

    @property
    def extra_body(self) -> Optional[Mapping[str, str]]:
        """
         Get the default extra body, if set.

         Returns:
             The default extra body.
         """
        return self._extra_body

    @property
    def default_prompt(self) -> Prompt:
        """
        Get the default prompt, if set.

        Returns:
              The default prompt.
        """
        return Prompt(
            **{f: getattr(self, f) for f in Prompt.model_fields if
               hasattr(self, f) and getattr(self, f)}
        )

    # Setters #
    # --------#

    def set_system_message(self, value: str) -> Self:
        """
        Set the default system message.  # noqa: DAR101.

        Args:
            value: The default system message.

        Returns:
            This client, useful for chaining inplace calls.
        """
        self._system_message = value
        return self

    def set_messages(
            self,
            value: Union[List[ChatCompletionMessageParam],
                         Dict[str, List[ChatCompletionMessageParam]]]
    ) -> Self:
        """
        Set the default messages.  # noqa: DAR101.

        Args:
            value: The default messages.

        Returns:
            This client, useful for chaining inplace calls.
        """
        self._messages = value
        return self

    def set_frequency_penalty(self, value: float) -> Self:
        """
        Set the default frequency penalty.  # noqa: DAR101.

        Args:
            value: The default frequency penalty.

        Returns:
            This client, useful for chaining inplace calls.
        """
        self._frequency_penalty = value
        return self

    def set_logit_bias(self, value: Dict[str, int]) -> Self:
        """
        Set the default logit bias.  # noqa: DAR101.

        Args:
            value: The default logit bias.

        Returns:
            This client, useful for chaining inplace calls.
        """
        self._logit_bias = value
        return self

    def set_logprobs(self, value: bool) -> Self:
        """
        Set the default logprobs.  # noqa: DAR101.

        Args:
            value: The default logprobs.

        Returns:
            This client, useful for chaining inplace calls.
        """
        self._logprobs = value
        return self

    def set_top_logprobs(self, value: int) -> Self:
        """
        Set the default top logprobs.  # noqa: DAR101.

        Args:
            value: The default top logprobs.

        Returns:
            This client, useful for chaining inplace calls.
        """
        self._top_logprobs = value
        return self

    def set_max_completion_tokens(self, value: int) -> Self:
        """
        Set the default max tokens.  # noqa: DAR101.

        Args:
            value: The default max tokens.

        Returns:
            This client, useful for chaining inplace calls.
        """
        self._max_completion_tokens = value
        return self

    def set_n(self, value: int) -> Self:
        """
        Set the default n value.  # noqa: DAR101.

        Args:
            value: The default n value.

        Returns:
            This client, useful for chaining inplace calls.
        """
        self._n = value
        return self

    def set_presence_penalty(self, value: float) -> Self:
        """
        Set the default presence penalty.  # noqa: DAR101.

        Args:
            value: The default presence penalty.

        Returns:
            This client, useful for chaining inplace calls.
        """
        self._presence_penalty = value
        return self

    def set_response_format(self, value: ResponseFormat) -> Self:
        """
        Set the default response format.  # noqa: DAR101.

        Args:
            value: The default response format.

        Returns:
            This client, useful for chaining inplace calls.
        """
        self._response_format = value
        return self

    def set_seed(self, value: int) -> Self:
        """
        Set the default seed value.  # noqa: DAR101.

        Args:
            value: The default seed value.

        Returns:
            This client, useful for chaining inplace calls.
        """
        self._seed = value
        return self

    def set_stop(self, value: Union[str, List[str]]) -> Self:
        """
        Set the default stop value.  # noqa: DAR101.

        Args:
            value: The default stop value.

        Returns:
            This client, useful for chaining inplace calls.
        """
        self._stop = value
        return self

    def set_stream(self, value: bool) -> Self:
        """
        Set the default stream bool.  # noqa: DAR101.

        Args:
            value: The default stream bool.

        Returns:
            This client, useful for chaining inplace calls.
        """
        self._stream = value
        return self

    def set_stream_options(self, value: ChatCompletionStreamOptionsParam) -> Self:
        """
        Set the default stream options.  # noqa: DAR101.

        Args:
            value: The default stream options.

        Returns:
            This client, useful for chaining inplace calls.
        """
        self._stream_options = value
        return self

    def set_temperature(self, value: float) -> Self:
        """
        Set the default temperature.  # noqa: DAR101.

        Args:
            value: The default temperature.

        Returns:
            This client, useful for chaining inplace calls.
        """
        self._temperature = value
        return self

    def set_top_p(self, value: float) -> Self:
        """
        Set the default top p value.  # noqa: DAR101.

        Args:
            value: The default top p value.

        Returns:
            This client, useful for chaining inplace calls.
        """
        self._top_p = value
        return self

    def set_tools(self, value: Iterable[ChatCompletionToolParam]) -> Self:
        """
        Set the default tools.  # noqa: DAR101.

        Args:
            value: The default tools.

        Returns:
            This client, useful for chaining inplace calls.
        """
        self._tools = value
        return self

    def set_tool_choice(self, value: ChatCompletionToolChoiceOptionParam) -> Self:
        """
        Set the default tool choice.  # noqa: DAR101.

        Args:
            value: The default tool choice.

        Returns:
            This client, useful for chaining inplace calls.
        """
        self._tool_choice = value
        return self

    def set_parallel_tool_calls(self, value: bool) -> Self:
        """
        Set the default parallel tool calls bool.  # noqa: DAR101.

        Args:
            value: The default parallel tool calls bool.

        Returns:
            This client, useful for chaining inplace calls.
        """
        self._parallel_tool_calls = value
        return self

    def set_use_custom_keys(self, value: bool) -> Self:
        """
        Set the default use custom keys bool.  # noqa: DAR101.

        Args:
            value: The default use custom keys bool.

        Returns:
            This client, useful for chaining inplace calls.
        """
        self._use_custom_keys = value
        return self

    def set_tags(self, value: List[str]) -> Self:
        """
        Set the default tags.  # noqa: DAR101.

        Args:
            value: The default tags.

        Returns:
            This client, useful for chaining inplace calls.
        """
        self._tags = value
        return self

    def set_drop_params(self, value: bool) -> Self:
        """
        Set the default drop params bool.  # noqa: DAR101.

        Args:
            value: The default drop params bool.

        Returns:
            This client, useful for chaining inplace calls.
        """
        self._drop_params = value
        return self

    def set_region(self, value: str) -> Self:
        """
        Set the default region.  # noqa: DAR101.

        Args:
            value: The default region.

        Returns:
            This client, useful for chaining inplace calls.
        """
        self._region = value
        return self

    def set_log_query_body(self, value: bool) -> Self:
        """
        Set the default log query body bool.  # noqa: DAR101.

        Args:
            value: The default log query body bool.

        Returns:
            This client, useful for chaining inplace calls.
        """
        self._log_query_body = value
        return self

    def set_log_response_body(self, value: bool) -> Self:
        """
        Set the default log response body bool.  # noqa: DAR101.

        Args:
            value: The default log response body bool.

        Returns:
            This client, useful for chaining inplace calls.
        """
        self._log_response_body = value
        return self

    def set_return_full_completion(self, value: bool) -> Self:
        """
        Set the default return full completion bool.  # noqa: DAR101.

        Args:
            value: The default return full completion bool.

        Returns:
            This client, useful for chaining inplace calls.
        """
        self._return_full_completion = value
        return self

    def set_cache(self, value: bool) -> Self:
        """
        Set the default cache bool.  # noqa: DAR101.

        Args:
            value: The default cache bool.

        Returns:
            This client, useful for chaining inplace calls.
        """
        self._cache = value
        return self

    def set_extra_headers(self, value: Headers) -> Self:
        """
        Set the default extra headers.  # noqa: DAR101.

        Args:
            value: The default extra headers.

        Returns:
            This client, useful for chaining inplace calls.
        """
        self._extra_headers = value
        return self

    def set_extra_query(self, value: Query) -> Self:
        """
        Set the default extra query.  # noqa: DAR101.

        Args:
            value: The default extra query.

        Returns:
            This client, useful for chaining inplace calls.
        """
        self._extra_query = value
        return self

    def set_extra_body(self, value: Body) -> Self:
        """
        Set the default extra body.  # noqa: DAR101.

        Args:
            value: The default extra body.

        Returns:
            This client, useful for chaining inplace calls.
        """
        self._extra_body = value
        return self

    def set_default_prompt(self, value: Prompt) -> Self:
        """
        Set the default prompt.  # noqa: DAR101.

        Args:
              The default prompt.

        Returns:
            This client, useful for chaining inplace calls.
        """
        for f in value.model_fields:
            if hasattr(self, f):
                getattr(self, "set_" + f)(getattr(value, f))
        return self

    # Generate #
    # ---------#

    def generate(
            self,
            user_message: Optional[str] = None,
            system_message: Optional[str] = None,
            messages: Optional[
                Union[List[ChatCompletionMessageParam],
                      Dict[str, List[ChatCompletionMessageParam]]]] = None,
            *,
            frequency_penalty: Optional[float] = None,
            logit_bias: Optional[Dict[str, int]] = None,
            logprobs: Optional[bool] = None,
            top_logprobs: Optional[int] = None,
            max_completion_tokens: Optional[int] = None,
            n: Optional[int] = None,
            presence_penalty: Optional[float] = None,
            response_format: Optional[ResponseFormat] = None,
            seed: Optional[int] = None,
            stop: Union[Optional[str], List[str]] = None,
            stream: Optional[bool] = None,
            stream_options: Optional[ChatCompletionStreamOptionsParam] = None,
            temperature: Optional[float] = None,
            top_p: Optional[float] = None,
            tools: Optional[Iterable[ChatCompletionToolParam]] = None,
            tool_choice: Optional[ChatCompletionToolChoiceOptionParam] = None,
            parallel_tool_calls: Optional[bool] = None,
            # platform arguments
            use_custom_keys: Optional[bool] = None,
            tags: Optional[List[str]] = None,
            drop_params: Optional[bool] = None,
            region: Optional[str] = None,
            log_query_body: Optional[bool] = None,
            log_response_body: Optional[bool] = None,
            # python client arguments
            return_full_completion: Optional[bool] = None,
            cache: Optional[bool] = None,
            # passthrough arguments
            extra_headers: Optional[Headers] = None,
            extra_query: Optional[Query] = None,
            **kwargs,
    ):
        """Generate a ChatCompletion response for the specified endpoint,
        from the provided query parameters.

        Args:
            user_message: A string containing the user message.
            If provided, messages must be None.

            system_message: An optional string containing the system message. This
            always appears at the beginning of the list of messages.

            messages: A list of messages comprising the conversation so far, or
            optionally a dictionary of such messages, with clients as the keys in the
            case of multi-llm clients. This will be appended to the system_message if it
            is not None, and any user_message will be appended if it is not None.

            frequency_penalty: Number between -2.0 and 2.0. Positive values penalize new
            tokens based on their existing frequency in the text so far, decreasing the
            model's likelihood to repeat the same line verbatim.

            logit_bias: Modify the likelihood of specified tokens appearing in the
            completion. Accepts a JSON object that maps tokens (specified by their token
            ID in the tokenizer) to an associated bias value from -100 to 100.
            Mathematically, the bias is added to the logits generated by the model prior
            to sampling. The exact effect will vary per model, but values between -1 and
            1 should decrease or increase likelihood of selection; values like -100 or
            100 should result in a ban or exclusive selection of the relevant token.

            logprobs: Whether to return log probabilities of the output tokens or not.
            If true, returns the log probabilities of each output token returned in the
            content of message.

            top_logprobs: An integer between 0 and 20 specifying the number of most
            likely tokens to return at each token position, each with an associated log
            probability. logprobs must be set to true if this parameter is used.

            max_completion_tokens: The maximum number of tokens that can be generated in
            the chat completion. The total length of input tokens and generated tokens
            is limited by the model's context length. Defaults value is 1024. Uses the
            provider's default max_completion_tokens when None is explicitly passed.

            n: How many chat completion choices to generate for each input message. Note
            that you will be charged based on the number of generated tokens across all
            of the choices. Keep n as 1 to minimize costs.

            presence_penalty: Number between -2.0 and 2.0. Positive values penalize new
            tokens based on whether they appear in the text so far, increasing the
            model's likelihood to talk about new topics.

            response_format: An object specifying the format that the model must output.
            Setting to `{ "type": "json_schema", "json_schema": {...} }` enables
            Structured Outputs which ensures the model will match your supplied JSON
            schema. Learn more in the Structured Outputs guide. Setting to
            `{ "type": "json_object" }` enables JSON mode, which ensures the message the
            model generates is valid JSON.

            seed: If specified, a best effort attempt is made to sample
            deterministically, such that repeated requests with the same seed and
            parameters should return the same result. Determinism is not guaranteed, and
            you should refer to the system_fingerprint response parameter to monitor
            changes in the backend.

            stop: Up to 4 sequences where the API will stop generating further tokens.

            stream: If True, generates content as a stream. If False, generates content
            as a single response. Defaults to False.

            stream_options: Options for streaming response. Only set this when you set
            stream: true.

            temperature:  What sampling temperature to use, between 0 and 2.
            Higher values like 0.8 will make the output more random,
            while lower values like 0.2 will make it more focused and deterministic.
            It is generally recommended to alter this or top_p, but not both.
            Default value is 1.0. Defaults to the provider's default temperature when
            None is explicitly passed.

            top_p: An alternative to sampling with temperature, called nucleus sampling,
            where the model considers the results of the tokens with top_p probability
            mass. So 0.1 means only the tokens comprising the top 10% probability mass
            are considered. Generally recommended to alter this or temperature, but not
            both.

            tools: A list of tools the model may call. Currently, only functions are
            supported as a tool. Use this to provide a list of functions the model may
            generate JSON inputs for. A max of 128 functions are supported.

            tool_choice: Controls which (if any) tool is called by the
            model. none means the model will not call any tool and instead generates a
            message. auto means the model can pick between generating a message or
            calling one or more tools. required means the model must call one or more
            tools. Specifying a particular tool via
            `{ "type": "function", "function": {"name": "my_function"} }`
            forces the model to call that tool.
            none is the default when no tools are present. auto is the default if tools
            are present.

            parallel_tool_calls: Whether to enable parallel function calling during tool
            use.

            use_custom_keys:  Whether to use custom API keys or our unified API keys
            with the backend provider. Defaults to False.

            tags: Arbitrary number of tags to classify this API query as needed. Helpful
            for generally grouping queries across tasks and users, for logging purposes.

            drop_params: Whether or not to drop unsupported OpenAI params by the
            provider you’re using.

            region: A string used to represent the region where the endpoint is
            accessed. Only relevant for on-prem deployments with certain providers like
            `vertex-ai`, `aws-bedrock` and `azure-ml`, where the endpoint is being
            accessed through a specified region.

            log_query_body: Whether to log the contents of the query json body.

            log_response_body: Whether to log the contents of the response json body.

            return_full_completion: If False, only return the message content
            chat_completion.choices[0].message.content.strip(" ") from the OpenAI
            return. Otherwise, the full response chat_completion is returned.
            Defaults to False.

            cache: If True, then the arguments will be stored in a local cache file, and
            any future calls with identical arguments will read from the cache instead
            of running the LLM query. This can help to save costs and also debug
            multi-step LLM applications, while keeping early steps fixed.
            This argument only has any effect when stream=False. Defaults to False.

            extra_headers: Additional "passthrough" headers for the request which are
            provider-specific, and are not part of the OpenAI standard. They are handled
            by the provider-specific API.

            extra_query: Additional "passthrough" query parameters for the request which
            are provider-specific, and are not part of the OpenAI standard. They are
            handled by the provider-specific API.

            kwargs: Additional "passthrough" JSON properties for the body of the
            request, which are provider-specific, and are not part of the OpenAI
            standard. They will be handled by the provider-specific API.

        Returns:
            If stream is True, returns a generator yielding chunks of content.
            If stream is False, returns a single string response.

        Raises:
            UnifyError: If an error occurs during content generation.
        """
        return self._generate(
            user_message,
            _default(system_message, self._system_message),
            _default(messages, self._messages),
            frequency_penalty=_default(frequency_penalty, self._frequency_penalty),
            logit_bias=_default(logit_bias, self._logit_bias),
            logprobs=_default(logprobs, self._logprobs),
            top_logprobs=_default(top_logprobs, self._top_logprobs),
            max_completion_tokens=_default(max_completion_tokens,
                                           self._max_completion_tokens),
            n=_default(n, self._n),
            presence_penalty=_default(presence_penalty, self._presence_penalty),
            response_format=_default(response_format, self._response_format),
            seed=_default(seed, self._seed),
            stop=_default(stop, self._stop),
            stream=_default(stream, self._stream),
            stream_options=_default(stream_options, self._stream_options),
            temperature=_default(temperature, self._temperature),
            top_p=_default(top_p, self._top_p),
            tools=_default(tools, self._tools),
            tool_choice=_default(tool_choice, self._tool_choice),
            parallel_tool_calls=_default(parallel_tool_calls,
                                         self._parallel_tool_calls),
            # platform arguments
            use_custom_keys=_default(use_custom_keys, self._use_custom_keys),
            tags=_default(tags, self._tags),
            drop_params=_default(drop_params, self._drop_params),
            region=_default(region, self._region),
            log_query_body=_default(log_query_body, self._log_query_body),
            log_response_body=_default(log_response_body, self._log_response_body),
            # python client arguments
            return_full_completion=True if _default(tools, self._tools) else
            _default(return_full_completion, self._return_full_completion),
            cache=_default(cache, self._cache),
            # passthrough arguments
            extra_headers=_default(extra_headers, self._extra_headers),
            extra_query=_default(extra_query, self._extra_query),
            **{**self._extra_body, **kwargs},
        )

    # Credits #
    # --------#

    def get_credit_balance(self) -> Union[float, None]:
        # noqa: DAR201, DAR401
        """
        Get the remaining credits left on your account.

        Returns:
            The remaining credits on the account if successful, otherwise None.
        Raises:
            BadRequestError: If there was an HTTP error.
            ValueError: If there was an error parsing the JSON response.
        """
        url = f"{BASE_URL}/credits"
        headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {self._api_key}",
        }
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            return response.json()["credits"]
        except requests.RequestException as e:
            raise requests.RequestException(
                "There was an error with the request.") from e
        except (KeyError, ValueError) as e:
            raise ValueError("Error parsing JSON response.") from e

    # Abstract Methods #
    # -----------------#

    @abstractmethod
    def _generate(
            self,
            user_message: str,
            system_message: str,
            messages: Optional[
                Union[List[ChatCompletionMessageParam],
                      Dict[str, List[ChatCompletionMessageParam]]]],
            *,
            frequency_penalty: Optional[float],
            logit_bias: Optional[Dict[str, int]],
            logprobs: Optional[bool],
            top_logprobs: Optional[int],
            max_completion_tokens: Optional[int],
            n: Optional[int],
            presence_penalty: Optional[float],
            response_format: Optional[ResponseFormat],
            seed: Optional[int],
            stop: Union[Optional[str], List[str]],
            stream: Optional[bool],
            stream_options: Optional[ChatCompletionStreamOptionsParam],
            temperature: Optional[float],
            top_p: Optional[float],
            tools: Optional[Iterable[ChatCompletionToolParam]],
            tool_choice: Optional[ChatCompletionToolChoiceOptionParam],
            parallel_tool_calls: Optional[bool],
            # platform arguments
            use_custom_keys: bool,
            tags: Optional[List[str]],
            drop_params: Optional[bool],
            region: Optional[str],
            log_query_body: Optional[bool],
            log_response_body: Optional[bool],
            # python client arguments
            return_full_completion: bool,
            cache: bool,
            # passthrough arguments
            extra_headers: Optional[Headers],
            extra_query: Optional[Query],
            **kwargs,
    ):
        raise NotImplementedError
