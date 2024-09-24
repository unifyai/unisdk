import argparse
import ast
import importlib
import inspect
import json
import os
import re
import shutil


replace = {
    "<uploaded_by>/<model_name>@<provider_name>": r"\<uploaded_by\>/\<model_name\>@\<provider_name\>",
    "<model_name>@<provider_name>": r"\<model_name\>@\<provider_name\>",
    "# noqa: DAR101.": "",
    "# noqa: DAR201.": "",
    "####": "---\n\n###",
}


class Visitor(ast.NodeVisitor):
    """Check for function and class definitions."""

    def __init__(self):
        self.class_stack = []
        self.function_stack = []
        self.classes = []
        self.functions = []

    def visit_ClassDef(self, node):
        self.class_stack.append(node.name)
        self.classes.append(node.name)
        self.generic_visit(node)
        self.class_stack.pop()

    def visit_FunctionDef(self, node):
        if self.function_stack or self.class_stack:
            return
        self.function_stack.append(node.name)
        self.functions.append(node.name)
        self.generic_visit(node)
        self.function_stack.pop()


def get_all_modules():
    # get all modules in the package
    module_paths = []
    for root, _, files in os.walk("unify"):
        for file in files:
            if "__init__" not in file and file[-3:] == ".py":
                module_paths.append(os.path.join(root, file))
    return module_paths


def get_functions_and_classes(module_paths):
    # ast parse to get functions and classes in each module
    details = dict()
    for module_path in module_paths:
        visitor = Visitor()
        with open(module_path) as f:
            code = f.read()
        tree = ast.parse(code)
        visitor.visit(tree)
        details[module_path] = {
            "class_names": visitor.classes,
            "function_names": visitor.functions,
        }
    return details


def filter_and_import(details):
    # filter and import the public functions and classes in public modules
    private_modules = []
    for module_path in details:
        private_module = False
        module_name = module_path.strip(".py").replace("/", ".")

        # check if there are any private modules
        for namespace in module_name.split("."):
            if namespace.startswith("_"):
                private_module = True
                break

        if private_module:
            private_modules.append(module_path)
            continue

        function_names = details[module_path]["function_names"]
        class_names = details[module_path]["class_names"]

        # import the functions and classes
        functions = {
            function_name: importlib.import_module(module_name).__dict__[function_name]
            for function_name in function_names
            if not function_name.startswith("_")
        }
        classes = {
            class_name: importlib.import_module(module_name).__dict__[class_name]
            for class_name in class_names
            if not class_name.startswith("_")
        }

        details[module_path]["module_name"] = module_name
        details[module_path]["functions"] = functions
        details[module_path]["classes"] = classes

    return details, private_modules


def get_function_signature(source_code):
    # get function signature
    sig_start, sig_end = re.search(
        r"def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(\s*((?:[^()]*|\([^()]*\))*)\s*\)\s*(?:->\s*([^:]+))?\s*:",
        source_code,
    ).span()
    signature = source_code[sig_start:sig_end]
    return signature


def get_formatted_docstring(func):
    # get the docstring and split into lines
    docstring = "\n".join(line.lstrip(" ") for line in func.__doc__.split("\n"))
    sections = docstring.strip().split("\n\n")

    # in case there's additional newlines, collect all the sections together
    final_sections = []
    count = 0
    for section in sections:
        if section.startswith("Args:"):
            final_sections.append(section)
            count = 1
        elif section.startswith("Returns:"):
            final_sections.append(section)
            count = 2
        elif section.startswith("Raises:"):
            final_sections.append(section)
            count = 3
        else:
            if count == 0:
                final_sections.append(section)
            else:
                final_sections[-1] += "\n" + section

    description = ""
    args_str = []
    returns_str = []
    raises_str = []

    # Iterate over the sections and classify each one
    for section in final_sections:

        # Extract the "Args" section
        if section.startswith("Args:"):
            arg_lines = section.strip().split("\n")[1:]
            for line in arg_lines:
                match = re.match(r"(\s*)(\S+): (.+)", line)
                if match:
                    _, arg, desc = match.groups()
                    args_str.append(f"- `{arg}` - {desc}")

        # Extract the "Returns" section
        elif section.startswith("Returns:"):
            return_lines = section.strip().split("\n")[1:]
            for line in return_lines:
                match = re.match(r"(\s*)(\S+): (.+)", line)
                if match:
                    _, arg, desc = match.groups()
                    returns_str.append(f"- `{arg}` - {desc}")
                elif len(returns_str) == 0:
                    returns_str.append(section.strip().split("Returns:")[1].strip())

        # Extract the "Raises" section
        elif section.startswith("Raises:"):
            raise_lines = section.strip().split("\n")[1:]
            for line in raise_lines:
                match = re.match(r"(\s*)(\S+): (.+)", line)
                if match:
                    _, exception, desc = match.groups()
                    raises_str.append(f"- `{exception}`: {desc}")

        # Treat the first section as the main description
        else:
            description += section.strip()

    # Construct the new docstring format
    formatted_docstring = f"{description}"
    if args_str:
        formatted_docstring += "\n\n**Arguments**:\n\n" + "\n".join(args_str) + "\n\n"
    if returns_str:
        formatted_docstring += "\n\n**Returns**:\n\n" + "\n".join(returns_str) + "\n\n"
    if raises_str:
        formatted_docstring += f"\n\n**Raises**:\n\n" + "\n".join(raises_str) + "\n"
    formatted_docstring = formatted_docstring.strip()

    return formatted_docstring


def write_function_and_class_jsons(details, private_modules):
    # create the json_files folder
    os.makedirs("json_files", exist_ok=True)

    # load all function and class docs
    for module_path in details:
        # skip private modules
        if module_path in private_modules:
            continue

        # get the module namespace from the path
        module_name = module_path.strip(".py").replace("/", ".")

        # load all function docs
        functions = details[module_path]["functions"]
        for function_name in functions:
            function = functions[function_name]
            functions[function_name] = dict()

            # get the signature of the function
            source_code = inspect.getsource(function)
            signature = get_function_signature(source_code)

            # get the formatted docstring of the function
            if function.__doc__:
                formatted_docstring = get_formatted_docstring(function)
                functions[function_name]["docstring"] = formatted_docstring
            else:
                functions[function_name]["docstring"] = ""
            functions[function_name]["signature"] = signature
            functions[function_name]["source_code"] = source_code

        # load all class docs
        classes = details[module_path]["classes"]
        for class_name in classes:
            class_ = classes[class_name]
            class_docstring = class_.__doc__

            # get all relevant members of the class
            members = dict()
            for member in inspect.getmembers(class_):
                module = getattr(member[1], "__module__", "")
                if (
                    (isinstance(module, str) and module.startswith("unify."))
                    or isinstance(member[1], property)
                ) and (member[0].startswith("__") or not member[0].startswith("_")):
                    members[member[0]] = member[1]

            # get the source code for all members
            for member in members:
                obj = members[member]
                if isinstance(obj, property):
                    members[member] = {
                        "obj": obj,
                        "source_code": inspect.getsource(obj.fget),
                    }
                else:
                    members[member] = {
                        "obj": obj,
                        "source_code": inspect.getsource(obj),
                    }

            # get the method signature and docstring for all the methods
            for member in members:
                obj = members[member]["obj"]
                source_code = members[member]["source_code"]

                # get signature
                signature = get_function_signature(source_code)

                # get the formatted docstring of the method
                if obj.__doc__:
                    formatted_docstring = get_formatted_docstring(obj)
                else:
                    formatted_docstring = ""

                # store the results
                members[member] = {
                    "member": member,
                    "source_code": source_code,
                    "signature": signature,
                    "docstring": formatted_docstring,
                }

            classes[class_name] = {"members": members, "docstring": class_docstring}

        # write all the functions to separate files
        for function_name in functions:
            with open(f"json_files/{module_name}.{function_name}.json", "w") as f:
                json.dump(functions[function_name], f)

        # write all the classes to separate files
        for class_name in classes:
            with open(f"json_files/{module_name}.{class_name}.json", "w") as f:
                json.dump(classes[class_name], f)


def write_docs():
    files = os.listdir("json_files")
    new_line = lambda f: f.write("\n\n")
    python_path_json = dict()

    for file_path in sorted(files):
        # get the module str
        module_name = file_path.replace(".json", "")
        module_path = "docs/" + module_name.replace(".", "/")

        # storing the tree of calls to update the mint.json
        info = python_path_json
        namespace = module_name.split(".")
        for key in namespace:
            if key not in info:
                info[key] = dict()
            info = info[key]

        # load the data from the json
        os.makedirs("/".join(module_path.split("/")[:-1]), exist_ok=True)
        with open(os.path.join("json_files", file_path)) as f:
            module_data = json.load(f)

        # write the results to an mdx
        name = module_name.split(".")[-1]
        with open(f"{module_path}.mdx", "w") as f:
            f.write("---\n" f"title: '{name}'\n" "---")

            # if the module is a class
            if "members" in module_data:
                # add class def python block
                new_line(f)
                f.write(f"```python\n" f"class {name}\n" "```")
                new_line(f)

                # add docstring for python class
                if module_data.get("docstring"):
                    f.write(module_data.get("docstring"))

                # add details for each instance method/property
                for member_name in module_data["members"]:
                    member = module_data["members"][member_name]
                    escaped_member_name = member_name.replace("_", "\_")
                    signature = member["signature"]
                    docstring = member["docstring"]

                    # add escape characters to the docstring
                    for key, value in replace.items():
                        docstring = docstring.replace(key, value)

                    # add method info
                    new_line(f)
                    f.write("---")
                    new_line(f)
                    f.write(f"### {escaped_member_name}")
                    new_line(f)
                    f.write("```python\n" f"{signature}\n" "```")
                    new_line(f)
                    f.write(docstring)

            # if the module is a function
            else:
                signature = module_data["signature"]
                docstring = module_data["docstring"]

                # add function info
                new_line(f)
                f.write("```python\n" f"{signature}\n" "```")
                new_line(f)
                f.write(docstring)

    with open("python_path.json", "w") as f:
        json.dump(python_path_json, f, indent=4)


def get_mint_format(python_path, root=""):
    results = []
    for key in python_path:
        results.append(
            {
                "group": key,
                "pages": get_mint_format(python_path[key], os.path.join(root, key)),
            }
        )
        if len(results[-1]["pages"]) == 0:
            results[-1] = os.path.join(root, key)
    return results


def update_mint():
    with open("mint.json") as f:
        mint = json.load(f)

    with open("python_path.json") as f:
        python_path = json.load(f)

    mint["navigation"][1] = {
        "group": "",
        "pages": get_mint_format(python_path["unify"], root="python"),
    }

    with open("mint.json", "w") as f:
        json.dump(mint, f)


if __name__ == "__main__":

    # parse args
    parser = argparse.ArgumentParser(
        prog="Orchestra Doc Builder",
        description="Build the Orchestra REST API Documentation",
    )
    parser.add_argument("-w", "--write", action="store_true")
    parser.add_argument("-dd", "--docs_dir", type=str, help="directory for docs")
    args = parser.parse_args()

    if args.write:

        # docs directory
        if args.docs_dir is not None:
            docs_dir = args.docs_dir
        else:
            docs_dir = "../unify-docs"

        # mint.json filepaths
        docs_mint_filepath = os.path.join(docs_dir, "mint.json")
        local_mint_filepath = "mint.json"

        # copy mint.json
        if os.path.exists(docs_mint_filepath):
            shutil.copyfile(docs_mint_filepath, local_mint_filepath)
        else:
            raise Exception(
                "No mint.json found locally,"
                "and {} also does not exist for retrieval".format(docs_mint_filepath),
            )

    module_paths = get_all_modules()

    details = get_functions_and_classes(module_paths)

    details, private_modules = filter_and_import(details)

    write_function_and_class_jsons(details, private_modules)

    write_docs()

    update_mint()

    if args.write:

        if os.path.exists("../unify-docs/python"):
            shutil.rmtree("../unify-docs/python")

        # move files + dirs
        shutil.move("docs/unify", "python")
        shutil.move("python", "../unify-docs/python")
        shutil.move("mint.json", "../unify-docs/mint.json")
