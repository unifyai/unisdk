import json
from typing import List


def process_output(content: List[str]):
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
        with open(f"{module_name}.mdx", "w") as f:
            f.write(f"---\ntitle: '{module_name}'\n---\n")
            f.write("".join(section_content[1:]))
    for idx, data in enumerate(mint["navigation"]):
        if data["group"] == "":
            mint["navigation"][idx] = {
                "group": "",
                "pages": modules
            }
            break
    with open("mint.json", "w") as f:
        json.dump(mint, f)


if __name__ == "__main__":
    with open("result.txt") as f:
        results = f.readlines()
    process_output(results)
