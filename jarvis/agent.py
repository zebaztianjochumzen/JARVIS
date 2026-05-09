"""JARVIS agent — Claude with streaming, tool use, and persistent memory."""

import json
from pathlib import Path

import anthropic

from jarvis.memory import Memory
from jarvis.tools import TOOLS, execute_tool

SOUL_PATH = Path(__file__).parent.parent / "SOUL.md"
MODEL = "claude-sonnet-4-6"
MAX_HISTORY = 20


class Agent:
    def __init__(self) -> None:
        self.client = anthropic.Anthropic()
        self.memory = Memory()
        self.soul = SOUL_PATH.read_text()
        self.pending_actions: list[dict] = []

    def _system_prompt(self) -> str:
        facts = self.memory.get_all_facts()
        if not facts:
            return self.soul
        facts_block = "\n".join(f"- {k}: {v}" for k, v in facts.items())
        return f"{self.soul}\n\n## What you know about the user\n{facts_block}"

    def ask(self, user_input: str, stream_callback=None) -> str:
        self.memory.append_message("user", user_input)
        messages = self.memory.get_recent_messages(MAX_HISTORY)

        response_text = self._run(messages, stream_callback=stream_callback)

        self.memory.append_message("assistant", response_text)
        return response_text

    def _run(self, messages: list[dict[str, str]], stream_callback=None) -> str:
        """Stream a response, executing tool calls until a final text reply is produced."""
        msg_list: list[dict] = list(messages)

        while True:
            full_text = ""
            tool_uses: list[dict] = []

            with self.client.messages.stream(
                model=MODEL,
                max_tokens=1024,
                system=self._system_prompt(),
                tools=TOOLS,
                messages=msg_list,
            ) as stream:
                for text in stream.text_stream:
                    if stream_callback:
                        stream_callback(text)
                    else:
                        print(text, end="", flush=True)
                    full_text += text

                final = stream.get_final_message()

            if final.stop_reason == "tool_use":
                # Strip SDK-only fields (e.g. parsed_output) that the API rejects
                assistant_content = []
                for block in final.content:
                    b = block.model_dump()
                    if b.get("type") == "text":
                        assistant_content.append({"type": "text", "text": b["text"]})
                    elif b.get("type") == "tool_use":
                        assistant_content.append({"type": "tool_use", "id": b["id"], "name": b["name"], "input": b["input"]})
                    else:
                        assistant_content.append(b)
                tool_uses = [b for b in assistant_content if b.get("type") == "tool_use"]

                # Append assistant turn (may include partial text + tool use blocks)
                msg_list.append({"role": "assistant", "content": assistant_content})

                # Execute each tool and build the results turn
                tool_results = []
                for tool in tool_uses:
                    result = execute_tool(tool["name"], tool.get("input", {}), self.memory, agent=self)
                    import time as _time
                    self.pending_actions.append({
                        "type":   "tool_log",
                        "tool":   tool["name"],
                        "input":  tool.get("input", {}),
                        "result": result,
                        "ts":     _time.strftime("%H:%M:%S"),
                    })
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool["id"],
                        "content": result,
                    })

                msg_list.append({"role": "user", "content": tool_results})
                # Loop — Claude will now produce a final reply using the tool results

            else:
                if not stream_callback:
                    print()
                return full_text
