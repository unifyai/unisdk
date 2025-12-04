from .utils import register_model_alias_map

models = {
    "gpt-oss-20b": "bedrock/us.openai.gpt-oss-20b-1:0",
    "gpt-oss-120b": "bedrock/us.openai.gpt-oss-120b-1:0",
    "deepseek-r1": "bedrock/us.deepseek.r1-v1:0",
    "llama-3.3-70b-chat": "bedrock/us.meta.llama3-3-70b-instruct-v1:0",
    "llama-3.2-1b-chat": "bedrock/us.meta.llama3-2-1b-instruct-v1:0",
    "llama-3.2-3b-chat": "bedrock/us.meta.llama3-2-3b-instruct-v1:0",
    "llama-3.1-8b-chat": "bedrock/meta.llama3-1-8b-instruct-v1:0",
    "llama-3.1-70b-chat": "bedrock/meta.llama3-1-70b-instruct-v1:0",
    "llama-3.1-405b-chat": "bedrock/meta.llama3-1-405b-instruct-v1:0",
    "llama-3-8b-chat": "bedrock/meta.llama3-8b-instruct-v1:0",
    "llama-3-70b-chat": "bedrock/meta.llama3-70b-instruct-v1:0",
    "claude-3-haiku": "bedrock/us.anthropic.claude-3-haiku-20240307-v1:0",
    "claude-3.5-haiku": "bedrock/us.anthropic.claude-3-5-haiku-20241022-v1:0",
    "claude-4-sonnet": "bedrock/us.anthropic.claude-sonnet-4-20250514-v1:0",
    "claude-4-opus": "bedrock/us.anthropic.claude-opus-4-20250514-v1:0",
    "claude-4.1-opus": "bedrock/us.anthropic.claude-opus-4-1-20250805-v1:0",
    "claude-4.5-sonnet": "bedrock/us.anthropic.claude-sonnet-4-5-20250929-v1:0",
    "claude-4.5-opus": "bedrock/us.anthropic.claude-opus-4-5-20251101-v1:0",
}

register_model_alias_map("bedrock", models)
