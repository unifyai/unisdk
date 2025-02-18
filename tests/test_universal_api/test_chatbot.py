import pytest
import builtins
import traceback

from unify import ChatBot, MultiUnify, Unify


class SimulateInput:
    def __init__(self):
        self._messages = [
            "What is the capital of Spain? Be succinct.",
            "Who is their most famous sports player? Be succinct.",
            "quit",
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


class TestChatbotUniLLM:
    def test_constructor(self) -> None:
        client = Unify(
            endpoint="gpt-4o@openai",
            cache=True,
        )
        ChatBot(client)

    def test_simple_non_stream_chat_n_quit(self):
        client = Unify(
            endpoint="gpt-4o@openai",
            cache=True,
        )
        chatbot = ChatBot(client)
        with SimulateInput():
            chatbot.run()

    @pytest.mark.skip()
    def test_simple_stream_chat_n_quit(self):
        client = Unify(
            endpoint="gpt-4o@openai",
            cache=True,
            stream=True,
        )
        chatbot = ChatBot(client)
        with SimulateInput():
            chatbot.run()


class TestChatbotMultiUnify:
    def test_constructor(self) -> None:
        client = MultiUnify(
            endpoints=["gpt-4@openai", "gpt-4o@openai"],
            cache=True,
        )
        ChatBot(client)

    def test_simple_non_stream_chat_n_quit(self):
        client = MultiUnify(
            endpoints=["gpt-4@openai", "gpt-4o@openai"],
            cache=True,
        )
        chatbot = ChatBot(client)
        with SimulateInput():
            chatbot.run()


if __name__ == "__main__":
    pass
