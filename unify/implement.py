import inspect
import importlib
import os.path

import unify

MODEL = "gpt-4o@openai"
CODING_SYS_MESSAGE_BASE = """
    You are encouraged to make use of imaginary functions whenever you don't have enough
    context to solve the task fully, or if you believe a modular solution would be best.
    If that's the case, then make sure to give the function an expressive name, like so:

    companies = get_all_companies_from_crm()
    large_companies = filter_companies_based_on_headcount(
        companies, headcount=100, greater_than=True
    )

    Please DO NOT implement any inner functions. Just assume they exist, and make calls
    to them like the examples above.

    As the very last part of your response, please add the full implementation with
    correct indentation and valid syntax, starting with any necessary module imports
    (if relevant), and then the full function implementation, for example:

    import {some_module}
    from {another_module} import {function}

    def {name}{signature}:
        {implementation}
"""
INIT_CODING_SYS_MESSAGE = """
    You should write a Python implementation for a function {name} with the
    following signature and docstring:

    {signature}

    {docstring}

    """
UPDATING_CODING_SYS_MESSAGE = """
    You should *update* the Python implementation (preserving the function name,
    arguments, and general structure), and only make changes as requested by the user
    in the chat.

"""

IMPLEMENTATIONS = dict()
IMPLEMENTATION_PATH = "implementations.py"

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


def implement(fn: callable):

    global IMPLEMENTATIONS
    module = importlib.reload(
        importlib.import_module(IMPLEMENTATION_PATH.rstrip(".py")),
    )
    for name, obj in inspect.getmembers(module):
        if callable(obj):
            IMPLEMENTATIONS[obj.__name__] = obj

    def _populate_system_message(template: str):
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

    name = fn.__name__
    docstring = fn.__doc__
    signature = str(inspect.signature(fn))
    client = unify.Unify(MODEL, cache=True)
    first_line = f"def {name}{signature}:"
    init_system_message = _populate_system_message(INIT_CODING_SYS_MESSAGE)
    update_system_message = _populate_system_message(UPDATING_CODING_SYS_MESSAGE)
    system_message_base = _populate_system_message(CODING_SYS_MESSAGE_BASE)
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

    def _get_src_code(response):
        implementation = first_line + response.split(first_line)[-1]
        lines = implementation.split("\n")
        valid_lines = [lines.pop(0)]
        for line in lines:
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
        return _get_imports(response), _get_src_code(response), response

    def _load_function():
        while True:
            try:
                return getattr(
                    importlib.reload(
                        importlib.import_module(IMPLEMENTATION_PATH.rstrip(".py")),
                    ),
                    name,
                )
            except Exception as e:
                print("Error loading function", e)
                input(
                    f"Open file {IMPLEMENTATION_PATH} and fix any issues, "
                    f"then press enter once you're done.",
                )

    def _write_to_file(imports, implementation):
        if not os.path.exists(IMPLEMENTATION_PATH):
            with open(IMPLEMENTATION_PATH, "w+") as file:
                if imports != "":
                    file.write(imports + "\n\n\n")
                file.write(implementation)
            return
        with open(IMPLEMENTATION_PATH, "r") as file:
            content = file.read()
        if first_line not in content:
            new_content = imports + content + implementation
            with open(IMPLEMENTATION_PATH, "w") as file:
                file.write(new_content)
            return
        fn_implemented = _load_function()
        src_code = inspect.getsource(fn_implemented)
        loaded_imports = _get_imports(content)
        new_content = content.replace(src_code, implementation).replace(
            loaded_imports,
            imports,
        )
        with open(IMPLEMENTATION_PATH, "w") as file:
            file.write(new_content)

    def _get_fn():
        global IMPLEMENTATIONS
        if name in IMPLEMENTATIONS:
            return IMPLEMENTATIONS[name]
        imports, implementation, llm_response = _generate_code()
        client.set_system_message(update_system_message)
        _write_to_file(imports, implementation)
        if interactive_mode():
            while True:
                assistant_msg = (
                    "\nIs there anything you would like me to change?\n"
                    "If so, then please respond in one of the two formats:\n"
                    '"Yes: {your explanation}"\n'
                    '"No: {your explanation}"\n\n'
                    "If you would like to make updates yourself, then you can directly "
                    f"modify the source code in {IMPLEMENTATION_PATH}.\n"
                    'Simply respond with the word "Reload" once '
                    "you've made the changes, and then I can take another look.\n\n"
                )
                print(llm_response)
                response = input(assistant_msg).strip("'").strip('"')
                if response[0:2].lower() == "no":
                    break
                elif response[0:6].lower() == "reload":
                    implementation = inspect.getsource(_load_function())
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
                _write_to_file(imports, implementation)
        fn_implemented = _load_function()
        IMPLEMENTATIONS[name] = fn_implemented
        return fn_implemented

    def implemented(*args, **kwargs):
        return _get_fn()(*args, **kwargs)

    return implemented
