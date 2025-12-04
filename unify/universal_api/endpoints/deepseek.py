from .utils import register_model_alias_map

models = {
    "deepseek-v3": "deepseek/deepseek-chat",
    "deepseek-r1": "deepseek/deepseek-reasoner",
}

register_model_alias_map("deepseek", models)
