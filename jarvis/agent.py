"""JARVIS agent — Claude with streaming, tool use, persistent memory, and context compression."""

import json
from pathlib import Path

import anthropic

from jarvis.memory import Memory
from jarvis.tools import TOOLS, execute_tool

AGENT_PATH   = Path(__file__).parent.parent / "AGENT.md"
SOUL_PATH    = Path(__file__).parent.parent / "SOUL.md"
MODEL        = "claude-sonnet-4-6"
MAX_HISTORY  = 20
COMPRESS_AT  = 30   # compress when stored messages exceed this


class Agent:
    def __init__(self) -> None:
        self.client  = anthropic.Anthropic()
        self.memory  = Memory()
        self.soul    = (AGENT_PATH if AGENT_PATH.exists() else SOUL_PATH).read_text()
        self.pending_actions: list[dict] = []
        self._cancelled = False

    def _system_prompt(self) -> str:
        facts = self.memory.get_all_facts()
        if not facts:
            return self.soul
        facts_block = "\n".join(f"- {k}: {v}" for k, v in facts.items())
        return f"{self.soul}\n\n## What you know about the user\n{facts_block}"

    def ask(self, user_input: str, stream_callback=None, action_callback=None, tool_filter=None) -> str:
        """Run the agent.

        tool_filter: optional set/frozenset of tool names to EXCLUDE from this
        call. Used by OpenClaw gateway to sandbox guest sessions without
        touching global state.
        """
        self.memory.append_message("user", user_input)

        # ── Context compression ───────────────────────────────────────────────
        if self.memory.should_compress(COMPRESS_AT):
            self._compress_context()

        messages = self.memory.get_messages_with_context(MAX_HISTORY)
        response_text = self._run(
            messages,
            stream_callback=stream_callback,
            action_callback=action_callback,
            tool_filter=tool_filter,
        )

        self.memory.append_message("assistant", response_text)
        return response_text

    def cancel(self) -> None:
        self._cancelled = True

    # ── Context compression ───────────────────────────────────────────────────

    def _compress_context(self) -> None:
        """Summarise old messages via Claude, then prune and write to Obsidian."""
        old_msgs = self.memory.get_messages_for_compression(keep_recent=15)
        if not old_msgs:
            return

        formatted = "\n".join(
            f"{m['role'].upper()}: {m['content'][:300]}" for m in old_msgs
        )
        try:
            resp = self.client.messages.create(
                model=MODEL,
                max_tokens=300,
                messages=[{
                    "role": "user",
                    "content": (
                        "Summarise the key information from this conversation excerpt in "
                        "3-5 concise sentences. Focus on facts, decisions, and context "
                        "that will help continue the conversation naturally:\n\n"
                        + formatted
                    ),
                }],
            )
            summary   = resp.content[0].text.strip()
            prune_ids = [m["id"] for m in old_msgs]
            self.memory.store_context_summary(summary, prune_ids)

            # Write a daily summary note to Obsidian as well
            try:
                from jarvis import obsidian
                obsidian.write_daily_summary(summary)
            except Exception:
                pass

            print(f"[Agent] Context compressed ({len(prune_ids)} msgs → summary)", flush=True)
        except Exception as e:
            print(f"[Agent] Context compression failed: {e}", flush=True)

    # ── Main inference loop ───────────────────────────────────────────────────

    def _run(self, messages: list[dict[str, str]], stream_callback=None, action_callback=None, tool_filter=None) -> str:
        """Stream a response, executing tool calls until a final text reply is produced.

        tool_filter: optional set of tool names to exclude (guest-session sandbox).
        """
        self._cancelled = False
        msg_list: list[dict] = list(messages)

        while True:
            full_text = ""
            tool_uses: list[dict] = []

            try:
                from jarvis import mcp_client as _mcp
                all_tools = TOOLS + _mcp.get_mcp_tools()
            except ImportError:
                all_tools = TOOLS

            if tool_filter:
                all_tools = [t for t in all_tools if t["name"] not in tool_filter]

            with self.client.messages.stream(
                model=MODEL,
                max_tokens=1024,
                system=self._system_prompt(),
                tools=all_tools,
                messages=msg_list,
            ) as stream:
                for text in stream.text_stream:
                    if self._cancelled:
                        break
                    if stream_callback:
                        stream_callback(text)
                    else:
                        print(text, end="", flush=True)
                    full_text += text

                final = stream.get_final_message()

            if self._cancelled:
                return full_text

            if final.stop_reason == "tool_use":
                assistant_content = []
                for block in final.content:
                    b = block.model_dump()
                    if b.get("type") == "text":
                        assistant_content.append({"type": "text", "text": b["text"]})
                    elif b.get("type") == "tool_use":
                        assistant_content.append({
                            "type":  "tool_use",
                            "id":    b["id"],
                            "name":  b["name"],
                            "input": b["input"],
                        })
                    else:
                        assistant_content.append(b)

                tool_uses = [b for b in assistant_content if b.get("type") == "tool_use"]
                msg_list.append({"role": "assistant", "content": assistant_content})

                tool_results = []
                for tool in tool_uses:
                    result = execute_tool(
                        tool["name"], tool.get("input", {}),
                        self.memory, agent=self, action_callback=action_callback,
                    )
                    import time as _time
                    self.pending_actions.append({
                        "type":   "tool_log",
                        "tool":   tool["name"],
                        "input":  tool.get("input", {}),
                        "result": result,
                        "ts":     _time.strftime("%H:%M:%S"),
                    })
                    tool_results.append({
                        "type":        "tool_result",
                        "tool_use_id": tool["id"],
                        "content":     result,
                    })

                msg_list.append({"role": "user", "content": tool_results})

            else:
                if not stream_callback:
                    print()
                return full_text
