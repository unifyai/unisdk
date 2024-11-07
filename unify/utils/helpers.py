import json
import os
import threading
from typing import Any, Dict, List, Optional, Union

import unify
import requests
from pydantic import BaseModel, ValidationError

PROJECT_LOCK = threading.Lock()


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


def _get_and_maybe_create_project(
    project: Optional[str] = None,
    required: bool = True,
    api_key: Optional[str] = None,
) -> Optional[str]:
    api_key = _validate_api_key(api_key)
    if project is None:
        project = unify.active_project
        if project is None:
            if required:
                raise Exception(
                    "No project specified in the arguments, and no globally set "
                    "project either, with required=True was passed. A project must be "
                    "passed in the argument, or set globally via "
                    "unify.activate('project_name')",
                )
            return None
    PROJECT_LOCK.acquire()
    if project not in unify.list_projects(api_key=api_key):
        unify.create_project(project, api_key=api_key)
    PROJECT_LOCK.release()
    return project


def _prune_dict(val):

    def keep(v):
        if v is None:
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
