# global
import abc
import asyncio
import requests
from typing import Optional, Union, List, Tuple, Dict, Iterable
# noinspection PyProtectedMember
from openai._types import Headers, Query
from openai.types.chat import (
    ChatCompletionToolParam,
    ChatCompletionToolChoiceOptionParam,
    ChatCompletionMessageParam
)
from openai.types.chat.completion_create_params import ResponseFormat

# local
from unify import BASE_URL
# noinspection PyProtectedMember
from unify.utils.helpers import _validate_api_key
from unify.chat.clients import _Client, _UniLLMClient, AsyncUnify


class _MultiLLMClient(_Client, abc.ABC):

    def __init__(
        self,
        endpoints: Optional[Iterable[str]] = None,
        *,
        system_message: Optional[str] = None,
        messages: Optional[
            Union[List[ChatCompletionMessageParam],
                  Dict[str, List[ChatCompletionMessageParam]]]] = None,
        frequency_penalty: Optional[float] = None,
        logit_bias: Optional[Dict[str, int]] = None,
        logprobs: Optional[bool] = None,
        top_logprobs: Optional[int] = None,
        max_completion_tokens: Optional[int] = 1024,
        n: Optional[int] = None,
        presence_penalty: Optional[float] = None,
        response_format: Optional[ResponseFormat] = None,
        seed: Optional[int] = None,
        stop: Union[Optional[str], List[str]] = None,
        temperature: Optional[float] = 1.0,
        top_p: Optional[float] = None,
        tools: Optional[Iterable[ChatCompletionToolParam]] = None,
        tool_choice: Optional[ChatCompletionToolChoiceOptionParam] = None,
        parallel_tool_calls: Optional[bool] = None,
        # platform arguments
        use_custom_keys: bool = False,
        tags: Optional[List[str]] = None,
        api_key: Optional[str] = None,
        # python client arguments
        return_full_completion: bool = False,
        cache: bool = False,
        # passthrough arguments
        extra_headers: Optional[Headers] = None,
        extra_query: Optional[Query] = None,
        **kwargs,
    ) -> None:
        super().__init__(
            system_message=system_message,
            messages=messages,
            frequency_penalty=frequency_penalty,
            logit_bias=logit_bias,
            logprobs=logprobs,
            top_logprobs=top_logprobs,
            max_completion_tokens=max_completion_tokens,
            n=n,
            presence_penalty=presence_penalty,
            response_format=response_format,
            seed=seed,
            stop=stop,
            temperature=temperature,
            top_p=top_p,
            tools=tools,
            tool_choice=tool_choice,
            parallel_tool_calls=parallel_tool_calls,
            # platform arguments
            use_custom_keys=use_custom_keys,
            tags=tags,
            api_key=api_key,
            # python client arguments
            return_full_completion=return_full_completion,
            cache=cache,
            # passthrough arguments
            extra_headers=extra_headers,
            extra_query=extra_query,
            **kwargs
        )
        endpoints = list(endpoints)
        self._api_key = _validate_api_key(api_key)
        self._endpoints = endpoints
        self._client_class = AsyncUnify
        self._clients = self._create_clients(endpoints)

    def _create_clients(
        self, endpoints: List[str]
    ) -> Dict[str, AsyncUnify]:
        return {
            endpoint: self._client_class(
                endpoint,
                system_message=self.system_message,
                messages=self.messages,
                frequency_penalty=self.frequency_penalty,
                logit_bias=self.logit_bias,
                logprobs=self.logprobs,
                top_logprobs=self.top_logprobs,
                max_completion_tokens=self.max_completion_tokens,
                n=self.n,
                presence_penalty=self.presence_penalty,
                response_format=self.response_format,
                seed=self.seed,
                stop=self.stop,
                temperature=self.temperature,
                top_p=self.top_p,
                tools=self.tools,
                tool_choice=self.tool_choice,
                parallel_tool_calls=self.parallel_tool_calls,
                # platform arguments
                use_custom_keys=self.use_custom_keys,
                tags=self.tags,
                api_key=self._api_key,
                # python client arguments
                return_full_completion=self.return_full_completion,
                cache=self.cache,
                # passthrough arguments
                extra_headers=self.extra_headers,
                extra_query=self.extra_query,
                **self.extra_body
            )
            for endpoint in endpoints
        }

    def add_endpoints(
        self, endpoints: Union[List[str], str], ignore_duplicates: bool = True
    ) -> None:
        if isinstance(endpoints, str):
            endpoints = [endpoints]
        # remove duplicates
        if ignore_duplicates:
            endpoints = [
                endpoint for endpoint in endpoints if endpoint not in self._endpoints
            ]
        elif len(self._endpoints + endpoints) != len(set(self._endpoints + endpoints)):
            raise Exception(
                "at least one of the provided endpoints to add {}"
                "was already set present in the endpoints {}."
                "Set ignore_duplicates to True to ignore errors like this".format(
                    endpoints, self._endpoints
                )
            )
        # update endpoints
        self._endpoints = self._endpoints + endpoints
        # create new clients
        self._clients.update(self._create_clients(endpoints))

    def remove_endpoints(
        self, endpoints: Union[List[str], str], ignore_missing: bool = True
    ) -> None:
        if isinstance(endpoints, str):
            endpoints = [endpoints]
        # remove irrelevant
        if ignore_missing:
            endpoints = [
                endpoint for endpoint in endpoints if endpoint in self._endpoints
            ]
        elif len(self._endpoints) != len(set(self._endpoints + endpoints)):
            raise Exception(
                "at least one of the provided endpoints to remove {}"
                "was not present in the current endpoints {}."
                "Set ignore_missing to True to ignore errors like this".format(
                    endpoints, self._endpoints
                )
            )
        # update endpoints and clients
        for endpoint in endpoints:
            self._endpoints.remove(endpoint)
            del self._clients[endpoint]

    def get_credit_balance(self) -> Union[float, None]:
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
            raise Exception("There was an error with the request.") from e
        except (KeyError, ValueError) as e:
            raise ValueError("Error parsing JSON response.") from e

    @property
    def endpoints(self) -> Tuple[str, ...]:
        return tuple(self._endpoints)

    @property
    def clients(self) -> Dict[str, _UniLLMClient]:
        return self._clients

    # Representation #
    # ---------------#

    def __repr__(self):
        return "{}(endpoints={})".format(self.__class__.__name__, self._endpoints)

    def __str__(self):
        return "{}(endpoints={})".format(self.__class__.__name__, self._endpoints)


class MultiLLM(_MultiLLMClient):

    def __init__(
        self,
        endpoints: Optional[Iterable[str]] = None,
        *,
        system_message: Optional[str] = None,
        messages: Optional[
            Union[List[ChatCompletionMessageParam],
                  Dict[str, List[ChatCompletionMessageParam]]]] = None,
        frequency_penalty: Optional[float] = None,
        logit_bias: Optional[Dict[str, int]] = None,
        logprobs: Optional[bool] = None,
        top_logprobs: Optional[int] = None,
        max_completion_tokens: Optional[int] = 1024,
        n: Optional[int] = None,
        presence_penalty: Optional[float] = None,
        response_format: Optional[ResponseFormat] = None,
        seed: Optional[int] = None,
        stop: Union[Optional[str], List[str]] = None,
        temperature: Optional[float] = 1.0,
        top_p: Optional[float] = None,
        tools: Optional[Iterable[ChatCompletionToolParam]] = None,
        tool_choice: Optional[ChatCompletionToolChoiceOptionParam] = None,
        parallel_tool_calls: Optional[bool] = None,
        # platform arguments
        use_custom_keys: bool = False,
        tags: Optional[List[str]] = None,
        api_key: Optional[str] = None,
        # python client arguments
        return_full_completion: bool = False,
        cache: bool = False,
        # passthrough arguments
        extra_headers: Optional[Headers] = None,
        extra_query: Optional[Query] = None,
        **kwargs,
    ) -> None:
        super().__init__(
            endpoints=endpoints,
            system_message=system_message,
            messages=messages,
            frequency_penalty=frequency_penalty,
            logit_bias=logit_bias,
            logprobs=logprobs,
            top_logprobs=top_logprobs,
            max_completion_tokens=max_completion_tokens,
            n=n,
            presence_penalty=presence_penalty,
            response_format=response_format,
            seed=seed,
            stop=stop,
            temperature=temperature,
            top_p=top_p,
            tools=tools,
            tool_choice=tool_choice,
            parallel_tool_calls=parallel_tool_calls,
            # platform arguments
            use_custom_keys=use_custom_keys,
            tags=tags,
            api_key=api_key,
            # python client arguments
            return_full_completion=return_full_completion,
            cache=cache,
            # passthrough arguments
            extra_headers=extra_headers,
            extra_query=extra_query,
            **kwargs
        )

    def _generate(  # noqa: WPS234, WPS211
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
        max_completion_tokens: Optional[int] = 1024,
        n: Optional[int] = None,
        presence_penalty: Optional[float] = None,
        response_format: Optional[ResponseFormat] = None,
        seed: Optional[int] = None,
        stop: Union[Optional[str], List[str]] = None,
        temperature: Optional[float] = 1.0,
        top_p: Optional[float] = None,
        tools: Optional[Iterable[ChatCompletionToolParam]] = None,
        tool_choice: Optional[ChatCompletionToolChoiceOptionParam] = None,
        parallel_tool_calls: Optional[bool] = None,
        # platform arguments
        use_custom_keys: bool = False,
        tags: Optional[List[str]] = None,
        # python client arguments
        return_full_completion: bool = False,
        # passthrough arguments
        extra_headers: Optional[Headers] = None,
        extra_query: Optional[Query] = None,
        **kwargs,
    ) -> Dict[str, str]:
        kw = dict(
            user_message=user_message,
            system_message=system_message,
            messages=messages,
            max_completion_tokens=max_completion_tokens,
            stop=stop,
            temperature=temperature,
            frequency_penalty=frequency_penalty,
            logit_bias=logit_bias,
            logprobs=logprobs,
            top_logprobs=top_logprobs,
            n=n,
            presence_penalty=presence_penalty,
            response_format=response_format,
            seed=seed,
            top_p=top_p,
            tools=tools,
            tool_choice=tool_choice,
            parallel_tool_calls=parallel_tool_calls,
            use_custom_keys=use_custom_keys,
            tags=tags,
            return_full_completion=return_full_completion,
            extra_headers=extra_headers,
            extra_query=extra_query,
            **kwargs,
        )

        # noinspection DuplicatedCode
        async def gen(kw_):
            multi_message = isinstance(messages, dict)
            kw_ = {k: v for k, v in kw_.items() if v is not None}
            responses = dict()
            for endpoint, client in self._clients.items():
                these_kw = kw_.copy()
                if multi_message:
                    these_kw["messages"] = these_kw["messages"][endpoint]
                responses[endpoint] = await client.generate(**these_kw)
            return responses
        return asyncio.run(gen(kw))


class MultiLLMAsync(_MultiLLMClient):

    def __init__(
        self,
        endpoints: Optional[Iterable[str]] = None,
        *,
        system_message: Optional[str] = None,
        messages: Optional[
            Union[List[ChatCompletionMessageParam],
                  Dict[str, List[ChatCompletionMessageParam]]]] = None,
        frequency_penalty: Optional[float] = None,
        logit_bias: Optional[Dict[str, int]] = None,
        logprobs: Optional[bool] = None,
        top_logprobs: Optional[int] = None,
        max_completion_tokens: Optional[int] = 1024,
        n: Optional[int] = None,
        presence_penalty: Optional[float] = None,
        response_format: Optional[ResponseFormat] = None,
        seed: Optional[int] = None,
        stop: Union[Optional[str], List[str]] = None,
        temperature: Optional[float] = 1.0,
        top_p: Optional[float] = None,
        tools: Optional[Iterable[ChatCompletionToolParam]] = None,
        tool_choice: Optional[ChatCompletionToolChoiceOptionParam] = None,
        parallel_tool_calls: Optional[bool] = None,
        # platform arguments
        use_custom_keys: bool = False,
        tags: Optional[List[str]] = None,
        api_key: Optional[str] = None,
        # python client arguments
        return_full_completion: bool = False,
        cache: bool = False,
        # passthrough arguments
        extra_headers: Optional[Headers] = None,
        extra_query: Optional[Query] = None,
        **kwargs,
    ) -> None:
        super().__init__(
            endpoints=endpoints,
            system_message=system_message,
            messages=messages,
            frequency_penalty=frequency_penalty,
            logit_bias=logit_bias,
            logprobs=logprobs,
            top_logprobs=top_logprobs,
            max_completion_tokens=max_completion_tokens,
            n=n,
            presence_penalty=presence_penalty,
            response_format=response_format,
            seed=seed,
            stop=stop,
            temperature=temperature,
            top_p=top_p,
            tools=tools,
            tool_choice=tool_choice,
            parallel_tool_calls=parallel_tool_calls,
            # platform arguments
            use_custom_keys=use_custom_keys,
            tags=tags,
            api_key=api_key,
            # python client arguments
            return_full_completion=return_full_completion,
            cache=cache,
            # passthrough arguments
            extra_headers=extra_headers,
            extra_query=extra_query,
            **kwargs
        )

    async def _generate(  # noqa: WPS234, WPS211
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
        max_completion_tokens: Optional[int] = 1024,
        n: Optional[int] = None,
        presence_penalty: Optional[float] = None,
        response_format: Optional[ResponseFormat] = None,
        seed: Optional[int] = None,
        stop: Union[Optional[str], List[str]] = None,
        temperature: Optional[float] = 1.0,
        top_p: Optional[float] = None,
        tools: Optional[Iterable[ChatCompletionToolParam]] = None,
        tool_choice: Optional[ChatCompletionToolChoiceOptionParam] = None,
        parallel_tool_calls: Optional[bool] = None,
        # platform arguments
        use_custom_keys: bool = False,
        tags: Optional[List[str]] = None,
        # python client arguments
        return_full_completion: bool = False,
        # passthrough arguments
        extra_headers: Optional[Headers] = None,
        extra_query: Optional[Query] = None,
        **kwargs,
    ) -> Dict[str, str]:
        kw = dict(
            user_message=user_message,
            system_message=system_message,
            messages=messages,
            max_completion_tokens=max_completion_tokens,
            stop=stop,
            temperature=temperature,
            frequency_penalty=frequency_penalty,
            logit_bias=logit_bias,
            logprobs=logprobs,
            top_logprobs=top_logprobs,
            n=n,
            presence_penalty=presence_penalty,
            response_format=response_format,
            seed=seed,
            top_p=top_p,
            tools=tools,
            tool_choice=tool_choice,
            parallel_tool_calls=parallel_tool_calls,
            use_custom_keys=use_custom_keys,
            tags=tags,
            return_full_completion=return_full_completion,
            extra_headers=extra_headers,
            extra_query=extra_query,
            **kwargs,
        )
        multi_message = isinstance(messages, dict)
        kw = {k: v for k, v in kw.items() if v is not None}
        responses = dict()
        for endpoint, client in self._clients.items():
            these_kw = kw.copy()
            if multi_message:
                these_kw["messages"] = these_kw["messages"][endpoint]
            responses[endpoint] = await client.generate(**these_kw)
        return responses
