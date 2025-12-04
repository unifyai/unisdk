from .utils import register_model_alias_map

models = {
    "llama-4-maverick-instruct": "replicate/meta/llama-4-maverick-instruct",
    "llama-4-scout-instruct": "replicate/meta/llama-4-scout-instruct",
    "llama-3-8b-chat": "replicate/meta/meta-llama-3-8b-instruct",
    "llama-3-70b-chat": "replicate/meta/meta-llama-3-70b-instruct",
    "llama-3.1-405b-chat": "replicate/meta/meta-llama-3.1-405b-instruct",
    "deepseek-v3.1": "replicate/deepseek-ai/deepseek-v3.1",
    "deepseek-v3": "replicate/deepseek-ai/deepseek-v3",
    "deepseek-r1": "replicate/deepseek-ai/deepseek-r1",
    "o4-mini": "replicate/openai/o4-mini",
    "gpt-4.1": "replicate/openai/gpt-4.1",
    "gpt-4.1-mini": "replicate/openai/gpt-4.1-mini",
    "gpt-4.1-nano": "replicate/openai/gpt-4.1-nano",
    "gpt-5": "replicate/openai/gpt-5",
    "gpt-5-mini": "replicate/openai/gpt-5-mini",
    "gpt-5-nano": "replicate/openai/gpt-5-nano",
    "gpt-oss-20b": "replicate/openai/gpt-oss-20b",
    "gpt-oss-120b": "replicate/openai/gpt-oss-120b",
    "gpt-5.1": "replicate/openai/gpt-5.1",
    "claude-4.5-haiku": "replicate/anthropic/claude-4.5-haiku",
    "claude-4.5-sonnet": "replicate/anthropic/claude-4.5-sonnet",
    "claude-4-sonnet": "replicate/anthropic/claude-4-sonnet",
    "claude-3.5-haiku": "replicate/anthropic/claude-3.5-haiku",
    "gemini-3-pro": "replicate/google/gemini-3-pro",
}

register_model_alias_map("replicate", models)
