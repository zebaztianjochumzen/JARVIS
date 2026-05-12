#!/usr/bin/env python3
"""Auto-generates documentation.md by sending repo files to the Claude API."""

import glob
import anthropic

FILE_PATTERNS = [
    "terraform/**/*.tf",
    "bootstrap/**/*.tf",
    ".github/workflows/*.yml",
    ".github/smoke-tests/*.sh",
]


def collect_files() -> dict[str, str]:
    result: dict[str, str] = {}
    for pattern in FILE_PATTERNS:
        for path in sorted(glob.glob(pattern, recursive=True)):
            with open(path, encoding="utf-8") as fh:
                result[path] = fh.read()
    return result


def generate_docs(file_map: dict[str, str]) -> str:
    client = anthropic.Anthropic()

    files_block = "\n\n".join(
        f'<file path="{path}">\n{content}\n</file>'
        for path, content in file_map.items()
    )

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        system=(
            "You are a technical documentation writer. "
            "Generate clear, well-structured Markdown documentation."
        ),
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": files_block,
                        "cache_control": {"type": "ephemeral"},
                    },
                    {
                        "type": "text",
                        "text": (
                            "Generate a complete documentation.md for the JARVIS project "
                            "based on the files above. Include:\n\n"
                            "1. **Project Overview** — what JARVIS is and its purpose\n"
                            "2. **Repository Structure** — annotated directory tree\n"
                            "3. **Infrastructure** — every AWS resource, what it creates and why\n"
                            "4. **GitHub Actions Workflows** — each workflow, trigger, and what it"
                            " does step by step\n"
                            "5. **Deployment Guide** — bootstrap → deploy dev → verify → merge"
                            " → deploy production\n"
                            "6. **Environment Configuration** — how dev and production differ\n\n"
                            "Write only the documentation.md content, no preamble."
                        ),
                    },
                ],
            }
        ],
    )

    block = response.content[0]
    if not isinstance(block, anthropic.types.TextBlock):
        raise ValueError(f"Unexpected response block type: {type(block)}")
    return block.text


if __name__ == "__main__":
    collected = collect_files()
    print(f"Collected {len(collected)} files: {', '.join(collected)}")
    docs = generate_docs(collected)
    with open("documentation.md", "w", encoding="utf-8") as out:
        out.write(docs)
    print("documentation.md written successfully")
