# Unify Python API Library
The Unify Python Package provides access to the [Unify](https://unify.ai) REST API, allowing you to query Large Language Models (LLMs)
from any Python 3.7.1+ application.
It includes Synchronous and Asynchronous clients with Streaming responses support.

Just like the REST API, you can:

- 🔑 **Use any endpoint with one key**: Access all LLMs at any provider with just one Unify API Key.


- 🚀 **Route to the best endpoint**: Each prompt is sent to the endpoint that will yield the best
  performance for your target metric, including high-throughput, low cost or low latency. See
  [the routing section](#dynamic-routing) to learn more about this!

## Installation
You can use pip to install the package as follows:
```bash
pip install unifyai
```

## Basic Usage
```python
import os
from unifyai import Unify
unify = Unify(
    # This is the default and optional to include.
    api_key=os.environ.get("UNIFY_KEY"),
    endpoint="llama-2-13b-chat@anyscale"
)
response = unify.generate(user_prompt="Hello Llama! Who was Isaac Newton?")
```

Here, `response` is a string containing the model's output.

You can also pass the `model` and `provider` as separate arguments as shown below:
```python
unify = Unify(
    # This is the default and optional to include.
    api_key=os.environ.get("UNIFY_KEY"),
    model="llama-2-13b-chat",
    provider="anyscale"
)
```

You can influence the model's persona using the `system_prompt` argument in the `.generate` function:

```python
response = unify.generate(user_prompt="Hello Llama! Who was Isaac Newton?", system_prompt="You should always talk in rhymes")
```

If you want change the `endpoint`, `model` or the `provider`, you can do so using the `.set_endpoint`, `.set_model`, `.set_provider` methods respectively.

```python
unify.set_endpoint("mistral-7b-instruct-v0.1@deepinfra")
unify.set_model("mistral-7b-instruct-v0.1")
unify.set_provider("deepinfra")
```

### Supported Models
The list of supported models and providers is available in [the platform](https://unify.ai/hub).

### API Key
You can get an API Key from [the Unify console](https://console.unify.ai/)

> [!NOTE]
> You can provide an `api_key` keyword argument, but
> we recommend using [python-dotenv](https://pypi.org/project/python-dotenv/)
> to add `UNIFY_KEY="My API Key"` to your `.env` file
> so that your API Key is not stored in source control.

### Sending multiple messages

If you'd like to send multiple messages using the `.generate` function, you should use the `messages` argument as follows:

 ```python
 messages=[
    {"role": "user", "content": "Who won the world series in 2020?"},
    {"role": "assistant", "content": "The Los Angeles Dodgers won the World Series in 2020."},
    {"role": "user", "content": "Where was it played?"}
]
res = unify.generate(messages=messages)
 ```


## Asynchronous Usage
For optimal performance in handling multiple user requests simultaneously, such as in a chatbot application, processing them asynchronously is recommended.
To use the AsyncUnify client, simply import `AsyncUnify` instead
 of `Unify` and use `await` with the `.generate` function.

 ```python
from unifyai import AsyncUnify
import os
import asyncio
async_unify = AsyncUnify(
    # This is the default and optional to include.
    api_key=os.environ.get("UNIFY_KEY"),
    endpoint="llama-2-13b-chat@anyscale"
)

async def main():
    responses = await async_unify.generate(user_prompt="Hello Llama! Who was Isaac Newton?")

asyncio.run(main())
```

Functionality wise, the Async and Sync clients are identical.

## Streaming Responses
You can enable streaming responses by setting `stream=True` in the `.generate` function.

```python
import os
from unifyai import Unify
unify = Unify(
    # This is the default and optional to include.
    api_key=os.environ.get("UNIFY_KEY"),
    endpoint="llama-2-13b-chat@anyscale"
)
stream = unify.generate(user_prompt="Hello Llama! Who was Isaac Newton?", stream=True)
for chunk in stream:
    print(chunk, end="")
```

It works in exactly the same way with Async clients.

 ```python
from unifyai import AsyncUnify
import os
import asyncio
async_unify = AsyncUnify(
    # This is the default and optional to include.
    api_key=os.environ.get("UNIFY_KEY"),
    endpoint="llama-2-13b-chat@anyscale"
)

async def main():
    async_stream = await async_unify.generate(user_prompt="Hello Llama! Who was Isaac Newton?", stream=True)
    async for chunk in async_stream:
        print(chunk, end="")

asyncio.run(main())
```

## Get Current Credit Balance
You can use the `.get_credit_balance` method to the credit balance for the authenticated account as follows:
```python
credits = unify.get_credit_balance()
```

## Dynamic Routing
As evidenced by our [benchmarks](https://unify.ai/hub), the optimal provider for each model varies by geographic location and time of day due to fluctuating API performances. With our dynamic routing, we automatically direct your requests to the "top-performing provider" at that moment. To enable this feature, simply replace your query's provider with one of the [available routing modes](https://unify.ai/docs/hub/concepts/runtime_routing.html#available-modes). As an example, you can query the `llama-2-7b-chat` endpoint to get the provider with the lowest input-cost as follows:

```python
import os
from unifyai import Unify
unify = Unify(
    # This is the default and optional to include.
    api_key=os.environ.get("UNIFY_KEY"),
    endpoint="llama-2-13b-chat@lowest-input-cost"
)
response = unify.generate(user_prompt="Hello Llama! Who was Isaac Newton?")
```
You can see the provider chosen by printing the `.provider` attribute of the client:

```python
print(unify.provider)
```

Dynamic routing works with both Synchronous and Asynchronous clients. For more information on Dynamic Routing, check our [documentation](https://unify.ai/docs/hub/concepts/runtime_routing.html#dynamic-routing).
