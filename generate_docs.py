import json


replace = {
    "<uploaded_by>/<model_name>@<provider_name>": r"\<uploaded_by\>/\<model_name\>@\<provider_name\>",
    "<model_name>@<provider_name>": r"\<model_name\>@\<provider_name\>",
    "# noqa: DAR101.": ""
}


def process_output():
    with open("output/result.txt") as f:
        content = f.readlines()
    with open("mint.json") as f:
        mint = json.load(f)
    sections, modules = [], []
    for idx, line in enumerate(content):
        if line.startswith("# "):
            print(line)
            sections.append(idx)
    section_wise_content = []
    for i, idx in enumerate(sections):
        if r"\_\_init\_\_" not in content[idx]:
            next_idx = sections[i + 1] - 1 if i < len(sections) - 1 else None
            section_wise_content.append(content[idx:next_idx])
    for section_content in section_wise_content:
        module_name = section_content[0].strip("\n")[2:]
        modules.append(f"python/{module_name}")
        with open(f"output/{module_name}.mdx", "w") as f:
            f.write(f"---\ntitle: '{module_name}'\n---\n")
            final_content = "".join(section_content[1:])
            for key, value in replace.items():
                final_content = final_content.replace(key, value)
            f.write(final_content)
    for idx, data in enumerate(mint["navigation"]):
        if data["group"] == "":
            mint["navigation"][idx] = {"group": "", "pages": sorted(modules)}
            break
    with open("mint.json", "w") as f:
        json.dump(mint, f)


if __name__ == "__main__":
    process_output()
