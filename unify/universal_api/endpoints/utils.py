from typing import Any, Dict

_MODEL_ALIAS_MAP = {}


def register_model_alias_map(
    provider: str,
    model_map: Dict[str, Any],
) -> Dict[str, str]:
    _MODEL_ALIAS_MAP.update(
        {f"{model}@{provider}": alias for model, alias in model_map.items()},
    )


def get_model_alias(endpoint: str) -> str:
    """
    Get the alias for a model. If the model is not found, return the original model.

    Args:
        endpoint: The endpoint of the model.
    Returns:
        LiteLLM model name for the model.
    """
    return _MODEL_ALIAS_MAP.get(endpoint, endpoint)
