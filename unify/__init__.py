"""Unify python module."""
from queries import *
from utils import *

_local_api = False  # for development


def base_url():
    if _local_api:
        return "http://127.0.0.1:8000/v0"
    return "https://api.unify.ai/v0"



