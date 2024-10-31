import json
import unittest

from openai.types.chat.chat_completion_message import ChatCompletionMessage
from openai.types.chat.chat_completion_message_tool_call import (
    ChatCompletionMessageToolCall,
    Function,
)
from unify import Unify


def test_openai_tool_use() -> None:
    # adapted from: https://cookbook.openai.com/examples/how_to_call_functions_with_chat_models # noqa
    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_n_day_weather_forecast",
                "description": "Get an N-day weather forecast",
                "params": {
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

    client = Unify(endpoint="gpt-4o@openai")
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
    assert isinstance(message, ChatCompletionMessage)
    tool_calls = message.tool_calls
    assert isinstance(tool_calls, list)
    assert len(tool_calls) == 1
    tool_call = tool_calls[0]
    assert isinstance(tool_call, ChatCompletionMessageToolCall)
    function = tool_call.function
    assert isinstance(function, Function)
    arguments = function.arguments
    assert isinstance(arguments, str)
    arguments = json.loads(arguments)
    assert isinstance(arguments, dict)
    assert "location" in arguments
    assert "format" in arguments
    assert "num_days" in arguments


if __name__ == "__main__":
    unittest.main()
