"""Unify python module."""
import os
from typing import Callable


if "UNIFY_BASE_URL" in os.environ.keys():
    BASE_URL = os.environ["UNIFY_BASE_URL"]
else:
    BASE_URL = "https://api.unify.ai/v0"


LOCAL_MODELS = dict()


def register_local_model(model_name: str, fn: Callable):
    if "@local" not in model_name:
        model_name += "@local"
    LOCAL_MODELS[model_name] = fn


from .utils import (
    credits,
    custom_api_keys,
    custom_endpoints,
    datasets,
    efficiency_benchmarks,
    helpers,
    evaluations,
    queries,
    router_configurations,
    router_deployment,
    router_training,
    supported_endpoints,
)
from .utils.credits import *
from .utils.custom_api_keys import *
from .utils.custom_endpoints import *
from .utils.datasets import *
from .utils.efficiency_benchmarks import *
from .utils.helpers import *
from .utils.evaluations import *
from .utils.queries import *
from .utils.router_configurations import *
from .utils.router_deployment import *
from .utils.router_training import *
from .utils.supported_endpoints import *

from .chat import chatbot, clients, logging
from .chat.clients import multi_llm
from .chat.chatbot import *
from unify.chat.clients.uni_llm import *
from unify.chat.clients.multi_llm import *

from . import (
    agent,
    casting,
    dataset,
    evaluator,
    repr,
    types
)
from .agent import *
from .casting import *
from .dataset import *
from .evaluator import *
from .chat.logging import *
from .repr import *
from .types import *


# Project #
# --------#

PROJECT: Optional[str] = None


# noinspection PyShadowingNames
def activate(project: str) -> None:
    global PROJECT
    PROJECT = project


def deactivate() -> None:
    global PROJECT
    PROJECT = None


def __getattr__(name):
    if name == 'active_project':
        global PROJECT
        return PROJECT
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


class Project:

    # noinspection PyShadowingNames
    def __init__(self, project: str, api_key: Optional[str] = None) -> None:
        self._project = project
        # noinspection PyProtectedMember
        self._api_key = helpers._validate_api_key(api_key)
        self._entered = False

    def create(self):
        create_project(self._project, self._api_key)

    def delete(self):
        delete_project(self._project, self._api_key)

    def rename(self, new_name: str):
        rename_project(self._project, new_name, self._api_key)
        self._project = new_name
        if self._entered:
            activate(self._project)

    def __enter__(self):
        activate(self._project)
        if self._project not in list_projects(self._api_key):
            self.create()
        self._entered = True

    def __exit__(self, exc_type, exc_val, exc_tb):
        deactivate()
        self._entered = False
