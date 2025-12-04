from .utils import register_model_alias_map

models = {
    "gpt-3.5-turbo": "gpt-3.5-turbo",
    "gpt-4": "gpt-4",
    "gpt-4-turbo": "gpt-4-turbo",
    "gpt-4o": "gpt-4o",
    "gpt-4o-2024-05-13": "gpt-4o-2024-05-13",
    "gpt-4o-mini": "gpt-4o-mini",
    "chatgpt-4o-latest": "chatgpt-4o-latest",
    "o1": "o1",
    "o3-mini": "o3-mini",
    "gpt-4o-search-preview": "gpt-4o-search-preview",
    "gpt-4o-mini-search-preview": "gpt-4o-mini-search-preview",
    "gpt-4.1": "gpt-4.1",
    "gpt-4.1-mini": "gpt-4.1-mini",
    "gpt-4.1-nano": "gpt-4.1-nano",
    "o3": "o3",
    "o4-mini": "o4-mini",
    "gpt-5": "gpt-5",
    "gpt-5-mini": "gpt-5-mini",
    "gpt-5-nano": "gpt-5-nano",
    "gpt-5-chat-latest": "gpt-5-chat-latest",
    "gpt-5.1": "gpt-5.1",
    "gpt-5.1-chat-latest": "gpt-5.1-chat-latest",
}

register_model_alias_map("openai", models)
