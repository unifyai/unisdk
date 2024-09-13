import os
import re
import json
import argparse
import shutil

replace = {
    "<uploaded_by>/<model_name>@<provider_name>": r"\<uploaded_by\>/\<model_name\>@\<provider_name\>",
    "<model_name>@<provider_name>": r"\<model_name\>@\<provider_name\>",
    "# noqa: DAR101.": "",
    "# noqa: DAR201.": "",
    "####": "---\n\n###",
}

folders = []
for path in os.listdir("unify"):
    if not path.startswith("__") and os.path.isdir(os.path.join("unify", path)):
        folders.append(path)

submods_to_ignore = []


def process_output():
    # load the result from pydoc-markdown
    with open("output/result.txt") as f:
        content = f.readlines()

    # load the current mint.json
    with open("mint.json") as f:
        mint = json.load(f)

    # extract all section headers from the result
    sections, ignore_sections, modules = [], [], []
    for idx, line in enumerate(content):
        module_str = line.lstrip("# ").rstrip("\n")
        if line.startswith("# "):
            if module_str in submods_to_ignore or (
                module_str.startswith(r"\_")
                and not module_str.startswith(r"\_\_init\_\_")
            ):
                ignore_sections.append(idx)
            print(line)
            sections.append(idx)

    # extract the section content for each header
    section_wise_content = []
    for i, idx in enumerate(sections):
        if r"\_\_init\_\_" not in content[idx]:
            next_idx = sections[i + 1] - 1 if i < len(sections) - 1 else None
            if idx not in ignore_sections:
                section_wise_content.append(content[idx:next_idx])

    # generate the mdx output
    current_folder = None
    for section_content in section_wise_content:
        module_name = section_content[0].strip("\n")[2:].replace("\\", "")
        module_path = module_name
        print(module_name)

        if (
            len("".join(section_content[1:-1]).strip()) == 0
            and module_name not in folders
        ):
            continue

        # folder root
        if module_name in folders:
            if current_folder:
                modules[-1]["pages"] = sorted(modules[-1]["pages"])
            current_folder = module_name
        # files inside the folder
        elif module_name.split(".")[0] in folders:
            module_path = module_name.replace(".", "/")
            module_name = ".".join(module_name.split(".")[1:])
            os.makedirs(
                "output/" + "/".join(module_path.split("/")[:-1]), exist_ok=True
            )
        # files in the root
        elif current_folder:
            modules[-1]["pages"] = sorted(modules[-1]["pages"])
            current_folder = None

        # create sub-group for folders
        if current_folder:
            if module_name in folders:
                modules.append({"group": module_name, "pages": []})
                continue
            else:
                modules[-1]["pages"].append(f"python/{module_path}")
        # append directly for root files
        else:
            modules.append(f"python/{module_path}")

        # write the content for the files
        with open(f"output/{module_path}.mdx", "w") as f:
            f.write(f"---\ntitle: '{module_name}'\n---\n")
            for i, content in enumerate(section_content):
                if re.findall(r"^##.*Objects\n$", content):
                    section_content[i] = section_content[i].replace(" Objects", "")
            final_content = "".join(section_content[1:])
            for key, value in replace.items():
                final_content = final_content.replace(key, value)
            f.write(final_content)

    # for subfolders at the end
    if current_folder:
        modules[-1]["pages"] = sorted(modules[-1]["pages"])
        current_folder = None

    # update mint
    mint["navigation"][1] = {
        "group": "",
        "pages": sorted(
            modules, key=lambda x: x["group"] if isinstance(x, dict) else x
        ),
    }
    with open("mint.json", "w") as f:
        json.dump(mint, f, indent=4)


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

        # create output directory
        os.makedirs("output", exist_ok=True)

        # copy markdown to unify folder
        shutil.copyfile("pydoc-markdown.yml", "unify/pydoc-markdown.yml")

        # trigger pydoc-markdown
        os.chdir("unify")
        os.system("pydoc-markdown | tee ../output/result.txt")
        os.chdir("..")

    # generate docs
    process_output()

    if args.write:

        # remove files + dirs
        os.remove("output/result.txt")
        os.remove("unify/pydoc-markdown.yml")
        if os.path.exists("../unify-docs/python"):
            shutil.rmtree("../unify-docs/python")

        # move files + dirs
        shutil.move("output", "python")
        shutil.move("python", "../unify-docs/python")
        shutil.move("mint.json", "../unify-docs/mint.json")
