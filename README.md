# Unify Python API Library
The Unify Python Package provides access to the [Unify](https://unify.ai) REST API, allowing you to query Large Language Models (LLMs)
from any Python 3.7.1+ application.
It includes Synchronous and Asynchronous clients with Streaming responses support.

Just like the REST API, you can:

- 🔑 **Use any endpoint with a single key**: Access all LLMs at any provider with just one Unify API Key.

- 🚀 **Route to the best endpoint**: Each prompt is sent to the endpoint that will yield the best throughput, cost or latency. 

> [!NOTE]
> You can learn more about routing [here](https://unify.ai/docs/concepts/routing.html)

## Getting started
To use the API, you first need to get [Sign In](https://console.unify.ai) to get an API key. You can then use pip to install the package as follows:

```bash
pip install unifyai
```

> [!NOTE]
> At any point, you can pass your key directly in one of the `Unify` clients as the `api_key` keyword argument, but
> we recommend using [python-dotenv](https://pypi.org/project/python-dotenv/)
> to add `UNIFY_KEY="My API Key"` to your `.env` file for safety.
> For the rest of the README, **we will assume you set your key as an environment variable.**


## Basic Usage
You can call the Unify API in a couple lines of code by specifying an endpoint Id. Endpoint Ids are a combination of the model Id and provider Id, both of which can be found in the [endpoint benchmarks](https://unify.ai/benchmarks) pages.

For e.g, the [benchmarks for llama-2-13b](https://unify.ai/benchmarks/llama-2-13b-chat) show that the model Id for Llama 2 13B is `llama-2-13b-chat` and the provider Id for Anyscale is `anyscale`. We can then call:

```python
from unify import Unify
unify = Unify("llama-2-13b-chat@anyscale")
response = unify.generate("Hello Llama! Who was Isaac Newton?")
```

### Changing models and providers

Instead of passing the endpoint, you can also pass the `model` and `provider` as separate arguments as shown below:
```python
unify = Unify(
    model="llama-2-13b-chat",
    provider="anyscale"
)
```

If you want change the `endpoint`, `model` or the `provider`, you can do so using the `.set_endpoint`, `.set_model`, `.set_provider` methods respectively.

```python
unify.set_endpoint("mistral-7b-instruct-v0.1@deepinfra")
unify.set_model("mistral-7b-instruct-v0.1")
unify.set_provider("deepinfra")
```

>[!NOTE]
> Besides the benchmarks, you can also get the model and provider Ids directly in Python using `list_models()>`, `list_providers()` and `list_endpoints()` by using:
>
>```python
>models = unify.list_models()
>providers = unify.list_providers("mistral-7b-instruct-v0.1")
>endpoints = unify.list_endpoints("mistral-7b-instruct-v0.1")
>```

### Custom prompting

You can influence the model's persona using the `system_prompt` argument in the `.generate` function:

```python
response = unify.generate(
    user_prompt="Hello Llama! Who was Isaac Newton?",  system_prompt="You should always talk in rhymes"
)
```

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
from unify import AsyncUnify
import asyncio
async_unify = AsyncUnify("llama-2-13b-chat@anyscale")

async def main():
    responses = await async_unify.generate("Hello Llama! Who was Isaac Newton?")

asyncio.run(main())
```

Functionality wise, the Async and Sync clients are identical.

## Streaming Responses
You can enable streaming responses by setting `stream=True` in the `.generate` function.

```python
from unify import Unify
unify = Unify("llama-2-13b-chat@anyscale")
stream = unify.generate("Hello Llama! Who was Isaac Newton?", stream=True)
for chunk in stream:
    print(chunk, end="")
```

It works in exactly the same way with Async clients.

 ```python
from unify import AsyncUnify
import asyncio
async_unify = AsyncUnify("llama-2-13b-chat@anyscale")

async def main():
    async_stream = await async_unify.generate("Hello Llama! Who was Isaac Newton?", stream=True)
    async for chunk in async_stream:
        print(chunk, end="")

asyncio.run(main())
```
## Dynamic Routing

As evidenced by our [benchmarks](https://unify.ai/benchmarks), the optimal provider for each model varies by geographic location and time of day due to fluctuating API performances.

With dynamic routing, we automatically direct your requests to the "top-performing provider" at that moment. To enable this feature, simply replace your query's provider with one of the [available routing modes](https://unify.ai/docs/api/deploy_router.html#optimizing-a-metric).

For e.g, you can query the `llama-2-7b-chat` endpoint to get the provider with the lowest input-cost as follows:

```python
from unify import Unify
unify = Unify("llama-2-13b-chat@lowest-input-cost")
response = unify.generate("Hello Llama! Who was Isaac Newton?")
```

You can see the provider chosen by printing the `.provider` attribute of the client:

```python
print(unify.provider)
```

>[!NOTE]
> Dynamic routing works with both Synchronous and Asynchronous  clients!

## ChatBot Agent

Our `ChatBot` allows you to start an interactive chat session with any of our supported llm endpoints with only a few lines of code:

```python
from unify import ChatBot
agent = ChatBot("llama-2-13b-chat@lowest-input-cost")
agent.run()
```
