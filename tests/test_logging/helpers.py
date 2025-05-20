import asyncio
import functools
import sys
import traceback

import unify


def _handle_project(test_fn):
    # noinspection PyBroadException
    @functools.wraps(test_fn)
    def wrapper(*args, **kwargs):
        project = test_fn.__name__
        if project in unify.list_projects():
            unify.delete_project(project)
        try:
            with unify.Project(project):
                test_fn(*args, **kwargs)
            unify.delete_project(project)
        except:
            unify.delete_project(project)
            exc_type, exc_value, exc_tb = sys.exc_info()
            tb_string = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
            raise Exception(f"{tb_string}")

    @functools.wraps(test_fn)
    async def async_wrapper(*args, **kwargs):
        project = test_fn.__name__
        if project in unify.list_projects():
            unify.delete_project(project)
        try:
            with unify.Project(project):
                await test_fn(*args, **kwargs)
            unify.delete_project(project)
        except:
            unify.delete_project(project)
            exc_type, exc_value, exc_tb = sys.exc_info()
            tb_string = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
            raise Exception(f"{tb_string}")

    return async_wrapper if asyncio.iscoroutinefunction(test_fn) else wrapper
