import os
import unittest
import builtins
import traceback

from unify import Unify, MultiLLM, ChatBot


class SimulateInput:

    def __init__(self):
        self._messages = [
            "What is the capital of Spain? Be succinct.",
            "Who is their most famous sports player? Be succinct.",
            "quit"
        ]
        self._count = 0
        self._true_input = None

    def _new_input(self):
        message = self._messages[self._count]
        self._count += 1
        print(message)
        return message

    def __enter__(self):
        self._true_input = builtins.__dict__["input"]
        builtins.__dict__["input"] = self._new_input

    def __exit__(self, exc_type, exc_value, tb):
        builtins.__dict__["input"] = self._true_input
        self._count = 0
        if exc_type is not None:
            traceback.print_exception(exc_type, exc_value, tb)
            return False
        return True


class TestChatbotUniLLM(unittest.TestCase):
    def setUp(self) -> None:
        self.valid_api_key = os.environ.get("UNIFY_KEY")

    # Basic #
    # ------#

    def test_constructor(self) -> None:
        client = Unify(
            api_key=self.valid_api_key, endpoint="llama-3-8b-chat@together-ai"
        )
        ChatBot(client)

    def test_simple_non_stream_chat_n_quit(self):
        client = Unify(
            api_key=self.valid_api_key, endpoint="llama-3-8b-chat@together-ai"
        )
        chatbot = ChatBot(client)
        with SimulateInput():
            chatbot.run()

    def test_simple_stream_chat_n_quit(self):
        client = Unify(
            api_key=self.valid_api_key, endpoint="llama-3-8b-chat@together-ai", stream=True,
        )
        chatbot = ChatBot(client)
        with SimulateInput():
            chatbot.run()


class TestChatbotMultiLLM(unittest.TestCase):
    def setUp(self) -> None:
        self.valid_api_key = os.environ.get("UNIFY_KEY")

    # Basic #
    # ------#

    def test_constructor(self) -> None:
        client = MultiLLM(
            api_key=self.valid_api_key,
            endpoints=[
                "llama-3-8b-chat@together-ai",
                "gpt-4o@openai"
            ]
        )
        ChatBot(client)

    def test_simple_non_stream_chat_n_quit(self):
        client = MultiLLM(
            api_key=self.valid_api_key,
            endpoints=[
                "llama-3-8b-chat@together-ai",
                "gpt-4o@openai"
            ]
        )
        chatbot = ChatBot(client)
        with SimulateInput():
            chatbot.run()


if __name__ == "__main__":
    unittest.main()
