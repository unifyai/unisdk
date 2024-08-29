"""Unify python module."""

LOCAL_API = False  # for development


def base_url():
    if LOCAL_API:
        return "http://127.0.0.1:8000/v0"
    return "https://api.unify.ai/v0"


from unify.chat import ChatBot  # noqa: F403
from unify.clients import AsyncUnify, Unify  # noqa: F403
from unify.multi_llm import MultiLLM, MultiLLMAsync  # noqa: F403
from unify.utils import (
    list_endpoints,
    list_models,
    list_providers,
    upload_dataset_from_file,
    upload_dataset_from_dictionary,
    delete_dataset,
    download_dataset,
    list_datasets,
    evaluate,
    delete_evaluation,
    list_evaluations,
)
