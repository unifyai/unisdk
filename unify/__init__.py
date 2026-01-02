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
from .logging.utils import contexts
from .logging.utils import logs
from .logging.utils import projects

from .logging.utils.contexts import *
from .logging.utils.logs import *
from .logging.utils.projects import *

# Utils
from .utils import helpers, map, _caching, storage
from .utils._caching import set_cache_backend
from .utils.storage import get_signed_url, download_object
from .utils.caching import get_cache_stats
from .utils import http
from .utils.http import RequestError

# Logging
from .logging import logs
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


def active_project() -> str:
    global PROJECT
    if PROJECT is None:
        return os.environ.get("UNIFY_PROJECT")
    return PROJECT
