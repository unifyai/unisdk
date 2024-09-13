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
models = unify.list_models()
providers = unify.list_providers()
endpoints = unify.list_endpoints()
```

You can also filter within these functions as follows:

```python
import random
anthropic_models = unify.list_models("anthropic")
client.set_endpoint(random.choice(anthropic_models) + "@anthropic")

latest_llama3p1_providers = unify.list_providers("llama-3.1-405b-chat")
client.set_endpoint("llama-3.1-405b-chat@" + random.choice(latest_llama3p1_providers))

openai_endpoints = unify.list_endpoints("openai")
client.set_endpoint(random.choice(openai_endpoints))

mixtral8x7b_endpoints = unify.list_endpoints("mixtral-8x7b-instruct-v0.1")
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

You can influence the model's persona using the `system_message` argument in the `.generate` function:

```python
response = client.generate(
    user_message="Hello Llama! Who was Isaac Newton?",  system_message="You should always talk in rhymes"
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

### Default Arguments

When querying LLMs, you often want to keep many aspects of your prompt fixed,
and only change a small subset of the prompt on each subsequent call.

For example, you might want to fix the temperate, the system prompt,
and the tools available, whilst passing different user messages coming from a downstream
application. All of the clients in unify make this very simple via default arguments,
which can be specified in the constructor,
and can also be set any time using setters methods.

For example, the following code will pass `temperature=0.5` to all subsequent requests,
without needing to be repeatedly passed into the `.generate()` method.

```python
client = unify.Unify("claude-3-haiku@anthropic", temperature=0.5)
client.generate("Hello world!")
client.generate("What a nice day.")
```

All parameters can also be retrieved by getters, and set via setters:

```python
client = unify.Unify("claude-3-haiku@anthropic", temperature=0.5)
print(client.temperature)  # 0.5
client.set_temperature(1.0)
print(client.temperature)  # 1.0
```

Passing a value to the `.generate()` method will *overwrite* the default value specified
for the client.

```python
client = unify.Unify("claude-3-haiku@anthropic", temperature=0.5)
client.generate("Hello world!") # temperature of 0.5
client.generate("What a nice day.", temperature=1.0) # temperature of 1.0
```

## Asynchronous Usage
For optimal performance in handling multiple user requests simultaneously,
such as in a chatbot application, processing them asynchronously is recommended.
A minimal example using `AsyncUnify` is given below:

 ```python
import unify
import asyncio
async_client = unify.AsyncUnify("llama-3-8b-chat@fireworks-ai")
asyncio.run(async_client.generate("Hello Llama! Who was Isaac Newton?"))
```

More a more applied example,
processing multiple requests in parallel can then be done as follows:

 ```python
import unify
import asyncio
clients = dict()
clients["gpt-4o@openai"] = unify.AsyncUnify("gpt-4o@openai")
clients["claude-3-opus@anthropic"] = unify.AsyncUnify("claude-3-opus@anthropic")
clients["llama-3-8b-chat@fireworks-ai"] = unify.AsyncUnify("llama-3-8b-chat@fireworks-ai")


async def generate_responses(user_message: str):
    responses_ = dict()
    for endpoint_, client in clients.items():
        responses_[endpoint_] = await client.generate(user_message)
    return responses_

responses = asyncio.run(generate_responses("Hello, how's it going?"))
for endpoint, response in responses.items():
    print("endpoint: {}".format(endpoint))
    print("response: {}\n".format(response))
```

Functionality wise, the asynchronous and synchronous clients are identical.

## Streaming Responses
You can enable streaming responses by setting `stream=True` in the `.generate` function.

```python
import unify
client = unify.Unify("llama-3-8b-chat@fireworks-ai")
stream = client.generate("Hello Llama! Who was Isaac Newton?", stream=True)
for chunk in stream:
    print(chunk, end="")
```

It works in exactly the same way with Async clients.

 ```python
import unify
import asyncio
async_client = unify.AsyncUnify("llama-3-8b-chat@fireworks-ai")

async def stream():
    async_stream = await async_client.generate("Hello Llama! Who was Isaac Newton?", stream=True)
    async for chunk in async_stream:
        print(chunk, end="")

asyncio.run(stream())
```
## Dive Deeper

To learn more about our more advanced API features, benchmarking, and LLM routing,
go check out our comprehensive [docs](https://unify.ai/docs)!