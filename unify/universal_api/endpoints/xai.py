from .utils import register_model_alias_map

models = {
    "grok-4.1-fast-reasoning": "xai/grok-4.1-fast-reasoning",
    "grok-4.1-fast-non-reasoning": "xai/grok-4.1-fast-non-reasoning",
    "grok-code-fast": "xai/grok-code-fast-1",
    "grok-4-fast-reasoning": "xai/grok-4-fast-reasoning",
    "grok-4-fast-non-reasoning": "xai/grok-4-fast-non-reasoning",
    "grok-4": "xai/grok-4",
    "grok-3": "xai/grok-3",
    "grok-3-mini": "xai/grok-3-mini",
}

register_model_alias_map("xai", models)
