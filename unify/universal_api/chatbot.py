import asyncio
import sys
from typing import Dict, Union

import unify
from unify.universal_api.clients import _Client, _MultiClient, _UniClient


class ChatBot:  # noqa: WPS338
    """Agent class represents an LLM chat agent."""

    def __init__(
        self,
        client: _Client,
    ) -> None:
        """
        Initializes the ChatBot object, wrapped around a client.

        Args:
            client: The Client instance to wrap the chatbot logic around.
        """
        self._paused = False
        assert not client.return_full_completion, (
            "ChatBot currently only supports clients which only generate the message "
            "content in the return"
        )
        self._client = client
        self.clear_chat_history()

    @property
    def client(self) -> _Client:
        """
        Get the client object.  # noqa: DAR201.

        Returns:
            The client.
        """
        return self._client

    def set_client(self, value: client) -> None:
        """
        Set the client.  # noqa: DAR101.

        Args:
            value: The unify client.
        """
        if isinstance(value, _Client):
            self._client = value
        else:
            raise Exception("Invalid client!")

    def _get_credits(self) -> float:
        """
        Retrieves the current credit balance from associated with the UNIFY account.

        Returns:
            Current credit balance.
        """
        return self._client.get_credit_balance()

    def _update_message_history(
        self,
        role: str,
        content: Union[str, Dict[str, str]],
    ) -> None:
        """
        Updates message history with user input.

        Args:
            role: Either "assistant" or "user".
            content: User input message.
        """
        if isinstance(self._client, _UniClient):
            self._client.messages.append(
                {
                    "role": role,
                    "content": content,
                },
            )
        elif isinstance(self._client, _MultiClient):
            if isinstance(content, str):
                content = {endpoint: content for endpoint in self._client.endpoints}
            for endpoint, cont in content.items():
                self._client.messages[endpoint].append(
                    {
                        "role": role,
                        "content": cont,
                    },
                )
        else:
            raise Exception(
                "client must either be a UniClient or MultiClient instance.",
            )

    def clear_chat_history(self) -> None:
        """Clears the chat history."""
        if isinstance(self._client, _UniClient):
            self._client.set_messages([])
        elif isinstance(self._client, _MultiClient):
            self._client.set_messages(
                {endpoint: [] for endpoint in self._client.endpoints},
            )
        else:
            raise Exception(
                "client must either be a UniClient or MultiClient instance.",
            )

    @staticmethod
    def _stream_response(response) -> str:
        words = ""
        for chunk in response:
            words += chunk
            sys.stdout.write(chunk)
            sys.stdout.flush()
        sys.stdout.write("\n")
        return words

    def _handle_uni_llm_response(
        self,
        response: str,
        endpoint: Union[bool, str],
    ) -> str:
        if endpoint:
            endpoint = self._client.endpoint if endpoint is True else endpoint
            sys.stdout.write(endpoint + ":\n")
        if self._client.stream:
            words = self._stream_response(response)
        else:
            words = response
            sys.stdout.write(words)
            sys.stdout.write("\n\n")
        return words

    def _handle_multi_llm_response(self, response: Dict[str, str]) -> Dict[str, str]:
        for endpoint, resp in response.items():
            self._handle_uni_llm_response(resp, endpoint)
        return response

    def _handle_response(
        self,
        response: Union[str, Dict[str, str]],
        show_endpoint: bool,
    ) -> None:
        if isinstance(self._client, _UniClient):
            response = self._handle_uni_llm_response(response, show_endpoint)
        elif isinstance(self._client, _MultiClient):
            response = self._handle_multi_llm_response(response)
        else:
            raise Exception(
                "client must either be a UniClient or MultiClient instance.",
            )
        self._update_message_history(
            role="assistant",
            content=response,
        )

    def run(self, show_credits: bool = False, show_endpoint: bool = False) -> None:
        """
        Starts the chat interaction loop.

        Args:
            show_credits: Whether to show credit consumption. Defaults to False.
            show_endpoint: Whether to show the endpoint used. Defaults to False.
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
            self._update_message_history(role="user", content=inp)
            initial_credit_balance = self._get_credits()
            if isinstance(self._client, unify.AsyncUnify):
                response = asyncio.run(self._client.generate())
            else:
                response = self._client.generate()
            self._handle_response(response, show_endpoint)
            final_credit_balance = self._get_credits()
            if show_credits:
                sys.stdout.write(
                    "\n(spent {:.6f} credits)".format(
                        initial_credit_balance - final_credit_balance,
                    ),
                )
