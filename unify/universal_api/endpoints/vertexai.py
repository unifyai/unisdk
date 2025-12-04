from .utils import register_model_alias_map

models = {
    "gemini-3-pro": "vertex_ai/gemini-3-pro-preview",
    "gemini-2.5-flash-lite": "vertex_ai/gemini-2.5-flash-lite",
    "gemini-2.5-flash": "vertex_ai/gemini-2.5-flash",
    "gemini-2.5-pro": "vertex_ai/gemini-2.5-pro",
    "gemini-2.0-flash-lite": "vertex_ai/gemini-2.0-flash-lite-001",
    "gemini-2.0-flash": "vertex_ai/gemini-2.0-flash-001",
    "claude-3-haiku": "vertex_ai/claude-3-haiku@20240307",
    "claude-3.5-haiku": "vertex_ai/claude-3-5-haiku@20241022",
    "claude-4-sonnet": "vertex_ai/claude-sonnet-4@20250514",
    "claude-4-opus": "vertex_ai/claude-opus-4@20250514",
    "claude-4.1-opus": "vertex_ai/claude-opus-4-1@20250805",
    "claude-4.5-sonnet": "vertex_ai/claude-sonnet-4-5@20250929",
    "claude-4.5-haiku": "vertex_ai/claude-haiku-4-5@20251001",
    "claude-4.5-opus": "vertex_ai/claude-opus-4-5@20251101",
    "llama-3.1-405b-chat": "vertex_ai/meta/llama3-405b-instruct-maas",
    "llama-3.3-70b-chat": "vertex_ai/meta/llama-3.3-70b-instruct-maas",
    "llama-4-maverick-instruct": "vertex_ai/meta/llama-4-maverick-17b-128e-instruct-maas",
    "llama-4-scout-instruct": "vertex_ai/meta/llama-4-scout-17b-16e-instruct-maas",
    "mistral-medium": "vertex_ai/mistral-medium-3",
    "mistral-small": "vertex_ai/mistral-small-2503",
    "qwen-3-235b-a22b-instruct": "vertex_ai/qwen/qwen3-235b-a22b-instruct-2507-maas",
    "deepseek-v3.1": "vertex_ai/deepseek-ai/deepseek-v3.1-maas",
    "deepseek-r1": "vertex_ai/deepseek-ai/deepseek-r1-0528-maas",
    "gpt-oss-20b": "vertex_ai/openai/gpt-oss-20b-maas",
    "gpt-oss-120b": "vertex_ai/openai/gpt-oss-120b-maas",
}

register_model_alias_map("vertex-ai", models)
