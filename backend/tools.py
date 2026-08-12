"""
tools.py
--------
These are the "hands" of the AI agent. The language model decides WHEN to call
them; this file decides WHAT they do. For the demo they read/write local JSON
files, but in a real client deployment you'd swap the bodies to hit their CRM,
MLS/listings API, and calendar — the interface the agent sees stays the same.
"""

import json
import os
from datetime import datetime

# ---- File locations -------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
LISTINGS_FILE = os.path.join(DATA_DIR, "listings.json")
LEADS_FILE = os.path.join(DATA_DIR, "leads.json")
BOOKINGS_FILE = os.path.join(DATA_DIR, "bookings.json")


def _load_json(path, default):
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _append_json(path, record):
    records = _load_json(path, [])
    records.append(record)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2)


# ---- Tool 1: search listings ---------------------------------------------
def search_listings(location=None, max_price=None, min_beds=None, property_type=None):
    """Return listings matching the buyer's criteria. All filters optional."""
    listings = _load_json(LISTINGS_FILE, [])
    results = []
    for home in listings:
        if home.get("status") != "available":
            continue
        if location and location.lower() not in home["location"].lower():
            continue
        if max_price and home["price"] > max_price:
            continue
        if min_beds and home["beds"] < min_beds:
            continue
        if property_type and property_type.lower() != home["type"].lower():
            continue
        results.append(home)

    # Sort cheapest first so the agent can lead with affordable options.
    results.sort(key=lambda h: h["price"])
    return {"count": len(results), "listings": results[:5]}


# ---- Tool 2: save the lead -----------------------------------------------
def save_lead(name=None, contact=None, budget=None, timeline=None,
              preferred_area=None, notes=None):
    """Store the captured lead so the human agent can follow up. This is the
    real business value: even if the buyer leaves, you keep the lead."""
    record = {
        "captured_at": datetime.now().isoformat(timespec="seconds"),
        "name": name,
        "contact": contact,
        "budget": budget,
        "timeline": timeline,
        "preferred_area": preferred_area,
        "notes": notes,
    }
    _append_json(LEADS_FILE, record)
    return {"ok": True, "message": f"Lead saved for {name or 'unknown'}."}


# ---- Tool 3: book a viewing ----------------------------------------------
def book_viewing(listing_id=None, name=None, contact=None, datetime_slot=None):
    """Book a property viewing. In production this writes to the agent's real
    calendar (Google Calendar, Calendly, etc.)."""
    listings = _load_json(LISTINGS_FILE, [])
    match = next((h for h in listings if h["id"] == listing_id), None)
    if not match:
        return {"ok": False, "message": f"Listing {listing_id} not found."}

    booking = {
        "booked_at": datetime.now().isoformat(timespec="seconds"),
        "listing_id": listing_id,
        "listing_title": match["title"],
        "name": name,
        "contact": contact,
        "datetime_slot": datetime_slot,
    }
    _append_json(BOOKINGS_FILE, booking)
    return {
        "ok": True,
        "message": f"Viewing booked for {match['title']} on {datetime_slot}.",
        "booking": booking,
    }


# ---- Schemas the model sees (Anthropic tool-use format) -------------------
TOOL_SCHEMAS = [
    {
        "name": "search_listings",
        "description": "Search available property listings. Use this whenever the "
                       "buyer describes what they want (area, budget, bedrooms, type).",
        "input_schema": {
            "type": "object",
            "properties": {
                "location": {"type": "string", "description": "Neighborhood or area name"},
                "max_price": {"type": "number", "description": "Maximum budget in dollars"},
                "min_beds": {"type": "integer", "description": "Minimum number of bedrooms"},
                "property_type": {
                    "type": "string",
                    "description": "house, apartment, condo, or townhouse",
                },
            },
        },
    },
    {
        "name": "save_lead",
        "description": "Save the buyer's contact details and preferences so a human "
                       "agent can follow up. Call this as soon as you have a name and a "
                       "way to contact them (phone or email).",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "contact": {"type": "string", "description": "Phone number or email"},
                "budget": {"type": "string"},
                "timeline": {"type": "string", "description": "e.g. 'within 3 months'"},
                "preferred_area": {"type": "string"},
                "notes": {"type": "string", "description": "Anything else useful"},
            },
            "required": ["name", "contact"],
        },
    },
    {
        "name": "book_viewing",
        "description": "Book a viewing for a specific listing once the buyer picks one "
                       "and gives a day/time.",
        "input_schema": {
            "type": "object",
            "properties": {
                "listing_id": {"type": "string", "description": "e.g. SR-101"},
                "name": {"type": "string"},
                "contact": {"type": "string"},
                "datetime_slot": {"type": "string", "description": "Requested day and time"},
            },
            "required": ["listing_id", "name", "contact", "datetime_slot"],
        },
    },
]

# Map tool names -> python functions
TOOL_HANDLERS = {
    "search_listings": search_listings,
    "save_lead": save_lead,
    "book_viewing": book_viewing,
}
