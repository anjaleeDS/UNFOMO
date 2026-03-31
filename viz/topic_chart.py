"""
Topic popularity chart: line chart of top 10 topics over 7 days.
Outputs a PNG for Telegram + an interactive Plotly dict for the web dashboard.
"""
import os
import plotly.graph_objects as go
from collections import defaultdict

from db import repository as db

PLAYER_COLORS = {
    "anthropic": "#c084fc",
    "openai":    "#60a5fa",
    "google":    "#34d399",
    "other":     "#94a3b8",
}

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "output")


def _layout(title: str) -> dict:
    return dict(
        title=dict(text=title, font=dict(color="#e8e8f0", size=14)),
        paper_bgcolor="#12121a",
        plot_bgcolor="#12121a",
        font=dict(color="#e8e8f0", family="Inter, sans-serif", size=12),
        xaxis=dict(gridcolor="#2a2a3a", color="#7a7a9a", showgrid=True),
        yaxis=dict(gridcolor="#2a2a3a", color="#7a7a9a", showgrid=True,
                   title="mentions"),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=10)),
        margin=dict(t=48, r=20, b=40, l=48),
        hovermode="x unified",
    )


def build_topic_chart(days: int = 7, output_path: str = None) -> str | None:
    """
    Build topic trend line chart. Saves PNG to output_path.
    Returns path to saved PNG, or None if no data.
    """
    rows = db.get_topic_trends(days=days)
    if not rows:
        print("[topic_chart] No trend data available.")
        return None

    # Group by topic
    by_topic: dict[str, dict] = defaultdict(lambda: {"x": [], "y": []})
    for r in rows:
        by_topic[r["name"]]["x"].append(str(r["date"]))
        by_topic[r["name"]]["y"].append(r["count"])

    # Keep top 10 by total mentions
    ranked = sorted(by_topic.items(), key=lambda kv: sum(kv[1]["y"]), reverse=True)[:10]

    fig = go.Figure()
    for i, (topic, vals) in enumerate(ranked):
        fig.add_trace(go.Scatter(
            x=vals["x"], y=vals["y"],
            mode="lines+markers",
            name=topic,
            line=dict(width=2),
            marker=dict(size=5),
        ))

    fig.update_layout(**_layout(f"Topic Trends — last {days} days"))

    if output_path is None:
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        output_path = os.path.join(OUTPUT_DIR, "topic_trends.png")

    fig.write_image(output_path, width=900, height=400, scale=2)
    print(f"[topic_chart] Saved → {output_path}")
    return output_path


if __name__ == "__main__":
    path = build_topic_chart()
    print(f"Chart saved: {path}")
