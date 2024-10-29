import json
import os
import unittest

from openai.types.chat.chat_completion_message import ChatCompletionMessage
from openai.types.chat.chat_completion_message_tool_call import (
    ChatCompletionMessageToolCall,
    Function,
)
from unify import Unify


class TestUnifyToolUse(unittest.TestCase):
    def setUp(self) -> None:
        self.valid_api_key = os.environ.get("UNIFY_KEY")

    def test_openai_tool_use(self) -> None:
        # adapted from: https://cookbook.openai.com/examples/how_to_call_functions_with_chat_models # noqa
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "get_n_day_weather_forecast",
                    "description": "Get an N-day weather forecast",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "location": {
                                "type": "string",
                                "description": (
                                    "The city and state, e.g. San Francisco, CA"
                                ),
                            },
                            "format": {
                                "type": "string",
                                "enum": ["celsius", "fahrenheit"],
                                "description": (
                                    "The temperature unit to use. Infer this "
                                    "from the users location."
                                ),
                            },
                            "num_days": {
                                "type": "integer",
                                "description": "The number of days to forecast",
                            },
                        },
                        "required": ["location", "format", "num_days"],
                    },
                },
            },
        ]

        client = Unify(api_key=self.valid_api_key, endpoint="gpt-4o@openai")
        result = client.generate(
            user_message=(
                "What is the weather going to be like in Glasgow, Scotland over "
                "the next 5 days?"
            ),
            tool_choice="required",
            tools=tools,
            return_full_completion=True,
        )
        message = result.choices[0].message
        self.assertIsInstance(message, ChatCompletionMessage)
        tool_calls = message.tool_calls
        self.assertIsInstance(tool_calls, list)
        self.assertEqual(len(tool_calls), 1)
        tool_call = tool_calls[0]
        self.assertIsInstance(tool_call, ChatCompletionMessageToolCall)
        function = tool_call.function
        self.assertIsInstance(function, Function)
        arguments = function.arguments
        self.assertIsInstance(arguments, str)
        arguments = json.loads(arguments)
        self.assertIsInstance(arguments, dict)
        self.assertIn("location", arguments)
        self.assertIn("format", arguments)
        self.assertIn("num_days", arguments)

    @unittest.skip("known problem, on backlog to fix")
    def test_anthropic_function_calling(self) -> None:
        # adapted from: https://cookbook.openai.com/examples/how_to_call_functions_with_chat_models and # noqa
        # https://docs.anthropic.com/en/docs/build-with-claude/tool-use#single-tool-example
        tools = [
            {
                "name": "get_n_day_weather_forecast",
                "description": "Get an N-day weather forecast",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "The city and state, e.g. San Francisco, CA",
                        },
                        "format": {
                            "type": "string",
                            "enum": ["celsius", "fahrenheit"],
                            "description": (
                                "The temperature unit to use. Infer this from "
                                "the users location."
                            ),
                        },
                        "num_days": {
                            "type": "integer",
                            "description": "The number of days to forecast",
                        },
                    },
                    "required": ["location", "format", "num_days"],
                },
            },
        ]

        client = Unify(api_key=self.valid_api_key, endpoint="claude-3-opus@anthropic")
        client.generate(
            user_message=(
                "What is the weather going to be like in Glasgow, Scotland"
                "over the next 5 days?"
            ),
            tool_choice={"type": "any"},
            tools=tools,
            return_full_completion=True,
        )


if __name__ == "__main__":
    unittest.main()
