"""CLI entry point — run with: python -m jarvis"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

try:
    from jarvis.secrets import get_secret
    api_key = get_secret("ANTHROPIC_API_KEY")
    os.environ["ANTHROPIC_API_KEY"] = api_key  # ensure the SDK picks it up
except RuntimeError as e:
    print(f"Error: {e}")
    sys.exit(1)

from jarvis.agent import Agent  # noqa: E402 — import after secrets resolved


BANNER = """
  ╔══════════════════════════════════════╗
  ║            J A R V I S              ║
  ║   Just A Rather Very Intelligent    ║
  ║             System                  ║
  ╚══════════════════════════════════════╝
  Type your message. 'exit' to quit.
"""


def main() -> None:
    print(BANNER)
    agent = Agent()

    # First-run: ask for user's name if not stored
    user_name = agent.memory.get_fact("user_name")
    if not user_name:
        env_name = os.getenv("JARVIS_USER_NAME", "").strip()
        if env_name:
            agent.memory.set_fact("user_name", env_name)
            print(f"JARVIS: Good to have you back, {env_name}.\n")
        else:
            name = input("JARVIS: Before we begin — what shall I call you?\n> ").strip()
            if name:
                agent.memory.set_fact("user_name", name)
                print(f"\nJARVIS: Understood. Good to meet you, {name}.\n")

    print("JARVIS: Online and ready.\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\nJARVIS: Goodbye, sir.")
            break

        if not user_input:
            continue

        if user_input.lower() in ("exit", "quit", "goodbye", "bye"):
            print("JARVIS: Goodbye, sir.")
            break

        print("\nJARVIS: ", end="", flush=True)
        agent.ask(user_input)
        print()


if __name__ == "__main__":
    main()
