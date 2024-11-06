import unify


# Helpers


def _is_custom_endpoint(endpoint: str):
    _, provider = endpoint.split("@")
    return "custom" in provider


def _is_local_endpoint(endpoint: str):
    _, provider = endpoint.split("@")
    return provider == "local"


def _is_meta_provider(provider: str):
    meta_providers = (
        (
            "highest-quality",
            "highest-q",
            "lowest-time-to-first-token",
            "lowest-ttft",
            "lowest-t",
            "lowest-inter-token-latency",
            "lowest-itl",
            "lowest-i",
            "lowest-cost",
            "lowest-c",
            "lowest-input-cost",
            "lowest-ic",
            "lowest-output-cost",
            "lowest-oc",
        )
        + (
            "quality" "time-to-first-token",
            "inter-token-latency",
            "input-cost",
            "output-cost",
            "cost",
        )
        + (
            "q",
            "ttft",
            "itl",
            "ic",
            "oc",
            "t",
            "i",
            "c",
        )
    )
    operators = ("<", ">", "=", "|", ".")
    for s in meta_providers + operators:
        provider = provider.replace(s, "")
    return all(c.isnumeric() for c in provider)


# Checks


def _is_valid_endpoint(endpoint: str, api_key: str = None):
    model, provider = endpoint.split("@")
    if _is_meta_provider(provider) and _is_valid_model(model):
        return True
    if endpoint in unify.list_endpoints(api_key=api_key):
        return True
    if _is_custom_endpoint(endpoint) or _is_local_endpoint(endpoint):
        return True
    return False


def _is_valid_provider(provider: str, api_key: str = None):
    if _is_meta_provider(provider):
        return True
    if provider in unify.list_providers(api_key=api_key):
        return True
    if provider == "local" or "custom" in provider:
        return True
    return False


def _is_valid_model(model: str, custom_or_local: bool = False, api_key: str = None):
    if custom_or_local:
        return True
    if model in unify.list_models(api_key=api_key):
        return True
    if model == "router":
        return True
    return False


# Assertions


def _assert_is_valid_endpoint(endpoint: str, api_key: str = None):
    assert _is_valid_endpoint(endpoint, api_key), f"{endpoint} is not a valid endpoint"


def _assert_is_valid_provider(provider: str, api_key: str = None):
    assert _is_valid_provider(provider, api_key), f"{provider} is not a valid provider"


def _assert_is_valid_model(
    model: str,
    custom_or_local: bool = False,
    api_key: str = None,
):
    assert _is_valid_model(
        model,
        custom_or_local,
        api_key,
    ), f"{model} is not a valid model"
