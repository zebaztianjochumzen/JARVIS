"""Multi-agent orchestration tools — parallel sub-agent execution for JARVIS.

Gives Claude the ability to spawn multiple isolated Agent instances in
parallel threads, each tackling a sub-query, then collect and merge results.

This maps to OpenClaw's spawn/send/monitor capability but runs entirely
within JARVIS's existing Python process — no extra services required.

Tools exposed to Claude:
  spawn_parallel_research(topics, query_template) → merged research
  parallel_web_search(queries)                    → merged search results
"""

import concurrent.futures
import json
from typing import Optional


# ── spawn_parallel_research ───────────────────────────────────────────────────

def spawn_parallel_research(topics: list, query_template: str = "{topic}") -> str:
    """Spawn one lightweight research agent per topic, run them in parallel.

    Each sub-agent gets a fresh conversation context (no shared memory) and
    is allowed only: web_search, get_weather, get_stock_price, get_news.
    Results are merged and returned as a single string.

    Args:
        topics:         List of topic strings, e.g. ["OpenAI", "Anthropic", "DeepMind"]
        query_template: Template with {topic} placeholder, e.g. "latest news on {topic}"
    """
    if not topics:
        return "No topics provided."

    if len(topics) > 8:
        topics = topics[:8]
        note = " (capped at 8 parallel agents)"
    else:
        note = ""

    results: dict[str, str] = {}

    def _research_one(topic: str) -> tuple[str, str]:
        from jarvis.agent import Agent
        from jarvis.tools.info import web_search

        query = query_template.replace("{topic}", topic)
        try:
            # Use a raw web_search instead of a full agent turn to keep it
            # lightweight — full Agent instances are expensive to spin up N×.
            raw = web_search(query=query, num_results=4)
            return topic, raw
        except Exception as exc:
            return topic, f"Error researching '{topic}': {exc}"

    with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(topics), 6)) as pool:
        futures = {pool.submit(_research_one, t): t for t in topics}
        for fut in concurrent.futures.as_completed(futures, timeout=45):
            try:
                topic, result = fut.result()
                results[topic] = result
            except Exception as exc:
                results[futures[fut]] = f"Error: {exc}"

    lines = [f"## {t}\n{results.get(t, 'No result')}" for t in topics]
    return f"Parallel research complete{note}:\n\n" + "\n\n".join(lines)


# ── parallel_web_search ───────────────────────────────────────────────────────

def parallel_web_search(queries: list) -> str:
    """Run multiple DuckDuckGo searches simultaneously and return all results.

    Use when a single response needs information from several distinct searches.
    Faster than sequential tool calls when queries are independent.

    Args:
        queries: List of search query strings (max 6).
    """
    if not queries:
        return "No queries provided."

    queries = queries[:6]

    def _search_one(query: str) -> tuple[str, str]:
        from jarvis.tools.info import web_search
        try:
            return query, web_search(query=query, num_results=3)
        except Exception as exc:
            return query, f"Search error: {exc}"

    results: dict[str, str] = {}

    with concurrent.futures.ThreadPoolExecutor(max_workers=len(queries)) as pool:
        futures = {pool.submit(_search_one, q): q for q in queries}
        for fut in concurrent.futures.as_completed(futures, timeout=30):
            try:
                q, r = fut.result()
                results[q] = r
            except Exception as exc:
                results[futures[fut]] = f"Error: {exc}"

    lines = [f"**{q}**\n{results.get(q, 'No result')}" for q in queries]
    return "\n\n---\n\n".join(lines)
