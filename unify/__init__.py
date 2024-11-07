"""Unify python module."""

import os
from typing import Callable, Optional


if "UNIFY_BASE_URL" in os.environ.keys():
    BASE_URL = os.environ["UNIFY_BASE_URL"]
else:
    BASE_URL = "https://api.unify.ai/v0"


CLIENT_LOGGING = False
LOCAL_MODELS = dict()
SEED = None


def set_seed(seed: int) -> None:
    global SEED
    SEED = seed


def get_seed() -> Optional[int]:
    return SEED


def register_local_model(model_name: str, fn: Callable):
    if "@local" not in model_name:
        model_name += "@local"
    LOCAL_MODELS[model_name] = fn


from .universal_api.utils import (
    credits,
    custom_api_keys,
    custom_endpoints,
    endpoint_metrics,
    queries,
    supported_endpoints,
)
from .universal_api.utils.credits import *
from .universal_api.utils.custom_api_keys import *
from .universal_api.utils.custom_endpoints import *
from .universal_api.utils.endpoint_metrics import *
from .universal_api.utils.queries import *
from .universal_api.utils.supported_endpoints import *

from .evals.utils import artifacts
from .evals.utils import compositions
from .evals.utils import datasets
from .evals.utils import logging
from .evals.utils import projects

from .evals.utils.artifacts import *
from .evals.utils.compositions import *
from .evals.utils.datasets import *
from .evals.utils.logging import *
from .evals.utils.projects import *

from .utils import helpers, map, _caching
from .utils._caching import set_caching, set_caching_fname

from .universal_api import chatbot, clients, logging
from .universal_api.clients import multi_llm
from .universal_api.chatbot import *
from unify.universal_api.clients.uni_llm import *
from unify.universal_api.clients.multi_llm import *

from .universal_api import casting, types
from .evals import dataset, logging

from .universal_api.casting import *
from .universal_api.logging import *
from .universal_api.types import *

from .evals.dataset import *
from .evals.logging import *


# Project #
# --------#

PROJECT: Optional[str] = None


# noinspection PyShadowingNames
def activate(project: str, overwrite: bool = False, api_key: str = None) -> None:
    if project not in list_projects(api_key=api_key):
        create_project(project, api_key=api_key)
    elif overwrite:
        delete_project(project, api_key=api_key)
        create_project(project, api_key=api_key)
    global PROJECT
    PROJECT = project


def deactivate() -> None:
    global PROJECT
    PROJECT = None


def __getattr__(name):
    if name == "active_project":
        global PROJECT
        return PROJECT
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


class Project:

    # noinspection PyShadowingNames
    def __init__(
        self,
        project: str,
        overwrite: bool = False,
        api_key: Optional[str] = None,
    ) -> None:
        self._project = project
        self._overwrite = overwrite
        # noinspection PyProtectedMember
        self._api_key = helpers._validate_api_key(api_key)
        self._entered = False

    def create(self) -> None:
        create_project(self._project, overwrite=self._overwrite, api_key=self._api_key)

    def delete(self):
        delete_project(self._project, api_key=self._api_key)

    def rename(self, new_name: str):
        rename_project(self._project, new_name, api_key=self._api_key)
        self._project = new_name
        if self._entered:
            activate(self._project)

    def __enter__(self):
        activate(self._project)
        if self._project not in list_projects(api_key=self._api_key):
            self.create()
        self._entered = True

    def __exit__(self, exc_type, exc_val, exc_tb):
        deactivate()
        self._entered = False
