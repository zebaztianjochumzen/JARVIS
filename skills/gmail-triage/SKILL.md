---
name: gmail-triage
description: Fetch Gmail inbox and categorise emails as URGENT / ACTION / FYI with one-line summaries
user-invocable: true
metadata:
  openclaw:
    requires:
      - env: GOOGLE_CREDENTIALS_PATH
---

# Gmail Triage

When the user asks to triage their inbox, check emails, or manage their mail:

1. Call `gmail_triage` to fetch all unread emails and categorise them
2. Present results in three groups — **URGENT** → **ACTION** → **FYI**
3. For each URGENT item, offer to: draft a reply, create a calendar event, or take another action
4. At the end, ask: "Want me to mark any of these as read?"

**URGENT** = requires a response today, deadline imminent, flagged by sender  
**ACTION** = needs a response but not urgent  
**FYI** = newsletters, receipts, notifications — no response needed

Never read or repeat full email body content unless the user explicitly asks.
Never send a reply without explicit confirmation.

If the inbox is empty or has no unread mail, say: "Inbox clear, sir."

## Example invocations
- "Triage my inbox"
- "What emails need attention?"
- "Run email triage"
- "Any urgent emails?"
