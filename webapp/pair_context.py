import requests
import json
from pathlib import Path
from broker_data import get_total_exposure_by_asset, get_drawdown
from graph_loader import load_graph_data
from sentiment_agent import get_live_sentiment

GRAPH_DIR = Path(__file__).resolve().parent.parent / "graph"

def get_pair_context(pair):
    pair_lower = pair.lower()
    graph = load_graph_data()
    exposure = get_total_exposure_by_asset()
    drawdown = get_drawdown()

    # Load references
    context = {
        "pair": pair.upper(),
        "drawdown": drawdown,
        "exposure": exposure.get(pair.upper(), 0.0),
        "hedge_only": False,
        "topdown_refs": [],
        "strategy_flags": [],
        "assistant_tip": ""
    }

    # Get sentiment analysis
    sentiment_data = get_live_sentiment(pair)
    context.update(sentiment_data)

    # Search for hedge-only or bias-related flags
    for concept in graph["concepts"]:
        if "hedge-only" in concept["name"].lower() and pair_lower in concept["description"].lower():
            context["hedge_only"] = True
            context["strategy_flags"].append("⚠️ In hedge-only zone")
        if "bias" in concept["name"].lower() and "structure" in concept["description"].lower():
            context["strategy_flags"].append("🧠 Watch for structure break before confirming bias")

    # Check for matching edges
    for edge in graph["edges"]:
        if pair.upper() in edge.get("to", "").upper():
            context["topdown_refs"].append(edge["to"])

    # Final assistant tip
    if context["drawdown"] > 3.0:
        context["assistant_tip"] = "🚨 Drawdown > 3% — consider hedge or DCT response."
    elif context["hedge_only"]:
        context["assistant_tip"] = "⚠️ You're in a hedge-only zone. Monitor for invalidation or hedge reaction."
    else:
        context["assistant_tip"] = "✅ No major risk flags. Continue monitoring structure + bias alignment."

    return context 