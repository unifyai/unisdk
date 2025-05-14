import importlib
import sys
from typing import Callable, List

import unify


class TraceLoader(importlib.abc.Loader):
    def __init__(self, original_loader, filter: Callable = None):
        self._original_loader = original_loader
        self.filter = filter

    def create_module(self, spec):
        return self._original_loader.create_module(spec)

    def exec_module(self, module):
        self._original_loader.exec_module(module)
        unify.traced(module, filter=self.filter)


class TraceFinder(importlib.abc.MetaPathFinder):
    def __init__(self, targets: List[str], filter: Callable = None):
        self.targets = targets
        self.filter = filter

    def find_spec(self, fullname, path, target=None):
        for target_module in self.targets:
            if not fullname.startswith(target_module):
                return None

        original_sys_meta_path = sys.meta_path[:]
        sys.meta_path = [
            finder for finder in sys.meta_path if not isinstance(finder, TraceFinder)
        ]
        try:
            spec = importlib.util.find_spec(fullname, path)
            if spec is None:
                return None
        finally:
            sys.meta_path = original_sys_meta_path

        if spec.origin is None or not spec.origin.endswith(".py"):
            return None

        spec.loader = TraceLoader(spec.loader, filter=self.filter)
        return spec


def install_tracing_hook(targets: List[str], filter: Callable = None):
    """Install an import hook that wraps imported modules with the traced decorator.

    This function adds a TraceFinder to sys.meta_path that will intercept module imports
    and wrap them with the traced decorator. The hook will only be installed if one
    doesn't already exist.

    Args:
        targets: List of module name prefixes to target for tracing. Only modules
            whose names start with these prefixes will be wrapped.

        filter: A filter function that is passed to the traced decorator.

    """
    if not any(isinstance(finder, TraceFinder) for finder in sys.meta_path):
        sys.meta_path.insert(0, TraceFinder(targets, filter))


def disable_tracing_hook():
    """Remove the tracing import hook from sys.meta_path.

    This function removes any TraceFinder instances from sys.meta_path, effectively
    disabling the tracing functionality for subsequent module imports.

    """
    for finder in sys.meta_path:
        if isinstance(finder, TraceFinder):
            sys.meta_path.remove(finder)
