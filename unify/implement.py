import inspect
import importlib

import unify

MODEL = "claude-3.5-sonnet@anthropic"
SYS_MESSAGE = """
    You should implement a Python implementation for a function {name} with the
    following signature and docstring:

    {signature}

    {docstring}

    As the very last part of your response, please add the full implementation with
    correct indentation and valid syntax, starting with:

    def {name}{signature}:
    """

IMPLEMENTATIONS = dict()
IMPLEMENTATION_PATH = "implementations.py"


def implement(fn: callable):

    def _get_fn():
        global IMPLEMENTATIONS
        name = fn.__name__
        docstring = fn.__doc__
        signature = str(inspect.signature(fn))
        if name in IMPLEMENTATIONS:
            return IMPLEMENTATIONS[name]
        system_message = (
            SYS_MESSAGE.replace(
                "{name}",
                name,
            )
            .replace(
                "{docstring}",
                docstring,
            )
            .replace(
                "{signature}",
                signature,
            )
        )
        implementation = unify.Unify(MODEL).generate(
            f"please implement the function {name}",
            system_message=system_message,
        )
        first_line = f"def {name}{signature}:"
        assert (
            first_line in implementation,
            "Model failed to follow the formatting instructions.",
        )
        implementation = first_line + implementation.split(first_line)[-1]
        lines = implementation.split("\n")
        while True:
            if len(lines[-1]) < 4 or lines[-1][0:4] != "    ":
                lines = lines[:-1]
            else:
                break
        implementation = "\n".join(lines) + "\n"
        with open(IMPLEMENTATION_PATH, "w+") as file:
            file.write(implementation)
        fn_implemented = getattr(importlib.import_module("implementations"), name)
        IMPLEMENTATIONS[name] = fn_implemented
        return fn_implemented

    def implemented(*args, **kwargs):
        return _get_fn()(*args, **kwargs)

    return implemented
