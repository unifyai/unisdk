from .utils import register_model_alias_map

models = {
    "gpt-oss-20b": "together_ai/openai/gpt-oss-20b",
    "gpt-oss-120b": "together_ai/openai/gpt-oss-120b",
    "deepseek-v3.1": "together_ai/deepseek-ai/DeepSeek-V3.1",
    "deepseek-r1": "together_ai/deepseek-ai/DeepSeek-R1",
    "deepseek-v3": "together_ai/deepseek-ai/DeepSeek-V3",
    "llama-4-maverick-instruct": "together_ai/meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8",
    "llama-3.3-70b-chat": "together_ai/meta-llama/Llama-3.3-70B-Instruct-Turbo",
    "llama-3.2-3b-chat": "together_ai/meta-llama/Llama-3.2-3B-Instruct-Turbo",
    "llama-3.1-70b-chat": "together_ai/meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",
    "llama-3.1-405b-chat": "together_ai/meta-llama/Meta-Llama-3.1-405B-Instruct-Turbo",
    "mistral-small": "mistralai/Mistral-Small-24B-Instruct-2501",
    "qwen-3-235b-a22b-instruct": "together_ai/Qwen/Qwen3-235B-A22B-fp8-tput",
    "qwen-2.5-7b-instruct": "together_ai/Qwen/Qwen2.5-7B-Instruct-Turbo",
    "qwen-2.5-72b-instruct": "together_ai/Qwen/Qwen2.5-72B-Instruct-Turbo",
}
register_model_alias_map("togetherai", models)
