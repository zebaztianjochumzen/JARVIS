#!/usr/bin/env python3
"""Auto-generates documentation.md by sending repo files to the Claude API."""

import glob
import os
import anthropic

FILE_PATTERNS = [
    "terraform/**/*.tf",
    "bootstrap/**/*.tf",
    ".github/workflows/*.yml",
    ".github/smoke-tests/*.sh",
]


def collect_files() -> dict[str, str]:
    files = {}
    for pattern in FILE_PATTERNS:
        for path in sorted(glob.glob(pattern, recursive=True)):
            with open(path) as f:
                files[path] = f.read()
    return files


def generate_docs(files: dict[str, str]) -> str:
    client = anthropic.Anthropic()

    files_block = "\n\n".join(
        f'<file path="{path}">\n{content}\n</file>'
        for path, content in files.items()
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
                            "4. **GitHub Actions Workflows** — each workflow, trigger, and what it does step by step\n"
                            "5. **Deployment Guide** — bootstrap → deploy dev → verify → merge → deploy production\n"
                            "6. **Environment Configuration** — how dev and production differ\n\n"
                            "Write only the documentation.md content, no preamble."
                        ),
                    },
                ],
            }
        ],
    )

    return response.content[0].text


if __name__ == "__main__":
    files = collect_files()
    print(f"Collected {len(files)} files: {', '.join(files)}")
    docs = generate_docs(files)
    with open("documentation.md", "w") as f:
        f.write(docs)
    print("documentation.md written successfully")
