"""
Logs every Claude/Gemini API call with token counts and USD cost.
Pricing as of March 2025 — update if Anthropic/Google change rates.
"""
from db import repository as db

# USD per million tokens
PRICING = {
    "claude-haiku-4-5-20251001":   {"in": 0.80,  "out": 4.00},
    "claude-sonnet-4-6":           {"in": 3.00,  "out": 15.00},
    "claude-opus-4-6":             {"in": 15.00, "out": 75.00},
    "gemini-2.5-flash-preview-04-17": {"in": 0.15, "out": 0.60},
    "gemini-2.5-pro":              {"in": 1.25,  "out": 5.00},
}

DEFAULT_MODEL = "claude-haiku-4-5-20251001"  # cheapest for daily summarization


def log(provider: str, model: str, tokens_in: int, tokens_out: int):
    rates = PRICING.get(model, {"in": 0.0, "out": 0.0})
    cost = (tokens_in / 1_000_000) * rates["in"] + (tokens_out / 1_000_000) * rates["out"]
    db.log_api_call(provider, model, tokens_in, tokens_out, round(cost, 6))
    return cost


def print_summary():
    rows = db.get_cost_summary()
    print("\n── API Cost Summary (last 30 days) ──")
    total = 0.0
    for r in rows:
        print(f"  {r['provider']} / {r['model']}: "
              f"{r['call_count']} calls | "
              f"${r['total_cost_usd']:.4f}")
        total += r['total_cost_usd']
    print(f"  TOTAL: ${total:.4f}\n")
