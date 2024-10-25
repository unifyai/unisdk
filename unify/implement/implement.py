import inspect
import traceback
import importlib
import os.path
from typing import Optional

import unify
from .system_messages import (
    CODING_SYS_MESSAGE_BASE,
    INIT_CODING_SYS_MESSAGE,
    UPDATING_CODING_SYS_MESSAGE,
    DOCSTRING_SYS_MESSAGE_HEAD,
    DOCSTRING_SYS_MESSAGE_FIRST_CONTEXT,
    DOCSTRING_SYS_MESSAGE_EXTRA_CONTEXT,
    DOCSTRING_SYS_MESSAGE_TAIL,
)

MODEL = "gpt-4o@openai"


IMPLEMENTATIONS = dict()
MODULE_PATH = "implementations.py"

INTERACTIVE = False


def set_interactive():
    global INTERACTIVE
    INTERACTIVE = True


def set_non_interactive():
    global INTERACTIVE
    INTERACTIVE = False


def interactive_mode():
    global INTERACTIVE
    return INTERACTIVE


class Interactive:

    def __enter__(self):
        set_interactive()

    def __exit__(self, exc_type, exc_val, exc_tb):
        set_non_interactive()


def implement(fn: callable, module_path: Optional[str] = None):

    global MODULE_PATH
    if module_path is None:
        module_path = MODULE_PATH
        full_module_path = os.path.join(os.getcwd(), MODULE_PATH)

    def _load_module(module_name: str):
        while True:
            try:
                return importlib.reload(
                    importlib.import_module(module_name),
                )
            except Exception as e:
                print("Error loading module", e)
                input(
                    f"Open file {full_module_path} and fix any issues, "
                    f"then press enter once you're done.",
                )

    global IMPLEMENTATIONS
    module = _load_module(module_path.rstrip(".py"))
    for name, obj in inspect.getmembers(module):
        if callable(obj):
            IMPLEMENTATIONS[obj.__name__] = obj

    def _populate_dev_system_message(template: str) -> str:
        return (
            template.replace(
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

    def _populate_docstring_context_system_message(
        template: str,
        child_name: str,
        parent_name: str,
        parent_implementation: str,
        calling_line: str,
    ) -> str:
        return (
            template.replace(
                "{child_name}",
                child_name,
            )
            .replace(
                "{parent_name}",
                parent_name,
            )
            .replace(
                "{parent_implementation}",
                parent_implementation,
            )
            .replace(
                "{calling_line}",
                calling_line,
            )
        )

    name = fn.__name__
    docstring = fn.__doc__
    signature = str(inspect.signature(fn))
    client = unify.Unify(MODEL, cache=True)
    docstring_client = unify.Unify(MODEL, cache=True)
    first_line = f"def {name}{signature}:"
    init_system_message = _populate_dev_system_message(INIT_CODING_SYS_MESSAGE)
    update_system_message = _populate_dev_system_message(UPDATING_CODING_SYS_MESSAGE)
    system_message_base = _populate_dev_system_message(CODING_SYS_MESSAGE_BASE)
    init_system_message += system_message_base
    update_system_message += system_message_base
    client.set_system_message(init_system_message)
    client.set_stateful(True)

    def _get_imports(response):
        top_half = response.split(first_line)[0].rstrip("\n")
        lines = top_half.split("\n")
        imports = list()

        for line in reversed(lines):
            if not line.startswith("import ") and not line.startswith("from "):
                break
            imports.append(line)
        return "\n".join(reversed(imports))

    def _get_src_code(response, fn_name):
        lines = response.split("\n")
        starting_line = [f"def {fn_name}(" in ln for ln in lines].index(True)
        valid_lines = lines[starting_line : starting_line + 1]
        for line in lines[starting_line + 1 :]:
            line_len = len(line)
            if (line_len > 4 and line[0:4] != "    ") or (
                line_len <= 4 and line.strip(" ").strip("\n") != ""
            ):
                break
            valid_lines.append(line)
        return "\n".join(valid_lines) + "\n"

    def _generate_code():
        response = client.generate(
            f"please implement the function {name} based on the prior chat history, "
            f"and also strictly following the instructions in the original "
            f"system message:",
        )
        assert (
            first_line in response,
            "Model failed to follow the formatting instructions.",
        )
        return _get_imports(response), _get_src_code(response, name), response

    def _generate_function_spec(fn_name):
        response = docstring_client.generate(
            f"please implement the function definition for {fn_name} as described in "
            "the format described in the system message.",
        )
        return _get_src_code(response, fn_name), response

    def _load_function(fn_name: str):
        while True:
            try:
                return getattr(
                    _load_module(module_path.rstrip(".py")),
                    fn_name,
                )
            except Exception as e:
                print(
                    "Loaded module without errors, "
                    "but there was an error trying to load function",
                    e,
                )
                input(
                    f"Open file {full_module_path} and fix any issues, "
                    f"then press enter once you're done.",
                )

    def _write_to_file(*, fn_name, imports="", implementation=""):
        if not os.path.exists(full_module_path):
            with open(full_module_path, "w+") as file:
                if imports != "":
                    file.write(imports + "\n\n\n")
                file.write(implementation)
            return
        with open(full_module_path, "r") as file:
            content = file.read()
        if f"def {fn_name}" not in content:
            new_content = imports + content + implementation
            with open(full_module_path, "w") as file:
                file.write(new_content)
            return
        fn_implemented = _load_function(fn_name)
        src_code = inspect.getsource(fn_implemented)
        loaded_imports = _get_imports(content)
        new_content = content.replace(src_code, implementation).replace(
            loaded_imports,
            imports,
        )
        with open(full_module_path, "w") as file:
            file.write(new_content)

    def _get_fn():
        global IMPLEMENTATIONS
        if name in IMPLEMENTATIONS:
            return IMPLEMENTATIONS[name]
        imports, implementation, llm_response = _generate_code()
        client.set_system_message(update_system_message)
        _write_to_file(fn_name=name, imports=imports, implementation=implementation)
        if interactive_mode():
            while True:
                assistant_msg = (
                    "\nIs there anything you would like me to change?\n"
                    "If so, then please respond in one of the two formats:\n"
                    '"Yes: {your explanation}"\n'
                    '"No: {your explanation}"\n\n'
                    "If you would like to make updates yourself, then you can directly "
                    f"modify the source code in {full_module_path}.\n"
                    'Simply respond with the word "Reload" once '
                    "you've made the changes, and then I can take another look.\n\n"
                )
                print(llm_response)
                response = input(assistant_msg).strip("'").strip('"')
                if response[0:2].lower() == "no":
                    break
                elif response[0:6].lower() == "reload":
                    client.append_messages(
                        [
                            {"role": "assistant", "content": assistant_msg},
                            {"role": "user", "content": response + ""},
                        ],
                    )
                    continue
                elif response[0:3].lower() != "yes":
                    print(
                        "Please respond in one of the following formats:\n"
                        "Yes: {your explanation}\n"
                        "No: {your explanation}",
                    )
                    continue
                client.append_messages(
                    [
                        {"role": "assistant", "content": assistant_msg},
                        {"role": "user", "content": response},
                    ],
                )
                imports, implementation, llm_response = _generate_code()
                _write_to_file(
                    fn_name=name,
                    imports=imports,
                    implementation=implementation,
                )
        fn_implemented = _load_function(name)
        IMPLEMENTATIONS[name] = fn_implemented
        return fn_implemented

    def _add_new_function_spec_w_implement_decorator(name_error, tracebk):
        # ToDo: make this process interactive
        system_message = DOCSTRING_SYS_MESSAGE_HEAD.replace("{name}", name_error.name)
        context = list()
        first_context = True
        parent_name = None
        for line in reversed(tracebk.split("\n")):
            if not line or line[0] != " ":
                continue
            context.append(line)
            if line[0:8] == '  File "':
                if first_context:
                    parent_name = context[1].split(",")[-1].split(" ")[-1]
                    system_message += _populate_docstring_context_system_message(
                        DOCSTRING_SYS_MESSAGE_FIRST_CONTEXT,
                        child_name=name_error.name,
                        parent_name=parent_name,
                        parent_implementation=inspect.getsource(
                            _load_function(parent_name),
                        ),
                        calling_line=context[0].lstrip(" "),
                    )
                    first_context = False
                else:
                    child_name = parent_name
                    parent_name = context[1].split(",")[-1].split(" ")[-1]
                    system_message += _populate_docstring_context_system_message(
                        DOCSTRING_SYS_MESSAGE_EXTRA_CONTEXT,
                        child_name=child_name,
                        parent_name=parent_name,
                        parent_implementation=inspect.getsource(
                            _load_function(parent_name),
                        ),
                        calling_line=context[0].lstrip(" "),
                    )
                context.clear()
                if parent_name == name:
                    break

        system_message += DOCSTRING_SYS_MESSAGE_TAIL.replace("{name}", name_error.name)
        docstring_client.set_system_message(system_message)
        function_spec, llm_response = _generate_function_spec(name_error.name)
        function_spec = "\n\n@unify.implement\n" + function_spec
        _write_to_file(fn_name=name_error.name, implementation=function_spec)

    def _execute_with_implement(func: callable, *args, **kwargs):
        try:
            return func(*args, **kwargs)
        except NameError as ne:
            _add_new_function_spec_w_implement_decorator(ne, traceback.format_exc())
        return func(*args, **kwargs)

    def implemented(*args, **kwargs):
        return _execute_with_implement(_get_fn(), *args, **kwargs)

    return implemented
