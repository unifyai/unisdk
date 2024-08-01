# Unify

We're on a mission to simplify the LLM landscape, Unify lets you:

* **🔑 Use any LLM from any Provider**: With a single interface, you can use all LLMs from all providers by simply changing one string. No need to manage several API keys or handle different input-output formats. Unify handles all of that for you!


* **📊 Improve LLM Performance**: Add your own custom tests and evals, and benchmark your own prompts on all models and providers. Comparing quality, cost and speed, and iterate on your system prompt until all test cases pass, and you can deploy your app!


* **🔀 Route to the Best LLM**: Improve quality, cost and speed by routing to the perfect model and provider for each individual prompt.

## Quickstart
Simply install the package:

```bash
pip install unifyai
```

Then [sign up](https://console.unify.ai) to get your API key, then you're ready to go! 🚀

```python
import unify
client = unify.Unify("gpt-4o@openai", api_key=<your_key>)
client.generate("hello world!")
```

> [!NOTE]
> We recommend using [python-dotenv](https://pypi.org/project/python-dotenv/)
> to add `UNIFY_KEY="My API Key"` to your `.env` file, avoiding the need to use the `api_key` argument as above.
> For the rest of the README, **we will assume you set your key as an environment variable.**

### Listing Models, Providers and Endpoints

You can list all models, providers and endpoints (`<model>@<provider>` pair) as follows:

```python
models = unify.utils.list_models()
providers = unify.utils.list_providers()
endpoints = unify.utils.list_endpoints()
```

You can also filter within these functions as follows:

```python
import random
anthropic_models = unify.utils.list_models("anthropic")
client.set_endpoint(random.choice(anthropic_models) + "@anthropic")

latest_llama3p1_providers = unify.utils.list_providers("llama-3.1-405b-chat")
client.set_endpoint("llama-3.1-405b-chat@" + random.choice(latest_llama3p1_providers))

openai_endpoints = unify.utils.list_endpoints("openai")
client.set_endpoint(random.choice(openai_endpoints))

mixtral8x7b_endpoints = unify.utils.list_endpoints("mixtral-8x7b-instruct-v0.1")
client.set_endpoint(random.choice(mixtral8x7b_endpoints))

```

### Changing Models, Providers and Endpoints

If you want change the `endpoint`, `model` or the `provider`, you can do so using the `.set_endpoint`, `.set_model`, `.set_provider` methods respectively.

```python
client.set_endpoint("mistral-7b-instruct-v0.3@deepinfra")
client.set_model("mistral-7b-instruct-v0.3")
client.set_provider("deepinfra")
```

### Custom Prompting

You can influence the model's persona using the `system_prompt` argument in the `.generate` function:

```python
response = client.generate(
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
res = client.generate(messages=messages)
 ```

## Asynchronous Usage
For optimal performance in handling multiple user requests simultaneously, such as in a chatbot application, processing them asynchronously is recommended.
To use the AsyncUnify client, simply import `AsyncUnify` instead
 of `Unify` and use `await` with the `.generate` function.

 ```python
import unify
import asyncio
async_client = unify.AsyncUnify("llama-3-8b-chat@anyscale")

async def main():
    responses = await async_client.generate("Hello Llama! Who was Isaac Newton?")

asyncio.run(main())
```

Functionality wise, the Async and Sync clients are identical.

## Streaming Responses
You can enable streaming responses by setting `stream=True` in the `.generate` function.

```python
import unify
client = unify.Unify("llama-3-8b-chat@anyscale")
stream = client.generate("Hello Llama! Who was Isaac Newton?", stream=True)
for chunk in stream:
    print(chunk, end="")
```

It works in exactly the same way with Async clients.

 ```python
import unify
import asyncio
async_client = unify.AsyncUnify("llama-3-8b-chat@anyscale")

async def main():
    async_stream = await async_client.generate("Hello Llama! Who was Isaac Newton?", stream=True)
    async for chunk in async_stream:
        print(chunk, end="")

asyncio.run(main())
```
## Dive Deeper

To learn more about our more advanced API features, benchmarking, and LLM routing,
go check out our comprehensive [docs](https://unify.ai/docs)!