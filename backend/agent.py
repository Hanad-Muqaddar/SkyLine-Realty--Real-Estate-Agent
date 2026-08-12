"""
agent.py
--------
The "brain". It runs a tool-use loop with Claude:

  1. Send the conversation + tool schemas to the model.
  2. If the model asks to use a tool, run it and send the result back.
  3. Repeat until the model returns a normal text reply for the buyer.

This loop is what makes it an *agent* rather than a scripted chatbot: the model
decides on its own when to search listings, save the lead, or book a viewing.
"""

import json
import os

from dotenv import load_dotenv

from tools import TOOL_SCHEMAS, TOOL_HANDLERS

load_dotenv()

MODEL = os.getenv("MODEL", "claude-3-5-sonnet-latest")
DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() == "true"

# The system prompt is the agent's job description and personality.
SYSTEM_PROMPT = """You are "Ava", the AI assistant for Skyline Realty, a real estate agency.
You chat with website visitors who are potential buyers.

YOUR GOALS, in order:
1. Respond warmly and instantly, like a sharp human agent would.
2. Qualify the lead by naturally learning: which area they want, their budget,
   how many bedrooms, and their timeline to buy.
3. Use the search_listings tool to show 1-3 matching homes. Describe them briefly
   and appealingly (never dump raw JSON at the user).
4. Capture their name and a contact (phone or email) and call save_lead. This is
   critical - even if they don't book, we must keep the lead.
5. If they like a home, offer to book a viewing and use book_viewing.

STYLE RULES:
- Keep replies short and conversational (2-4 sentences). This is a chat widget.
- Ask ONE question at a time. Don't interrogate.
- Never invent listings, prices, or availability. Only mention what search_listings returns.
- If they're not ready, still try to get a name + contact so a human can follow up.
- You are an assistant, not a licensed agent. For legal, mortgage, or contract
  specifics, say a human agent from Skyline will confirm the details.
"""


# ---------------------------------------------------------------------------
# Real agent loop (uses the Anthropic API)
# ---------------------------------------------------------------------------
def _run_with_claude(messages):
    from anthropic import Anthropic

    client = Anthropic()  # reads ANTHROPIC_API_KEY from the environment
    working = list(messages)

    # Safety cap so a tool loop can never run forever.
    for _ in range(6):
        response = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            tools=TOOL_SCHEMAS,
            messages=working,
        )

        if response.stop_reason == "tool_use":
            # Record the assistant's tool request...
            working.append({"role": "assistant", "content": response.content})

            # ...run each requested tool and collect the results.
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    handler = TOOL_HANDLERS.get(block.name)
                    result = handler(**block.input) if handler else {"error": "unknown tool"}
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": json.dumps(result),
                    })
            working.append({"role": "user", "content": tool_results})
            continue  # loop again so the model can use the tool output

        # Normal text reply -> we're done. Save it to history so the model
        # remembers what it said on the next turn.
        text = "".join(b.text for b in response.content if b.type == "text")
        working.append({"role": "assistant", "content": text})
        return text, working

    return "Sorry, I got a little tangled up there — could you say that again?", working


# ---------------------------------------------------------------------------
# Demo fallback (no API key needed) - very simple, just to show the UI working
# ---------------------------------------------------------------------------
def _run_demo(messages):
    from tools import search_listings

    last = messages[-1]["content"]
    if isinstance(last, list):  # tool result turns, shouldn't happen in demo
        last = ""
    text = str(last).lower()
    words = set(text.replace("?", " ").replace(",", " ").split())

    if any(area in text for area in ["oakwood", "riverside", "city", "greenfield"]):
        found = search_listings(location=text)
        if found["listings"]:
            h = found["listings"][0]
            reply = (f"Great choice. For example, we have '{h['title']}' in {h['location']} "
                     f"— {h['beds']} bed, ${h['price']:,}. Want to book a viewing? "
                     f"Could I get your name and phone number?")
        else:
            reply = "Let me check what we have there. Could I get your name and contact number?"
    elif words & {"hi", "hello", "hey", "interested", "looking", "buy"}:
        reply = ("Hi! I'm Ava from Skyline Realty. I'd love to help you find a home. "
                 "Which area are you looking in, and what's your budget?")
    else:
        reply = ("Got it! Could I grab your name and a phone number or email so one of our "
                 "agents can send you matching listings?")

    messages.append({"role": "assistant", "content": reply})
    return reply, messages


# ---------------------------------------------------------------------------
# Public entry point used by the web server
# ---------------------------------------------------------------------------
def get_reply(messages):
    """messages: list of {"role": "user"/"assistant", "content": str}.
    Returns (reply_text, updated_messages)."""
    if DEMO_MODE or not os.getenv("ANTHROPIC_API_KEY"):
        return _run_demo(messages)
    return _run_with_claude(messages)
