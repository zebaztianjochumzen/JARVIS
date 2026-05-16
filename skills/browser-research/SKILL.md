---
name: browser-research
description: Multi-step web research using Playwright browser — navigate, extract, and synthesise
user-invocable: true
---

# Browser Research

When the user asks to research a topic in depth, read a specific page,
or extract information from a website:

## Deep research workflow
1. Call `web_search` to find the most relevant URLs (3–5 results)
2. For each promising URL, call `browser_navigate` to load it fully
3. Call `browser_extract_text` to pull the page content
4. Take a `browser_screenshot` if visual context matters
5. Synthesise findings into a concise summary

## Single-page reading
1. `browser_navigate` to the URL
2. `browser_extract_text` for content
3. Summarise — do not repeat the raw text verbatim

## Form filling / automation
1. `browser_navigate` to the target page
2. Identify fields with `browser_extract_text`
3. `browser_fill` each field
4. `browser_click` to submit
5. `browser_screenshot` to confirm success

**Requires approval before `browser_execute_js` on any external site.**
Never fill forms with personal data (passwords, credit cards) without explicit instruction.

## Example invocations
- "Research the top 3 AI chip companies and compare them"
- "Read the article at [URL] and summarise it"
- "What does the NVIDIA investor page say about Q1 earnings?"
- "Spawn parallel research on OpenAI, Anthropic, and DeepMind"
