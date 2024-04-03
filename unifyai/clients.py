import os
from typing import AsyncGenerator, Dict, Generator, List, Optional, Union

import openai
import requests
from unifyai.exceptions import BadRequestError, UnifyError, status_error_map


def _validate_api_key(api_key: Optional[str]) -> str:
    if api_key is None:
        api_key = os.environ.get("UNIFY_KEY")
    if api_key is None:
        raise KeyError(
            "UNIFY_KEY is missing. Please make sure it is set correctly!",
        )
    return api_key


class Unify:
    """Class for interacting with the Unify API."""

    def __init__(
        self,
        api_key: Optional[str] = None,
    ) -> None:  # noqa: DAR101, DAR401
        """Initialize the Unify client.

        Args:
            api_key (str, optional): API key for accessing the Unify API.
                If None, it attempts to retrieve the API key from the
                environment variable UNIFY_KEY.
                Defaults to None.

        Raises:
            UnifyError: If the API key is missing.
        """
        self.api_key = _validate_api_key(api_key)
        try:
            self.client = openai.OpenAI(
                base_url="https://api.unify.ai/v0/",
                api_key=self.api_key,
            )
        except openai.OpenAIError as e:
            raise UnifyError(f"Failed to initialize Unify client: {str(e)}")

    def generate(  # noqa: WPS234, WPS211
        self,
        messages: Union[str, List[Dict[str, str]]],
        system_prompt: Optional[str] = None,
        model: str = "llama-2-13b-chat",
        provider: str = "anyscale",
        stream: bool = False,
    ) -> Union[Generator[str, None, None], str]:  # noqa: DAR101, DAR201
        """Generate content using the Unify API.

        Args:
            messages (Union[str, List[Dict[str, str]]]): A single prompt as a
            string or a dictionary containing the conversation history.
            system_prompt (Optinal[str]): An optional string containing the
            system prompt.
            model (str): The name of the model. Defaults to "llama-2-13b-chat".
            provider (str): The provider of the model. Defaults to "anyscale".
            stream (bool): If True, generates content as a stream.
            If False, generates content as a single response.
            Defaults to False.

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

        if isinstance(messages, str):
            contents.append({"role": "user", "content": messages})
        else:
            contents.extend(messages)

        if stream:
            return self._generate_stream(contents, model, provider)
        return self._generate_non_stream(contents, model, provider)

    def get_credit_balance(self) -> Optional[int]:
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
            "Authorization": f"Bearer {self.api_key}",
        }
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            return response.json()["credits"]
        except requests.RequestException as e:
            raise BadRequestError("There was an error with the request.") from e
        except (KeyError, ValueError) as e:
            raise ValueError("Error parsing JSON response.") from e

    def _generate_stream(
        self,
        messages: List[Dict[str, str]],
        model: str,
        provider: str,
    ) -> Generator[str, None, None]:
        try:
            chat_completion = self.client.chat.completions.create(
                model="@".join([model, provider]),
                messages=messages,  # type: ignore[arg-type]
                stream=True,
            )
            for chunk in chat_completion:
                content = chunk.choices[0].delta.content  # type: ignore[union-attr]
                if content is not None:
                    yield content
        except openai.APIStatusError as e:
            raise status_error_map[e.status_code](e.message) from None

    def _generate_non_stream(
        self,
        messages: List[Dict[str, str]],
        model: str,
        provider: str,
    ) -> str:
        try:
            chat_completion = self.client.chat.completions.create(
                model="@".join([model, provider]),
                messages=messages,  # type: ignore[arg-type]
                stream=False,
            )
            return chat_completion.choices[0].message.content.strip(" ")  # type: ignore # noqa: E501, WPS219
        except openai.APIStatusError as e:
            raise status_error_map[e.status_code](e.message) from None


class AsyncUnify:
    """Class for interacting asynchronously with the Unify API."""

    def __init__(
        self,
        api_key: Optional[str] = None,
    ) -> None:  # noqa:DAR101, DAR401
        """Initialize the AsyncUnify client.

        Args:
            api_key (str, optional): API key for accessing the Unify API.
            If None, it attempts to retrieve the API key from
            the environment variable UNIFY_KEY.
            Defaults to None.

        Raises:
            UnifyError: If the API key is missing.
        """
        self.api_key = _validate_api_key(api_key)
        try:
            self.client = openai.AsyncOpenAI(
                base_url="https://api.unify.ai/v0/",
                api_key=self.api_key,
            )
        except openai.APIStatusError as e:
            raise UnifyError(f"Failed to initialize Unify client: {str(e)}")

    def get_credit_balance(self) -> Optional[int]:
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
            "Authorization": f"Bearer {self.api_key}",
        }
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            return response.json()["credits"]
        except requests.RequestException as e:
            raise BadRequestError("There was an error with the request.") from e
        except (KeyError, ValueError) as e:
            raise ValueError("Error parsing JSON response.") from e

    async def generate(  # noqa: WPS234, WPS211
        self,
        messages: Union[str, List[Dict[str, str]]],
        system_prompt: Optional[str] = None,
        model: str = "llama-2-13b-chat",
        provider: str = "anyscale",
        stream: bool = False,
    ) -> Union[AsyncGenerator[str, None], str]:  # noqa: DAR101, DAR201
        """Generate content asynchronously using the Unify API.

        Args:
            messages (Union[str, List[Dict[str, str]]]): A single prompt as a
            string or a dictionary containing the conversation history.
            system_prompt (Optinal[str]): An optional string containing the
            system prompt.
            model (str): The name of the model. Defaults to "llama-2-13b-chat".
            provider (str): The provider of the model. Defaults to "anyscale".
            stream (bool): If True, generates content as a stream.
            If False, generates content as a single response.
            Defaults to False.

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

        if isinstance(messages, str):
            contents.append({"role": "user", "content": messages})
        else:
            contents.extend(messages)

        if stream:
            return self._generate_stream(contents, model, provider)
        return await self._generate_non_stream(contents, model, provider)

    async def _generate_stream(
        self,
        messages: List[Dict[str, str]],
        model: str,
        provider: str,
    ) -> AsyncGenerator[str, None]:
        try:
            async with self.client as async_client:
                async_stream = await async_client.chat.completions.create(
                    model="@".join([model, provider]),
                    messages=messages,  # type: ignore[arg-type]
                    stream=True,
                )
                async for chunk in async_stream:  # type: ignore[union-attr]
                    yield chunk.choices[0].delta.content or ""
        except openai.APIStatusError as e:
            raise status_error_map[e.status_code](e.message) from None

    async def _generate_non_stream(
        self,
        messages: List[Dict[str, str]],
        model: str,
        provider: str,
    ) -> str:
        try:
            async with self.client as async_client:
                async_response = await async_client.chat.completions.create(
                    model="@".join([model, provider]),
                    messages=messages,  # type: ignore[arg-type]
                    stream=False,
                )
            return async_response.choices[0].message.content.strip(" ")  # type: ignore # noqa: E501, WPS219
        except openai.APIStatusError as e:
            raise status_error_map[e.status_code](e.message) from None
