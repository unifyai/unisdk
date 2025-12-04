from .utils import register_model_alias_map

models = {
    "mistral-large": "mistral/mistral-large-latest",
    "mistral-medium": "mistral/mistral-medium-latest",
    "mistral-small": "mistral/mistral-small-latest",
}

register_model_alias_map("mistral", models)
