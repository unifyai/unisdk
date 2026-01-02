"""Unify python module."""

import os
from typing import Optional, Union


if "UNIFY_BASE_URL" in os.environ.keys():
    BASE_URL = os.environ["UNIFY_BASE_URL"]
else:
    BASE_URL = "https://api.unify.ai/v0"


UNIFY_DIR = os.path.dirname(__file__)


# Platform API utilities
from .platform.queries import log_query
from .platform.user import get_user_basic_info

# Logging utilities
from .logging.utils import compositions
from .logging.utils import contexts
from .logging.utils import datasets
from .logging.utils import logs
from .logging.utils import projects

from .logging.utils.compositions import *
from .logging.utils.contexts import *
from .logging.utils.datasets import *
from .logging.utils.logs import *
from .logging.utils.projects import *

# Utils
from .utils import helpers, map, get_map_mode, set_map_mode, _caching, storage
from .utils._caching import (
    set_caching,
    set_cache_backend,
    cache_file_union,
    cache_file_intersection,
    subtract_cache_files,
    cached,
)
from .utils.storage import get_signed_url, download_object, get_object_info
from .utils.caching import (
    get_cache_stats,
    reset_cache_stats,
    CacheStats,
)
from .utils import http
from .utils.http import RequestError

# Logging
from .logging import dataset, logs
from .logging.dataset import *
from .logging.logs import *

# Assistants
from .assistants.management import *


# Project #
# --------#

PROJECT: Optional[str] = None


# noinspection PyShadowingNames
def activate(
    project: str,
    overwrite: Union[bool, str] = False,
    api_key: str = None,
) -> None:
    if project not in list_projects(api_key=api_key):
        create_project(project, api_key=api_key)
    elif overwrite:
        create_project(project, api_key=api_key, overwrite=overwrite)
    global PROJECT
    PROJECT = project


def deactivate() -> None:
    global PROJECT
    PROJECT = None


def active_project() -> str:
    global PROJECT
    if PROJECT is None:
        return os.environ.get("UNIFY_PROJECT")
    return PROJECT


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
        if self._project not in list_projects(api_key=self._api_key) or self._overwrite:
            self.create()
        self._entered = True

    def __exit__(self, exc_type, exc_val, exc_tb):
        deactivate()
        self._entered = False
