import unify

# Helpers


def _is_custom_endpoint(endpoint: str):
    _, provider = endpoint.split("@")
    return "custom" in provider


def _is_local_endpoint(endpoint: str):
    _, provider = endpoint.split("@")
    return provider == "local"


def _is_fallback_provider(provider: str, api_key: str = None):
    public_providers = unify.list_providers(api_key=api_key)
    return all(p in public_providers for p in provider.split("->"))


def _is_fallback_model(model: str, api_key: str = None):
    public_models = unify.list_models(api_key=api_key)
    return all(p in public_models for p in model.split("->"))


def _is_fallback_endpoint(endpoint: str, api_key: str = None):
    public_endpoints = unify.list_endpoints(api_key=api_key)
    return all(e in public_endpoints for e in endpoint.split("->"))


def _is_meta_provider(provider: str, api_key: str = None):
    public_providers = unify.list_providers(api_key=api_key)
    if "skip_providers:" in provider:
        skip_provs = provider.split("skip_providers:")[-1].split("|")[0]
        for prov in skip_provs.split(","):
            if prov.strip() not in public_providers:
                return False
        chnk0, chnk1 = provider.split("skip_providers:")
        chnk2 = "|".join(chnk1.split("|")[1:])
        provider = "".join([chnk0, chnk2])
    if "providers:" in provider:
        provs = provider.split("providers:")[-1].split("|")[0]
        for prov in provs.split(","):
            if prov.strip() not in public_providers:
                return False
        chnk0, chnk1 = provider.split("providers:")
        chnk2 = "|".join(chnk1.split("|")[1:])
        provider = "".join([chnk0, chnk2])
        if provider[-1] == "|":
            provider = provider[:-1]
    public_models = unify.list_models(api_key=api_key)
    if "skip_models:" in provider:
        skip_mods = provider.split("skip_models:")[-1].split("|")[0]
        for md in skip_mods.split(","):
            if md.strip() not in public_models:
                return False
        chnk0, chnk1 = provider.split("skip_models:")
        chnk2 = "|".join(chnk1.split("|")[1:])
        provider = "".join([chnk0, chnk2])
    if "models:" in provider:
        mods = provider.split("models:")[-1].split("|")[0]
        for md in mods.split(","):
            if md.strip() not in public_models:
                return False
        chnk0, chnk1 = provider.split("models:")
        chnk2 = "|".join(chnk1.split("|")[1:])
        provider = "".join([chnk0, chnk2])
    meta_providers = (
        (
            "highest-quality",
            "lowest-time-to-first-token",
            "lowest-inter-token-latency",
            "lowest-input-cost",
            "lowest-output-cost",
            "lowest-cost",
            "lowest-ttft",
            "lowest-itl",
            "lowest-ic",
            "lowest-oc",
            "highest-q",
            "lowest-t",
            "lowest-i",
            "lowest-c",
        )
        + (
            "quality",
            "time-to-first-token",
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
    operators = ("<", ">", "=", "|", ".", ":")
    for s in meta_providers + operators:
        provider = provider.replace(s, "")
    return all(c.isnumeric() for c in provider)


# Checks


def _is_valid_endpoint(endpoint: str, api_key: str = None):
    if endpoint == "user-input":
        return True
    if _is_fallback_endpoint(endpoint, api_key):
        return True
    model, provider = endpoint.split("@")
    if _is_valid_provider(provider) and _is_valid_model(model):
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
    if _is_fallback_provider(provider):
        return True
    if provider == "local" or "custom" in provider:
        return True
    return False


def _is_valid_model(model: str, custom_or_local: bool = False, api_key: str = None):
    if custom_or_local:
        return True
    if model in unify.list_models(api_key=api_key):
        return True
    if _is_fallback_model(model):
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
