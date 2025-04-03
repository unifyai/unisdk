import inspect
import json
import os
import threading
from typing import Any, Dict, List, Optional, Tuple, Union

import openai
import requests
import unify
from pydantic import BaseModel, ValidationError

PROJECT_LOCK = threading.Lock()


class RequestError(Exception):
    def __init__(self, response: requests.Response):
        req = response.request
        message = (
            f"{req.method} {req.url} failed with status code {response.status_code}. "
            f"Request body: {req.body}, Response: {response.text}"
        )
        super().__init__(message)
        self.response = response


def _check_response(response: requests.Response):
    if not response.ok:
        raise RequestError(response)


def _res_to_list(response: requests.Response) -> Union[List, Dict]:
    return json.loads(response.text)


def _validate_api_key(api_key: Optional[str]) -> str:
    if api_key is None:
        api_key = os.environ.get("UNIFY_KEY")
    if api_key is None:
        raise KeyError(
            "UNIFY_KEY is missing. Please make sure it is set correctly!",
        )
    return api_key


def _default(value: Any, default_value: Any) -> Any:
    return value if value is not None else default_value


def _dict_aligns_with_pydantic(dict_in: Dict, pydantic_cls: type(BaseModel)) -> bool:
    try:
        pydantic_cls.model_validate(dict_in)
        return True
    except ValidationError:
        return False


def _make_json_serializable(
    item: Union[Dict, List, Tuple],
) -> Union[Dict, List, Tuple]:
    if isinstance(item, list):
        return [_make_json_serializable(i) for i in item]
    elif isinstance(item, dict):
        return {k: _make_json_serializable(v) for k, v in item.items()}
    elif isinstance(item, tuple):
        return tuple(_make_json_serializable(i) for i in item)
    elif inspect.isclass(item) and issubclass(item, BaseModel):
        return item.schema()
    elif isinstance(item, BaseModel):
        return item.dict()
    elif hasattr(item, "json") and callable(item.json):
        return _make_json_serializable(item.json())
    else:
        return item


def _get_and_maybe_create_project(
    project: Optional[str] = None,
    required: bool = True,
    api_key: Optional[str] = None,
    create_if_missing: bool = True,
) -> Optional[str]:
    # noinspection PyUnresolvedReferences
    from unify.logging.utils.logs import ASYNC_LOGGING

    api_key = _validate_api_key(api_key)
    if project is None:
        project = unify.active_project()
        if project is None:
            if required:
                project = "_"
            else:
                return None
    if not create_if_missing:
        return project
    if ASYNC_LOGGING:
        # acquiring the project lock here will block the async logger
        # so we skip the lock if we are in async mode
        return project
    with PROJECT_LOCK:
        if project not in unify.list_projects(api_key=api_key):
            unify.create_project(project, api_key=api_key)
    return project


def _prune_dict(val):
    def keep(v):
        if v in (None, openai.NotGiven, openai.NOT_GIVEN):
            return False
        else:
            ret = _prune_dict(v)
            if isinstance(ret, dict) or isinstance(ret, list) or isinstance(ret, tuple):
                return bool(ret)
            return True

    if (
        not isinstance(val, dict)
        and not isinstance(val, list)
        and not isinstance(val, tuple)
    ):
        return val
    elif isinstance(val, dict):
        return {k: _prune_dict(v) for k, v in val.items() if keep(v)}
    elif isinstance(val, list):
        return [_prune_dict(v) for i, v in enumerate(val) if keep(v)]
    else:
        return tuple(_prune_dict(v) for i, v in enumerate(val) if keep(v))
