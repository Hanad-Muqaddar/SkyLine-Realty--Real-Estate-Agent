# Skyline Realty — Instant Lead-Response AI Agent

A working demo of an AI agent that replies to real-estate website leads in
seconds, qualifies them, shows matching homes, captures their contact details,
and books viewings — 24/7. Built as a portfolio piece to show clients.

---

## What it actually does (the pitch)

**The problem:** Real estate businesses pay for leads (Zillow, ads, portals) but
lose them on *response speed*. A buyer inquires at 11pm, the agent replies at
9am, and by then the buyer already booked with a competitor. Speed-to-lead is
the single biggest lever, and humans can't be awake 24/7.

**The agent:** The moment a visitor opens the website chat, "Ava" responds
instantly, asks smart qualifying questions (area, budget, bedrooms, timeline),
pulls matching listings, saves the lead for the human agent, and books a viewing.

This is a real **AI agent, not a scripted bot** — the language model decides on
its own when to search listings, save a lead, or book a viewing (that's the
`tools`). That distinction is what makes clients say "yes".

---

## How it's built

```
real-estate-agent/
├── backend/
│   ├── app.py        FastAPI server: serves the site + /chat endpoint
│   ├── agent.py      The brain: Claude tool-use loop + system prompt
│   └── tools.py      The hands: search_listings, save_lead, book_viewing
├── frontend/
│   └── index.html    Demo real-estate site with a chat widget
├── data/
│   ├── listings.json  Mock property inventory
│   ├── leads.json     (auto-created) captured leads land here
│   └── bookings.json  (auto-created) booked viewings land here
├── requirements.txt
└── .env.example
```

**Flow:** browser widget → `POST /chat` → `agent.py` runs Claude with the three
tools → tools read/write the JSON files → reply goes back to the widget.

For a real client you only change the *bodies* of the functions in `tools.py`
(point them at their CRM, listings/MLS API, and Google Calendar). The agent and
UI stay the same.

---

## Run it (about 5 minutes)

You need Python 3.9+.

```bash
# 1. From inside the real-estate-agent/ folder, install dependencies
pip install -r requirements.txt

# 2. Set up your key
cp .env.example .env
#    then open .env and paste your Anthropic API key
#    (get one at https://console.anthropic.com)

# 3. Start the server (run this from the backend/ folder)
cd backend
uvicorn app:app --reload

# 4. Open the demo
#    http://127.0.0.1:8000
```

Click the 💬 bubble bottom-right and start chatting.

### No API key yet? Quick visual demo
Set `DEMO_MODE=true` in `.env` (or just leave the key blank). The widget will
work with simple scripted replies so you can show the UI. For the real,
impressive AI conversation, use an API key — the scripted mode is only a stopgap.

---

## Demo script for a client meeting

Run this live. It lands harder than any slide.

1. **Set the scene.** "This is your website at midnight. A buyer just landed."
2. Type: *"Hi, I'm looking for a 3 bedroom house in Oakwood under 450k."*
   → Ava replies instantly with a real matching listing.
3. Type: *"Looks good, can I see it?"*
   → Ava asks for name + phone, then books the viewing.
4. Give a fake name/number, then a day/time.
5. **The reveal:** open `data/leads.json` and `data/bookings.json` and show the
   captured lead and booking. Say: *"That lead is now in your system with zero
   human effort, at 3am, while your competitor's phone went to voicemail."*

### Objection handling
- *"Is it just a chatbot?"* → No. It uses tools to take real actions (search,
  save, book). Show `tools.py`.
- *"Will it give wrong legal/price info?"* → The system prompt forbids inventing
  data and defers legal/mortgage questions to a human. Show the prompt in
  `agent.py`.
- *"Can it connect to my CRM/calendar?"* → Yes — that's a `tools.py` change.

---

## What to build next (upsell path)
- Swap mock tools for the client's real CRM (HubSpot/Follow Up Boss) + calendar.
- Add SMS/WhatsApp so it replies on the channel the lead used.
- Add a nightly summary email of all captured leads.
- Multi-language replies for international buyers.

---

*Note: "Ava" is an assistant, not a licensed agent. Keep a human in the loop for
contracts, mortgage, and legal specifics — and tell clients that; it builds trust.*
