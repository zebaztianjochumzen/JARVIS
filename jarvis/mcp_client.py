"""MCP (Model Context Protocol) client — connects JARVIS to any MCP server.

Reads mcp_servers.json from the repo root. Each configured server is started
as a stdio subprocess; its tools are exposed to Claude alongside JARVIS's
native tools, so adding one MCP server instantly gives JARVIS access to all
of its capabilities (GitHub, Slack, databases, smart home, etc.).

Naming convention: native MCP tool names are prefixed as
  mcp_<server_name>_<tool_name>
so they never collide with JARVIS's own tools.

Tool dispatch is synchronous (matches JARVIS's execute_tool pattern) but
internally runs on a dedicated asyncio event loop in a daemon thread.

mcp_servers.json format:
{
  "servers": [
    {
      "name":    "filesystem",
      "command": "npx",
      "args":    ["-y", "@modelcontextprotocol/server-filesystem", "/home/user/docs"],
      "env":     {}
    },
    {
      "name":    "github",
      "command": "npx",
      "args":    ["-y", "@modelcontextprotocol/server-github"],
      "env":     {"GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_..."}
    }
  ]
}

Note: MCP servers that use npx require Node.js to be installed.
"""

import asyncio
import json
import threading
from pathlib import Path
from typing import Optional

CONFIG_PATH = Path(__file__).parent.parent / "mcp_servers.json"

# ── Shared state ──────────────────────────────────────────────────────────────
_loop:         Optional[asyncio.AbstractEventLoop] = None
_loop_thread:  Optional[threading.Thread]          = None
_sessions:     dict[str, object]                   = {}   # server_name → ClientSession
_mcp_tools:    list[dict]                          = []   # Claude-format tool schemas
_mcp_tool_map: dict[str, tuple[str, str]]          = {}   # registered → (server, original)
_started       = False


# ── Public API ────────────────────────────────────────────────────────────────

def get_mcp_tools() -> list[dict]:
    """Return all tool schemas loaded from MCP servers (merged into Claude's tools list)."""
    return list(_mcp_tools)


def call_tool_sync(registered_name: str, arguments: dict) -> str:
    """Call an MCP tool synchronously from the JARVIS tool dispatch thread."""
    if _loop is None:
        return "MCP subsystem not running."
    mapping = _mcp_tool_map.get(registered_name)
    if not mapping:
        return f"Unknown MCP tool: {registered_name}"
    server_name, original_name = mapping
    try:
        future = asyncio.run_coroutine_threadsafe(
            _call_async(server_name, original_name, arguments), _loop
        )
        return future.result(timeout=30)
    except TimeoutError:
        return f"MCP tool '{original_name}' timed out."
    except Exception as exc:
        return f"MCP error: {exc}"


def start() -> None:
    """Read mcp_servers.json and start a background session for each server."""
    global _started, _loop, _loop_thread
    if _started:
        return
    _started = True

    if not CONFIG_PATH.exists():
        _write_default_config()
        return

    try:
        config  = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        servers = config.get("servers", [])
    except Exception as e:
        print(f"[MCP] Bad config: {e}", flush=True)
        return

    if not servers:
        print("[MCP] No servers configured in mcp_servers.json", flush=True)
        return

    _loop = asyncio.new_event_loop()
    _loop_thread = threading.Thread(
        target=lambda: _loop.run_until_complete(_run_all_sessions(servers)),
        daemon=True,
        name="mcp-event-loop",
    )
    _loop_thread.start()


def server_summary() -> str:
    """Short status string for /api/memories or health checks."""
    if not _sessions:
        return "MCP: no servers connected"
    names = ", ".join(_sessions.keys())
    total = len(_mcp_tools)
    return f"MCP: {len(_sessions)} server(s) [{names}] — {total} tool(s)"


def get_server_status() -> list[dict]:
    """Return per-server connection status for the /api/status endpoint."""
    result = []
    for name in list(_sessions.keys()):
        tool_count = sum(
            1 for t in _mcp_tools
            if t["name"].startswith(f"mcp_{name.replace('-','_').replace('.','_')}_")
        )
        result.append({"name": name, "connected": True, "tool_count": tool_count})
    return result


# ── Internal ──────────────────────────────────────────────────────────────────

async def _call_async(server_name: str, tool_name: str, arguments: dict) -> str:
    session = _sessions.get(server_name)
    if not session:
        return f"MCP server '{server_name}' is not connected."
    result = await session.call_tool(tool_name, arguments)
    texts  = [c.text for c in result.content if hasattr(c, "text") and c.text]
    return "\n".join(texts) or "(tool returned no text output)"


async def _run_all_sessions(servers: list[dict]) -> None:
    """Start a persistent session for every configured server concurrently."""
    await asyncio.gather(
        *[_hold_session(cfg) for cfg in servers],
        return_exceptions=True,
    )


async def _hold_session(cfg: dict) -> None:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    name    = cfg.get("name", "unnamed")
    command = cfg.get("command", "")
    args    = cfg.get("args", [])
    env     = cfg.get("env") or None

    if not command:
        print(f"[MCP] Server '{name}' has no command — skipping.", flush=True)
        return

    params = StdioServerParameters(command=command, args=args, env=env)

    try:
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                _sessions[name] = session
                print(f"[MCP] Connected: {name}", flush=True)

                tools_result = await session.list_tools()
                _register_tools(name, tools_result.tools)

                # Keep the session alive for the lifetime of the process
                await asyncio.sleep(float("inf"))

    except asyncio.CancelledError:
        pass
    except Exception as exc:
        print(f"[MCP] '{name}' connection failed: {exc}", flush=True)
    finally:
        _sessions.pop(name, None)


def _register_tools(server_name: str, tools: list) -> None:
    """Convert MCP tool descriptors to Claude tool schemas and register them."""
    for tool in tools:
        # Sanitise name: mcp_<server>_<tool>  (only alphanum + _)
        reg_name = (
            "mcp_"
            + server_name.replace("-", "_").replace(".", "_")
            + "_"
            + tool.name.replace("-", "_").replace(".", "_")
        )
        if reg_name in _mcp_tool_map:
            continue  # already registered (reconnect case)

        _mcp_tool_map[reg_name] = (server_name, tool.name)
        _mcp_tools.append({
            "name":         reg_name,
            "description":  f"[MCP:{server_name}] {tool.description or tool.name}",
            "input_schema": tool.inputSchema or {"type": "object", "properties": {}, "required": []},
        })

    count = len([t for t in _mcp_tools if t["name"].startswith(f"mcp_{server_name}")])
    print(f"[MCP] {server_name}: {count} tool(s) registered", flush=True)


def _write_default_config() -> None:
    """Create an empty mcp_servers.json with documented examples."""
    default = {
        "_comment": (
            "Add MCP servers here. Each server is started as a stdio subprocess. "
            "Requires Node.js for npx-based servers."
        ),
        "servers": [
            {
                "_comment": "Example — uncomment and fill in to activate",
                "_name":    "filesystem",
                "_command": "npx",
                "_args":    ["-y", "@modelcontextprotocol/server-filesystem", "C:/Users/you/Documents"],
            },
            {
                "_comment": "Example — GitHub integration",
                "_name":    "github",
                "_command": "npx",
                "_args":    ["-y", "@modelcontextprotocol/server-github"],
                "_env":     {"GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_your_token_here"},
            },
        ],
    }
    CONFIG_PATH.write_text(json.dumps(default, indent=2), encoding="utf-8")
    print(f"[MCP] Created default mcp_servers.json — configure servers to activate MCP.", flush=True)
