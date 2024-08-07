import sys
from typing import Dict, Generator, List, Optional

from unify.clients import Unify
from unify.exceptions import UnifyError


class ChatBot:  # noqa: WPS338
    """Agent class represents an LLM chat agent."""

    def __init__(
        self,
        endpoint: Optional[str] = None,
        model: Optional[str] = None,
        provider: Optional[str] = None,
        api_key: Optional[str] = None,
    ) -> None:
        """
        Initializes the ChatBot object.

        Args:
            endpoint (str, optional): Endpoint name in OpenAI API format:
                <uploaded_by>/<model_name>@<provider_name>
                Defaults to None.

            model (str, optional): Name of the model. If None,
            endpoint must be provided.

            provider (str, optional): Name of the provider. If None,
            endpoint must be provided.

            api_key (str, optional): API key for accessing the Unify API.
                If None, it attempts to retrieve the API key from the
                environment variable UNIFY_KEY.
                Defaults to None.

        Raises:
            UnifyError: If the API key is missing.
        """
        self._message_history: List[Dict[str, str]] = []
        self._paused = False
        self._client = Unify(
            api_key=api_key,
            endpoint=endpoint,
            model=model,
            provider=provider,
        )

    @property
    def client(self) -> Unify:
        """
        Get the client object.  # noqa: DAR201.

        Returns:
            str: The model name.
        """
        return self._client

    def set_client(self, value: Unify) -> None:
        """
        Set the model name.  # noqa: DAR101.

        Args:
            value: The unify client.
        """
        if isinstance(value, Unify):
            self._client = value
        else:
            raise UnifyError("Invalid client!")

    @property
    def model(self) -> str:
        """
        Get the model name.  # noqa: DAR201.

        Returns:
            str: The model name.
        """
        return self._client.model

    def set_model(self, value: str) -> None:
        """
        Set the model name.  # noqa: DAR101.

        Args:
            value (str): The model name.
        """
        self._client.set_model(value)
        if self._client.provider:
            self._client.set_endpoint("@".join([value, self._client.provider]))
        else:
            mode = self._client.endpoint.split("@")[1]
            self._client.set_endpoint("@".join([value, mode]))

    @property
    def provider(self) -> Optional[str]:
        """
        Get the provider name.  # noqa :DAR201.

        Returns:
            str: The provider name.
        """
        return self._client.provider

    def set_provider(self, value: str) -> None:
        """
        Set the provider name.  # noqa: DAR101.

        Args:
            value (str): The provider name.
        """
        self._client.set_provider(value)
        self._client.set_endpoint("@".join([self._client._model, value]))

    @property
    def endpoint(self) -> str:
        """
        Get the endpoint name.  # noqa: DAR201.

        Returns:
            str: The endpoint name.
        """
        return self._client.endpoint

    def set_endpoint(self, value: str) -> None:
        """
        Set the model name.  # noqa: DAR101.

        Args:
            value (str): The endpoint name.
        """
        self._client.set_endpoint(value)
        self._client.set_model(value.split("@")[0])
        self._client.set_provider(value.split("@")[1])

    def _get_credits(self) -> float:
        """
        Retrieves the current credit balance from associated with the UNIFY account.

        Returns:
            float: Current credit balance.
        """
        return self._client.get_credit_balance()

    def _process_input(
        self, inp: str, show_credits: bool, show_provider: bool
    ) -> Generator[str, None, None]:
        """
        Processes the user input to generate AI response.

        Args:
            inp (str): User input message.
            show_credits (bool): Whether to show credit consumption.
            show_credits (bool): Whether to show provider used.

        Yields:
            str: Generated AI response chunks.
        """
        self._update_message_history(role="user", content=inp)
        initial_credit_balance = self._get_credits()
        stream = self._client.generate(
            messages=self._message_history,
            stream=True,
        )
        words = ""
        for chunk in stream:
            words += chunk
            yield chunk

        self._update_message_history(
            role="assistant",
            content=words,
        )
        final_credit_balance = self._get_credits()
        if show_credits:
            sys.stdout.write(
                "\n(spent {:.6f} credits)".format(
                    initial_credit_balance - final_credit_balance,
                ),
            )
        if show_provider:
            sys.stdout.write("\n(provider: {})".format(self._client.provider))

    def _update_message_history(self, role: str, content: str) -> None:
        """
        Updates message history with user input.

        Args:
            role (str): Either "assistant" or "user".
            content (str): User input message.
        """
        self._message_history.append(
            {
                "role": role,
                "content": content,
            },
        )

    def clear_chat_history(self) -> None:
        """Clears the chat history."""
        self._message_history.clear()

    def run(self, show_credits: bool = False, show_provider: bool = False) -> None:
        """
        Starts the chat interaction loop.

        Args:
            show_credits (bool, optional): Whether to show credit consumption.
            Defaults to False.
            show_provider (bool, optional): Whether to show the provider used.
            Defaults to False.
        """
        if not self._paused:
            sys.stdout.write(
                "Let's have a chat. (Enter `pause` to pause and `quit` to exit)\n",
            )
            self.clear_chat_history()
        else:
            sys.stdout.write(
                "Welcome back! (Remember, enter `pause` to pause and `quit` to exit)\n",
            )
        self._paused = False
        while True:
            sys.stdout.write("> ")
            inp = input()
            if inp == "quit":
                self.clear_chat_history()
                break
            elif inp == "pause":
                self._paused = True
                break
            for word in self._process_input(inp, show_credits, show_provider):
                sys.stdout.write(word)
                sys.stdout.flush()
            sys.stdout.write("\n")
