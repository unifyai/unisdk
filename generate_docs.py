
from typing import List


def process_output(content: List[str]):
    sections = []
    for idx, line in enumerate(content):
        if line.startswith("# "):
            print(line)
            sections.append(idx)
    section_wise_content = []
    for i, idx in enumerate(sections):
        if r"\_\_init\_\_" not in content[idx]:
            next_idx = sections[i + 1] - 1 if i < len(sections) - 1 else None
            section_wise_content.append(content[idx : next_idx])
    for section_content in section_wise_content:
        module_name = section_content[0].strip("\n")[2:]
        with open(f"{module_name}.mdx", "w") as f:
            f.write(f"---\ntitle: '{module_name}'\n---\n")
            f.write("".join(section_content[1 : ]))


if __name__ == "__main__":
    with open("result.txt") as f:
        process_output(f.readlines())