---
name: obsidian-sync
description: Sync facts, summaries, and skills to the Obsidian vault; query vault notes for context
user-invocable: true
metadata:
  openclaw:
    requires:
      - env: OBSIDIAN_VAULT_PATH
---

# Obsidian Sync

JARVIS maintains a live mirror of its memory in the Obsidian vault at
`$OBSIDIAN_VAULT_PATH/JARVIS/`. This skill teaches workflows for
querying and writing to that vault.

## Vault structure
```
JARVIS/
  Memory/
    Facts/          ← one .md per remembered fact
    Memory.md       ← master index of all facts
    Context.md      ← latest context compression
    Daily/          ← YYYY-MM-DD.md conversation summaries
  Skills/           ← SKILL.md files (this directory)
```

## Reading from the vault
When the user asks "what do you know about X" or "check your notes on Y":
1. Use `recall_semantic` to search memory by meaning
2. If a vault path is configured, cross-reference by reading the relevant .md file

## Writing to the vault
JARVIS automatically syncs facts via `remember_this` → `obsidian.write_fact()`.
For manual notes:
1. Use `save_note` for ephemeral notes (local file, not vault)
2. Use `remember_this` for durable facts that should appear in the vault

## Storing skills in the vault
OpenClaw skills live in `$OBSIDIAN_VAULT_PATH/JARVIS/Skills/`.
Each skill is a SKILL.md file that OpenClaw and JARVIS can both read.
To add a new skill to the vault:
1. Create the SKILL.md content
2. Call `write_file` with path `skills/<name>/SKILL.md`
3. Note: requires admin session (blocked for guest sessions)

## Example invocations
- "What do you know about my work schedule?"
- "Open my Obsidian vault"
- "Summarise today's conversation and save it"
