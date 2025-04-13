# global
import copy
from abc import ABC, abstractmethod
from typing import Dict, Iterable, List, Mapping, Optional, Type, Union

import requests

# noinspection PyProtectedMember
from openai._types import Body, Headers, Query
from openai.types.chat import (
    ChatCompletionMessageParam,
    ChatCompletionStreamOptionsParam,
    ChatCompletionToolChoiceOptionParam,
    ChatCompletionToolParam,
)
from pydantic import BaseModel, create_model
from typing_extensions import Self

# local
from unify import BASE_URL
from unify.utils import _requests

# noinspection PyProtectedMember
from unify.utils.helpers import _validate_api_key


class _Client(ABC):
    """Base Abstract class for interacting with the Unify chat completions endpoint."""

    def __init__(
        self,
        *,
        system_message: Optional[str],
        messages: Optional[
            Union[
                List[ChatCompletionMessageParam],
                Dict[str, List[ChatCompletionMessageParam]],
            ]
        ],
        frequency_penalty: Optional[float],
        logit_bias: Optional[Dict[str, int]],
        logprobs: Optional[bool],
        top_logprobs: Optional[int],
        max_completion_tokens: Optional[int],
        n: Optional[int],
        presence_penalty: Optional[float],
        response_format: Optional[Union[Type[BaseModel], Dict[str, str]]],
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
        stateful: bool,
        return_full_completion: bool,
        traced: bool,
        cache: Union[bool, str],
        # passthrough arguments
        extra_headers: Optional[Headers],
        extra_query: Optional[Query],
        **kwargs,
    ) -> None:  # noqa: DAR101, DAR401

        # initial values
        self._api_key = _validate_api_key(api_key)
        self._system_message = None
        self._messages = None
        self._frequency_penalty = None
        self._logit_bias = None
        self._logprobs = None
        self._top_logprobs = None
        self._max_completion_tokens = None
        self._n = None
        self._presence_penalty = None
        self._response_format = None
        self._seed = None
        self._stop = None
        self._stream = None
        self._stream_options = None
        self._temperature = None
        self._top_p = None
        self._tools = None
        self._tool_choice = None
        self._parallel_tool_calls = None
        self._use_custom_keys = None
        self._tags = None
        self._drop_params = None
        self._region = None
        self._log_query_body = None
        self._log_response_body = None
        self._stateful = None
        self._return_full_completion = None
        self._traced = None
        self._cache = None
        self._extra_headers = None
        self._extra_query = None
        self._extra_body = None

        # set based on arguments
        self.set_system_message(system_message)
        self.set_messages(messages)
        self.set_frequency_penalty(frequency_penalty)
        self.set_logit_bias(logit_bias)
        self.set_logprobs(logprobs)
        self.set_top_logprobs(top_logprobs)
        self.set_max_completion_tokens(max_completion_tokens)
        self.set_n(n)
        self.set_presence_penalty(presence_penalty)
        self.set_response_format(response_format)
        self.set_seed(seed)
        self.set_stop(stop)
        self.set_stream(stream)
        self.set_stream_options(stream_options)
        self.set_temperature(temperature)
        self.set_top_p(top_p)
        self.set_tools(tools)
        self.set_tool_choice(tool_choice)
        self.set_parallel_tool_calls(parallel_tool_calls)
        # platform arguments
        self.set_use_custom_keys(use_custom_keys)
        self.set_tags(tags)
        self.set_drop_params(drop_params)
        self.set_region(region)
        self.set_log_query_body(log_query_body)
        self.set_log_response_body(log_response_body)
        # python client arguments
        self.set_stateful(stateful)
        self.set_return_full_completion(return_full_completion)
        self.set_traced(traced)
        self.set_cache(cache)
        # passthrough arguments
        self.set_extra_headers(extra_headers)
        self.set_extra_query(extra_query)
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
    def messages(
        self,
    ) -> Optional[
        Union[
            List[ChatCompletionMessageParam],
            Dict[str, List[ChatCompletionMessageParam]],
        ]
    ]:
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
    def response_format(self) -> Optional[Union[Type[BaseModel], Dict[str, str]]]:
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
    def stateful(self) -> bool:
        """
        Get the default stateful bool, if set.

        Returns:
            The default stateful bool.
        """
        return self._stateful

    @property
    def return_full_completion(self) -> bool:
        """
        Get the default return full completion bool.

        Returns:
            The default return full completion bool.
        """
        return self._return_full_completion

    @property
    def traced(self) -> bool:
        """
        Get the default traced bool.

        Returns:
            The default traced bool.
        """
        return self._traced

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
        if self._messages is None or self._messages == []:
            self._messages = [
                {
                    "role": "system",
                    "content": value,
                },
            ]
        elif self._messages[0]["role"] != "system":
            self._messages = [
                {
                    "role": "system",
                    "content": value,
                },
            ] + self._messages
        else:
            self._messages[0] = {
                "role": "system",
                "content": value,
            }
        return self

    def set_messages(
        self,
        value: Union[
            List[ChatCompletionMessageParam],
            Dict[str, List[ChatCompletionMessageParam]],
        ],
    ) -> Self:
        """
        Set the default messages.  # noqa: DAR101.

        Args:
            value: The default messages.

        Returns:
            This client, useful for chaining inplace calls.
        """
        self._messages = value
        if isinstance(value, list) and value and value[0]["role"] == "system":
            self.set_system_message(value[0]["content"])
        return self

    def append_messages(
        self,
        value: Union[
            List[ChatCompletionMessageParam],
            Dict[str, List[ChatCompletionMessageParam]],
        ],
    ) -> Self:
        """
        Append to the default messages.  # noqa: DAR101.

        Args:
            value: The messages to append to the default.

        Returns:
            This client, useful for chaining inplace calls.
        """
        if self._messages is None:
            self._messages = []
        self._messages += value
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

    def set_response_format(
        self,
        value: Optional[Union[Type[BaseModel], Dict[str, str]]],
    ) -> Self:
        """
        Set the default response format.  # noqa: DAR101.

        Args:
            value: The default response format.

        Returns:
            This client, useful for chaining inplace calls.
        """
        self._response_format = value
        return self

    def set_seed(self, value: Optional[int]) -> Self:
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

    def set_stateful(self, value: bool) -> Self:
        """
        Set the default stateful bool.  # noqa: DAR101.

        Args:
            value: The default stateful bool.

        Returns:
            This client, useful for chaining inplace calls.
        """
        self._stateful = value
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

    # noinspection PyAttributeOutsideInit
    def set_traced(self, value: bool) -> Self:
        """
        Set the default traced bool.  # noqa: DAR101.

        Args:
            value: The default traced bool.

        Returns:
            This client, useful for chaining inplace calls.
        """
        self._traced = value
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
            response = _requests.get(url, headers=headers, timeout=10)
            if response.status_code != 200:
                raise Exception(response.json())
            return response.json()["credits"]
        except requests.RequestException as e:
            raise requests.RequestException(
                "There was an error with the request.",
            ) from e
        except (KeyError, ValueError) as e:
            raise ValueError("Error parsing JSON response.") from e

    # Methods #
    # --------#

    def copy(self):
        # noinspection PyUnresolvedReferences,PyArgumentList
        return type(self)(
            **copy.deepcopy(
                {
                    **self._constructor_args,
                    **dict(
                        system_message=self._system_message,
                        messages=self._messages,
                        frequency_penalty=self._frequency_penalty,
                        logit_bias=self._logit_bias,
                        logprobs=self._logprobs,
                        top_logprobs=self._top_logprobs,
                        max_completion_tokens=self._max_completion_tokens,
                        n=self._n,
                        presence_penalty=self._presence_penalty,
                        response_format=self._response_format,
                        seed=self._seed,
                        stop=self._stop,
                        stream=self._stream,
                        stream_options=self._stream_options,
                        temperature=self._temperature,
                        top_p=self._top_p,
                        tools=self._tools,
                        tool_choice=self._tool_choice,
                        parallel_tool_calls=self._parallel_tool_calls,
                        # platform arguments
                        use_custom_keys=self._use_custom_keys,
                        tags=self._tags,
                        drop_params=self._drop_params,
                        region=self._region,
                        log_query_body=self._log_query_body,
                        log_response_body=self._log_response_body,
                        api_key=self._api_key,
                        # python client arguments
                        stateful=self._stateful,
                        return_full_completion=self._return_full_completion,
                        traced=self._traced,
                        cache=self._cache,
                        # passthrough arguments
                        extra_headers=self._extra_headers,
                        extra_query=self._extra_query,
                        **self._extra_body,
                    ),
                },
            ),
        )

    def json(self):
        model = create_model(type(self).__name__, __config__={"extra": "allow"})
        instance = model(
            **{
                "type": type(self).__name__,
                **self._constructor_args,
                **dict(
                    system_message=self._system_message,
                    messages=self._messages,
                    frequency_penalty=self._frequency_penalty,
                    logit_bias=self._logit_bias,
                    logprobs=self._logprobs,
                    top_logprobs=self._top_logprobs,
                    max_completion_tokens=self._max_completion_tokens,
                    n=self._n,
                    presence_penalty=self._presence_penalty,
                    response_format=self._response_format,
                    seed=self._seed,
                    stop=self._stop,
                    stream=self._stream,
                    stream_options=self._stream_options,
                    temperature=self._temperature,
                    top_p=self._top_p,
                    tools=self._tools,
                    tool_choice=self._tool_choice,
                    parallel_tool_calls=self._parallel_tool_calls,
                    # platform arguments
                    use_custom_keys=self._use_custom_keys,
                    tags=self._tags,
                    drop_params=self._drop_params,
                    region=self._region,
                    log_query_body=self._log_query_body,
                    log_response_body=self._log_response_body,
                    api_key=self._api_key,
                    # python client arguments
                    stateful=self._stateful,
                    return_full_completion=self._return_full_completion,
                    traced=self._traced,
                    cache=self._cache,
                    # passthrough arguments
                    extra_headers=self._extra_headers,
                    extra_query=self._extra_query,
                    extra_body=self._extra_body,
                ),
            },
        )
        return instance.model_dump()

    # Abstract Methods #
    # -----------------#

    @abstractmethod
    def _generate(
        self,
        messages: Optional[
            Union[
                List[ChatCompletionMessageParam],
                Dict[str, List[ChatCompletionMessageParam]],
            ]
        ],
        *,
        frequency_penalty: Optional[float],
        logit_bias: Optional[Dict[str, int]],
        logprobs: Optional[bool],
        top_logprobs: Optional[int],
        max_completion_tokens: Optional[int],
        n: Optional[int],
        presence_penalty: Optional[float],
        response_format: Optional[Union[Type[BaseModel], Dict[str, str]]],
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
        cache: Union[bool, str],
        # passthrough arguments
        extra_headers: Optional[Headers],
        extra_query: Optional[Query],
        **kwargs,
    ):
        raise NotImplementedError
