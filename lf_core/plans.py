"""LeadsFind (LF) - Quota packs. Tool ke sources 100% free hain (owner ka zero cost),
user se packs becho = pure profit. 1 lead = 1 credit.
"""
PLANS = {
    "FREE": {
        "price_inr": 0,
        "total_leads": 5,
        "label": "FREE — signup pe 5 leads, one-time",
    },
    "OFFER": {
        "price_inr": 49,
        "total_leads": 60,
        "label": "🔥 SPECIAL OFFER Rs49 — 60 leads",
    },
    "STARTER": {
        "price_inr": 299,
        "total_leads": 300,
        "label": "STARTER Rs299 — 300 leads",
    },
    "PRO": {
        "price_inr": 699,
        "total_leads": 800,
        "label": "PRO Rs699 — 800 leads (POPULAR)",
    },
    "AGENCY": {
        "price_inr": 1499,
        "total_leads": 1800,
        "label": "AGENCY Rs1499 — 1800 leads",
    },
}

PAID_PLANS = ["OFFER", "STARTER", "PRO", "AGENCY"]


def get_plan(name: str) -> dict:
    return PLANS.get(name, PLANS["FREE"])
