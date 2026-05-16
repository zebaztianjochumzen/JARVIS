---
name: mcporter
description: Bridge to MCP (Model Context Protocol) servers — use any MCP tool from OpenClaw
user-invocable: false
disable-model-invocation: false
metadata:
  openclaw:
    requires:
      - file: mcp_servers.json
---

# MCP Bridge (mcporter)

JARVIS connects to MCP servers defined in `mcp_servers.json`. All MCP tools
are automatically registered with the prefix `mcp_<server>_<tool>` and
appear in Claude's tool list alongside native JARVIS tools.

## How MCP tools work in JARVIS
- `jarvis/mcp_client.py` reads `mcp_servers.json` at startup
- Each server is started as a stdio subprocess
- Tools are registered as `mcp_{server}_{tool_name}`
- Claude calls them exactly like any other JARVIS tool

## Adding a new MCP server
Edit `mcp_servers.json`:
```json
{
  "servers": [
    {
      "name": "github",
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": { "GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_TOKEN}" }
    }
  ]
}
```
Restart JARVIS to load the new server.

## OpenClaw ↔ MCP sharing
Both OpenClaw's mcporter skill and JARVIS's mcp_client.py can share the
same `mcp_servers.json`. OpenClaw reads it to register skills; JARVIS reads
it to register tools. No duplication needed.

## Available MCP servers (examples)
- `github` — PR review, issue management, repo search
- `filesystem` — read/write files outside the JARVIS workspace
- `slack` — post to Slack channels
- `databases` — query PostgreSQL / SQLite directly
- `smart-home` — Philips Hue, Home Assistant

## Security
MCP tool calls are routed through `execute_tool` like any other tool.
Dangerous MCP tools (write operations) trigger the approval queue.
