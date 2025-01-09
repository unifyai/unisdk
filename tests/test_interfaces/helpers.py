import functools

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

    return wrapper
