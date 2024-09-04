# global
import requests
from abc import ABC, abstractmethod
from typing import Optional, Union, List, Tuple, Dict, Iterable, Generator
from openai._types import Headers, Query
from openai.types.chat import (
    ChatCompletionToolParam,
    ChatCompletionToolChoiceOptionParam,
    ChatCompletionMessageParam,
)
from openai.types.chat.completion_create_params import ResponseFormat

# local
from unify import BASE_URL
from .clients import Unify, AsyncUnify
from unify.utils.helpers import _validate_api_key
from unify.exceptions import UnifyError
from unify.exceptions import BadRequestError


class MultiLLMClient(ABC):
    def __init__(
        self,
        endpoints: Optional[Iterable[str]] = None,
        asynchronous: bool = False,
        api_key: Optional[str] = None,
    ) -> None:
        endpoints = list(endpoints)
        self._api_key = _validate_api_key(api_key)
        self._endpoints = endpoints
        self._client_class = AsyncUnify if asynchronous else Unify
        self._clients = self._create_clients(endpoints)

    def _create_clients(
        self, endpoints: List[str]
    ) -> Dict[str, Union[Unify, AsyncUnify]]:
        return {
            endpoint: self._client_class(endpoint, api_key=self._api_key)
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
            raise UnifyError(
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
            raise UnifyError(
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
            raise BadRequestError("There was an error with the request.") from e
        except (KeyError, ValueError) as e:
            raise ValueError("Error parsing JSON response.") from e

    @property
    def endpoints(self) -> Tuple[str, ...]:
        return tuple(self._endpoints)

    @property
    def clients(self) -> Dict[str, Union[Unify, AsyncUnify]]:
        return self._clients

    @abstractmethod
    def generate(  # noqa: WPS234, WPS211
        self,
        user_prompt: Optional[str] = None,
        system_prompt: Optional[str] = None,
        messages: Optional[Iterable[ChatCompletionMessageParam]] = None,
        *,
        frequency_penalty: Optional[float] = None,
        logit_bias: Optional[Dict[str, int]] = None,
        logprobs: Optional[bool] = None,
        top_logprobs: Optional[int] = None,
        max_tokens: Optional[int] = 1024,
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
        message_content_only: bool = True,
        # passthrough arguments
        extra_headers: Optional[Headers] = None,
        extra_query: Optional[Query] = None,
        **kwargs,
    ) -> Union[Generator[str, None, None], str]:  # noqa: DAR101, DAR201, DAR401
        """Generate content using the Unify API.

        Args:
            user_prompt: A string containing the user prompt.
            If provided, messages must be None.

            system_prompt: An optional string containing the system prompt.

            messages: A list of messages comprising the conversation so far. If
            provided, user_prompt must be None.

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

            max_tokens: The maximum number of tokens that can be generated in the chat
            completion. The total length of input tokens and generated tokens is limited
            by the model's context length. Defaults to the provider's default max_tokens
            when the value is None.

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
            Defaults to the provider's default max_tokens when the value is None.

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
            `{"type": "function", "function": {"name": "my_function"}}` forces the model
            to call that tool.
            none is the default when no tools are present. auto is the default if tools
            are present.

            parallel_tool_calls: Whether to enable parallel function calling during tool
            use.

            use_custom_keys:  Whether to use custom API keys or our unified API keys
            with the backend provider.

            tags: Arbitrary number of tags to classify this API query as needed. Helpful
            for generally grouping queries across tasks and users, for logging purposes.

            message_content_only: If True, only return the message content
            chat_completion.choices[0].message.content.strip(" ") from the OpenAI
            return. Otherwise, the full response chat_completion is returned.
            Defaults to True.

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
            A dictionary of responses from each of the LLM clients.

        Raises:
            UnifyError: If an error occurs during content generation.
        """
        raise NotImplementedError


class MultiLLM(MultiLLMClient):
    def __init__(
        self,
        endpoints: Optional[Iterable[str]] = None,
        api_key: Optional[str] = None,
    ) -> None:
        super().__init__(endpoints=endpoints, asynchronous=False, api_key=api_key)

    def generate(  # noqa: WPS234, WPS211
        self,
        user_prompt: Optional[str] = None,
        system_prompt: Optional[str] = None,
        messages: Optional[Iterable[ChatCompletionMessageParam]] = None,
        *,
        frequency_penalty: Optional[float] = None,
        logit_bias: Optional[Dict[str, int]] = None,
        logprobs: Optional[bool] = None,
        top_logprobs: Optional[int] = None,
        max_tokens: Optional[int] = 1024,
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
        message_content_only: bool = True,
        # passthrough arguments
        extra_headers: Optional[Headers] = None,
        extra_query: Optional[Query] = None,
        **kwargs,
    ) -> Dict[str, str]:
        kw = dict(
            user_prompt=user_prompt,
            system_prompt=system_prompt,
            messages=messages,
            max_tokens=max_tokens,
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
            message_content_only=message_content_only,
            extra_headers=extra_headers,
            extra_query=extra_query,
            **kwargs,
        )
        kw = {k: v for k, v in kw.items() if v is not None}
        responses = dict()
        for endpoint, client in self._clients.items():
            responses[endpoint] = client.generate(**kw)
        return responses


class MultiLLMAsync(MultiLLMClient):
    def __init__(
        self,
        endpoints: Optional[Iterable[str]] = None,
        api_key: Optional[str] = None,
    ) -> None:
        super().__init__(endpoints=endpoints, asynchronous=True, api_key=api_key)

    async def generate(  # noqa: WPS234, WPS211
        self,
        user_prompt: Optional[str] = None,
        system_prompt: Optional[str] = None,
        messages: Optional[Iterable[ChatCompletionMessageParam]] = None,
        *,
        frequency_penalty: Optional[float] = None,
        logit_bias: Optional[Dict[str, int]] = None,
        logprobs: Optional[bool] = None,
        top_logprobs: Optional[int] = None,
        max_tokens: Optional[int] = 1024,
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
        message_content_only: bool = True,
        # passthrough arguments
        extra_headers: Optional[Headers] = None,
        extra_query: Optional[Query] = None,
        **kwargs,
    ) -> Dict[str, str]:
        kw = dict(
            user_prompt=user_prompt,
            system_prompt=system_prompt,
            messages=messages,
            max_tokens=max_tokens,
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
            message_content_only=message_content_only,
            extra_headers=extra_headers,
            extra_query=extra_query,
            **kwargs,
        )
        kw = {k: v for k, v in kw.items() if v is not None}
        responses = dict()
        for endpoint, client in self._clients.items():
            responses[endpoint] = await client.generate(**kw)
        return responses
