# global
import openai
import requests
from abc import ABC, abstractmethod
from typing import AsyncGenerator, Dict, Generator, List, Optional, Union

# local
import unify.utils
from unify.utils import _validate_api_key
from unify.exceptions import BadRequestError, UnifyError, status_error_map


class Client(ABC):
    """Base Abstract class for interacting with the Unify chat completions endpoint."""

    @abstractmethod
    def _get_client(self):
        raise NotImplemented

    @abstractmethod
    def generate(self):
        raise NotImplemented

    def __init__(
        self,
        endpoint: Optional[str] = None,
        model: Optional[str] = None,
        provider: Optional[str] = None,
        api_key: Optional[str] = None,
    ) -> None:  # noqa: DAR101, DAR401
        """Initialize the Unify client.

        Args:
            endpoint (str, optional): Endpoint name in OpenAI API format:
                <model_name>@<provider_name>
                Defaults to None.

            model (str, optional): Name of the model.

            provider (str, optional): Name of the provider.

            api_key (str, optional): API key for accessing the Unify API.
                If None, it attempts to retrieve the API key from the
                environment variable UNIFY_KEY.
                Defaults to None.

        Raises:
            UnifyError: If the API key is missing.
        """
        self._api_key = _validate_api_key(api_key)
        if endpoint and (model or provider):
            raise UnifyError(
                "if the model or provider are passed, then the endpoint must not be passed."
            )
        self._endpoint, self._model, self._provider = None, None, None
        if endpoint:
            self.set_endpoint(endpoint)
        if provider:
            self.set_provider(provider)
        if model:
            self.set_model(model)
        self._client = self._get_client()

    @property
    def model(self) -> str:
        """
        Get the model name.  # noqa: DAR201.

        Returns:
            str: The model name.
        """
        return self._model

    def set_model(self, value: str) -> None:
        """
        Set the model name.  # noqa: DAR101.

        Args:
            value (str): The model name.
        """
        valid_models = unify.utils.list_models(self._provider)
        if value not in valid_models:
            if self._provider:
                raise UnifyError(
                    "Current provider {} does not support the specified model {},"
                    "please select one of: {}".format(
                        self._provider, value, valid_models
                    )
                )
            raise UnifyError(
                "The specified model {} is not one of the models supported by Unify: {}".format(
                    value, valid_models
                )
            )
        self._model = value
        if self._provider:
            self._endpoint = "@".join([value, self._provider])

    @property
    def provider(self) -> Optional[str]:
        """
        Get the provider name.  # noqa: DAR201.

        Returns:
            str: The provider name.
        """
        return self._provider

    def set_provider(self, value: str) -> None:
        """
        Set the provider name.  # noqa: DAR101.

        Args:
            value (str): The provider name.
        """
        valid_providers = unify.utils.list_providers(self._model)
        if value not in valid_providers:
            if self._model:
                raise UnifyError(
                    "Current model {} does not support the specified provider {},"
                    "please select one of: {}".format(
                        self._model, value, valid_providers
                    )
                )
            raise UnifyError(
                "The specified provider {} is not one of the providers supported by Unify: {}".format(
                    value, valid_providers
                )
            )
        self._provider = value
        if self._model:
            self._endpoint = "@".join([self._model, value])

    @property
    def endpoint(self) -> str:
        """
        Get the endpoint name.  # noqa: DAR201.

        Returns:
            str: The endpoint name.
        """
        return self._endpoint

    def set_endpoint(self, value: str) -> None:
        """
        Set the endpoint name.  # noqa: DAR101.

        Args:
            value (str): The endpoint name.
        """
        valid_endpoints = unify.utils.list_endpoints()
        if value not in valid_endpoints:
            raise UnifyError(
                "The specified endpoint {} is not one of the endpoints supported by Unify: {}".format(
                    value, valid_endpoints
                )
            )
        self._endpoint = value
        self._model, self._provider = value.split("@")  # noqa: WPS414

    def get_credit_balance(self) -> float:
        # noqa: DAR201, DAR401
        """
        Get the remaining credits left on your account.

        Returns:
            int or None: The remaining credits on the account
            if successful, otherwise None.
        Raises:
            BadRequestError: If there was an HTTP error.
            ValueError: If there was an error parsing the JSON response.
        """
        url = "https://api.unify.ai/v0/get_credits"
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


class Unify(Client):
    """Class for interacting with the Unify chat completions endpoint in a synchronous manner."""

    def _get_client(self):
        try:
            return openai.OpenAI(
                base_url="https://api.unify.ai/v0/",
                api_key=self._api_key,
            )
        except openai.OpenAIError as e:
            raise UnifyError(f"Failed to initialize Unify client: {str(e)}")

    def _generate_stream(
        self,
        messages: List[Dict[str, str]],
        endpoint: str,
        max_tokens: Optional[int] = 1024,
        temperature: Optional[float] = 1.0,
        stop: Optional[List[str]] = None,
        message_content_only: bool = True,
        **kwargs,
    ) -> Generator[str, None, None]:
        try:
            chat_completion = self._client.chat.completions.create(
                model=endpoint,
                messages=messages,  # type: ignore[arg-type]
                max_tokens=max_tokens,
                temperature=temperature,
                stop=stop,
                stream=True,
                extra_body={"signature": "package"},
                **kwargs,
            )
            for chunk in chat_completion:
                if message_content_only:
                    content = chunk.choices[0].delta.content  # type: ignore[union-attr]
                else:
                    content = chunk
                self.set_provider(chunk.model.split("@")[-1])  # type: ignore[union-attr]
                if content is not None:
                    yield content
        except openai.APIStatusError as e:
            raise status_error_map[e.status_code](e.message) from None

    def _generate_non_stream(
        self,
        messages: List[Dict[str, str]],
        endpoint: str,
        max_tokens: Optional[int] = 1024,
        temperature: Optional[float] = 1.0,
        stop: Optional[List[str]] = None,
        message_content_only: bool = True,
        **kwargs,
    ) -> str:
        try:
            chat_completion = self._client.chat.completions.create(
                model=endpoint,
                messages=messages,  # type: ignore[arg-type]
                max_tokens=max_tokens,
                temperature=temperature,
                stop=stop,
                stream=False,
                extra_body={"signature": "package"},
                **kwargs,
            )
            if "router" not in endpoint:
                self.set_provider(
                    chat_completion.model.split(  # type: ignore[union-attr]
                        "@",
                    )[-1]
                )
            if message_content_only:
                content = chat_completion.choices[0].message.content
                if content:
                    return content.strip(" ")
                return ""
            return chat_completion
        except openai.APIStatusError as e:
            raise status_error_map[e.status_code](e.message) from None

    def generate(  # noqa: WPS234, WPS211
        self,
        user_prompt: Optional[str] = None,
        system_prompt: Optional[str] = None,
        messages: Optional[List[Dict[str, str]]] = None,
        max_tokens: Optional[int] = 1024,
        temperature: Optional[float] = 1.0,
        stop: Optional[List[str]] = None,
        stream: bool = False,
        message_content_only: bool = True,
        **kwargs,
    ) -> Union[Generator[str, None, None], str]:  # noqa: DAR101, DAR201, DAR401
        """Generate content using the Unify API.

        Args:
            user_prompt (Optional[str]): A string containing the user prompt.
            If provided, messages must be None.

            system_prompt (Optional[str]): An optional string containing the
            system prompt.

            messages (List[Dict[str, str]]): A list of dictionaries containing the
            conversation history. If provided, user_prompt must be None.

            max_tokens (Optional[int]): The max number of output tokens.
            Defaults to the provider's default max_tokens when the value is None.

            temperature (Optional[float]):  What sampling temperature to use, between 0 and 2.
            Higher values like 0.8 will make the output more random,
            while lower values like 0.2 will make it more focused and deterministic.
            Defaults to the provider's default max_tokens when the value is None.

            stop (Optional[List[str]]): Up to 4 sequences where the API will stop generating further tokens.

            stream (bool): If True, generates content as a stream.
            If False, generates content as a single response.
            Defaults to False.

            message_content_only (bool): If True, only return the message content
            chat_completion.choices[0].message.content.strip(" ") from the OpenAI return.
            Otherwise, the full response chat_completion is returned.
            Defaults to True.

            kwargs: Additional keyword arguments to be passed to the chat.completions.create() method
            of the openai.OpenAI() class, from the OpenAI Python client, which runs under the hood.

        Returns:
            Union[Generator[str, None, None], str]: If stream is True,
             returns a generator yielding chunks of content.
             If stream is False, returns a single string response.

        Raises:
            UnifyError: If an error occurs during content generation.
        """
        contents = []
        if system_prompt:
            contents.append({"role": "system", "content": system_prompt})
        if user_prompt:
            contents.append({"role": "user", "content": user_prompt})
        elif messages:
            contents.extend(messages)
        else:
            raise UnifyError("You must provider either the user_prompt or messages!")

        if stream:
            return self._generate_stream(
                contents,
                self._endpoint,
                max_tokens=max_tokens,
                temperature=temperature,
                stop=stop,
                message_content_only=message_content_only,
                **kwargs,
            )
        return self._generate_non_stream(
            contents,
            self._endpoint,
            max_tokens=max_tokens,
            temperature=temperature,
            stop=stop,
            message_content_only=message_content_only,
            **kwargs,
        )


class AsyncUnify(Client):
    """Class for interacting with the Unify chat completions endpoint in a synchronous manner."""

    def _get_client(self):
        try:
            return openai.AsyncOpenAI(
                base_url="https://api.unify.ai/v0/",
                api_key=self._api_key,
            )
        except openai.APIStatusError as e:
            raise UnifyError(f"Failed to initialize Unify client: {str(e)}")

    async def generate(  # noqa: WPS234, WPS211
        self,
        user_prompt: Optional[str] = None,
        system_prompt: Optional[str] = None,
        messages: Optional[List[Dict[str, str]]] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = 1.0,
        stop: Optional[List[str]] = None,
        stream: bool = False,
        message_content_only: bool = True,
        **kwargs,
    ) -> Union[AsyncGenerator[str, None], str]:  # noqa: DAR101, DAR201, DAR401
        """Generate content asynchronously using the Unify API.

        Args:
            user_prompt (Optional[str]): A string containing the user prompt.
            If provided, messages must be None.

            system_prompt (Optional[str]): An optional string containing the
            system prompt.

            messages (List[Dict[str, str]]): A list of dictionaries containing the
            conversation history. If provided, user_prompt must be None.

            max_tokens (Optional[int]): The max number of output tokens, defaults
            to the provider's default max_tokens when the value is None.

            temperature (Optional[float]):  What sampling temperature to use, between 0 and 2.
            Higher values like 0.8 will make the output more random,
            while lower values like 0.2 will make it more focused and deterministic.
            Defaults to the provider's default max_tokens when the value is None.

            stop (Optional[List[str]]): Up to 4 sequences where the API will stop generating further tokens.

            stream (bool): If True, generates content as a stream.
            If False, generates content as a single response.
            Defaults to False.

            message_content_only (bool): If True, only return the message content
            chat_completion.choices[0].message.content.strip(" ") from the OpenAI return.
            Otherwise, the full response chat_completion is returned.
            Defaults to True.

            kwargs: Additional keyword arguments to be passed to the chat.completions.create() method
            of the openai.OpenAI() class, from the OpenAI Python client, which runs under the hood.

        Returns:
            Union[AsyncGenerator[str, None], List[str]]: If stream is True,
            returns an asynchronous generator yielding chunks of content.
            If stream is False, returns a list of string responses.

        Raises:
            UnifyError: If an error occurs during content generation.
        """
        contents = []
        if system_prompt:
            contents.append({"role": "system", "content": system_prompt})

        if user_prompt:
            contents.append({"role": "user", "content": user_prompt})
        elif messages:
            contents.extend(messages)
        else:
            raise UnifyError("You must provide either the user_prompt or messages!")

        if stream:
            return self._generate_stream(
                contents,
                self._endpoint,
                max_tokens=max_tokens,
                stop=stop,
                temperature=temperature,
                message_content_only=message_content_only,
                **kwargs,
            )
        return await self._generate_non_stream(
            contents,
            self._endpoint,
            max_tokens=max_tokens,
            stop=stop,
            temperature=temperature,
            message_content_only=message_content_only,
            **kwargs,
        )

    async def _generate_stream(
        self,
        messages: List[Dict[str, str]],
        endpoint: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = 1.0,
        stop: Optional[List[str]] = None,
        message_content_only: bool = True,
        **kwargs,
    ) -> AsyncGenerator[str, None]:
        try:
            async_stream = await self._client.chat.completions.create(
                model=endpoint,
                messages=messages,  # type: ignore[arg-type]
                max_tokens=max_tokens,
                temperature=temperature,
                stop=stop,
                stream=True,
                extra_body={"signature": "package"},
                **kwargs,
            )
            async for chunk in async_stream:  # type: ignore[union-attr]
                self.set_provider(chunk.model.split("@")[-1])
                if message_content_only:
                    yield chunk.choices[0].delta.content or ""
                yield chunk
        except openai.APIStatusError as e:
            raise status_error_map[e.status_code](e.message) from None

    async def _generate_non_stream(
        self,
        messages: List[Dict[str, str]],
        endpoint: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = 1.0,
        stop: Optional[List[str]] = None,
        message_content_only: bool = True,
        **kwargs,
    ) -> str:
        try:
            async_response = await self._client.chat.completions.create(
                model=endpoint,
                messages=messages,  # type: ignore[arg-type]
                max_tokens=max_tokens,
                temperature=temperature,
                stop=stop,
                stream=False,
                extra_body={"signature": "package"},
                **kwargs,
            )
            self.set_provider(async_response.model.split("@")[-1])  # type: ignore
            if message_content_only:
                content = async_response.choices[0].message.content
                if content:
                    return content.strip(" ")
                return ""
            return async_response
        except openai.APIStatusError as e:
            raise status_error_map[e.status_code](e.message) from None
