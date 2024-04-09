import sys

from typing import Optional
from unifyai.clients import Unify


class ChatBot:  # noqa: WPS338
    """Agent class represents an LLM chat agent."""

    def __init__(self, api_key: Optional[str] = None, endpoint: Optional[str] = "llama-2-7b-chat@anyscale") -> None:
        """
        Initializes the ChatBot object.

        Args:
            api_key (optional, str): Your UNIFY key.
            endpoint (optional, str): The endpoint for the chatbot.
        """
        self._message_history = []
        self._endpoint = endpoint
        self._api_key = api_key
        self._paused = False
        self._client = Unify(
            api_key=self._api_key,
            endpoint=self._endpoint,
        )

    def _get_credits(self):
        """
        Retrieves the current credit balance from associated with the UNIFY account.

        Returns:
            float: Current credit balance.
        """
        return self._client.get_credit_balance()

    def _process_input(self, inp: str, show_credits: bool, show_provider: bool):
        """
        Processes the user input to generate AI response.

        Args:
            inp (str): User input message.
            show_credits (bool): Whether to show credit consumption.

        Yields:
            str: Generated AI response chunks.
        """
        self._update_message_history(inp)
        initial_credit_balance = self._get_credits()
        stream = self._client.generate(
            messages=self._message_history,
            stream=True,
        )
        words = ""
        for chunk in stream:
            words += chunk
            yield chunk

        self._message_history.append(
            {
                "role": "assistant",
                "content": words,
            },
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

    def _update_message_history(self, inp):
        """
        Updates message history with user input.

        Args:
            inp (str): User input message.
        """
        self._message_history.append(
            {
                "role": "user",
                "content": inp,
            },
        )

    @property
    def endpoint(self):
        return self._endpoint

    @endpoint.setter
    def endpoint(self, value):
        self._endpoint = value
        self._client.set_endpoint(self._endpoint)

    def clear_chat_history(self):
        """Clears the chat history."""
        self._message_history.clear()

    def run(self, show_credits: bool = False, show_provider: bool = False):
        """
        Starts the chat interaction loop.

        Args:
            show_credits (bool, optional): Whether to show credit consumption. Defaults to False.
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
