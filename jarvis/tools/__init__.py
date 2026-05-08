"""Tool registry — exposes TOOLS list and execute_tool() to the agent."""

from jarvis.tools.basic import (
    get_current_time,
    save_note,
    remember_this,
    recall_fact,
    forget_fact,
)

# JSON schemas passed to Claude's tool use API
TOOLS: list[dict] = [
    {
        "name": "get_current_time",
        "description": "Returns the current local date and time.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "save_note",
        "description": "Saves a note to the user's local notes file (~/.jarvis/notes.md).",
        "input_schema": {
            "type": "object",
            "properties": {
                "content": {"type": "string", "description": "The note text to save."}
            },
            "required": ["content"],
        },
    },
    {
        "name": "remember_this",
        "description": "Stores a fact about the user in persistent memory so it can be recalled in future conversations.",
        "input_schema": {
            "type": "object",
            "properties": {
                "key": {"type": "string", "description": "Short label for the fact, e.g. 'user_name', 'preferred_language'."},
                "value": {"type": "string", "description": "The value to store."},
            },
            "required": ["key", "value"],
        },
    },
    {
        "name": "recall_fact",
        "description": "Retrieves a specific stored fact from memory by its key.",
        "input_schema": {
            "type": "object",
            "properties": {
                "key": {"type": "string", "description": "The key of the fact to retrieve."}
            },
            "required": ["key"],
        },
    },
    {
        "name": "forget_fact",
        "description": "Deletes a stored fact from memory.",
        "input_schema": {
            "type": "object",
            "properties": {
                "key": {"type": "string", "description": "The key of the fact to delete."}
            },
            "required": ["key"],
        },
    },
]

_DISPATCH: dict = {
    "get_current_time": get_current_time,
    "save_note": save_note,
    "remember_this": remember_this,
    "recall_fact": recall_fact,
    "forget_fact": forget_fact,
}


def execute_tool(name: str, tool_input: dict, memory: object) -> str:
    fn = _DISPATCH.get(name)
    if fn is None:
        return f"Unknown tool: {name}"
    # Memory-aware tools receive the memory instance
    if name in ("remember_this", "recall_fact", "forget_fact"):
        return fn(memory=memory, **tool_input)
    return fn(**tool_input)
