from .utils import register_model_alias_map

models = {
    "llama-3.1-8b-chat": "groq/llama-3.1-8b-instant",
    "llama-3.3-70b-chat": "groq/llama-3.3-70b-versatile",
    "llama-4-maverick-instruct": "groq/meta-llama/llama-4-maverick-17b-128e-instruct",
    "llama-4-scout-instruct": "groq/meta-llama/llama-4-scout-17b-16e-instruct",
    "gpt-oss-20b": "groq/openai/gpt-oss-20b",
    "gpt-oss-120b": "groq/openai/gpt-oss-120b",
}

register_model_alias_map("groq", models)
