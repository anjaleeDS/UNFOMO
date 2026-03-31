"""
Player velocity chart: grouped bar — this week vs last week per AI player.
"""
import os
import plotly.graph_objects as go

from db import repository as db

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "output")

PLAYER_COLORS = {
    "anthropic": "#c084fc",
    "openai":    "#60a5fa",
    "google":    "#34d399",
    "other":     "#94a3b8",
}


def build_velocity_chart(output_path: str = None) -> str | None:
    rows = db.get_player_velocity()
    if not rows:
        print("[velocity_chart] No velocity data available.")
        return None

    players    = [r["ai_player"] for r in rows]
    this_week  = [r["this_week"]  for r in rows]
    last_week  = [r["last_week"]  for r in rows]
    colors     = [PLAYER_COLORS.get(p, "#94a3b8") for p in players]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="This week",
        x=players, y=this_week,
        marker_color=colors,
        marker_opacity=1.0,
    ))
    fig.add_trace(go.Bar(
        name="Last week",
        x=players, y=last_week,
        marker_color=colors,
        marker_opacity=0.4,
    ))

    fig.update_layout(
        barmode="group",
        title=dict(text="Player Velocity: this week vs last", font=dict(color="#e8e8f0", size=14)),
        paper_bgcolor="#12121a",
        plot_bgcolor="#12121a",
        font=dict(color="#e8e8f0", family="Inter, sans-serif", size=12),
        xaxis=dict(color="#7a7a9a"),
        yaxis=dict(gridcolor="#2a2a3a", color="#7a7a9a", title="significant items"),
        legend=dict(bgcolor="rgba(0,0,0,0)"),
        margin=dict(t=48, r=20, b=40, l=48),
    )

    if output_path is None:
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        output_path = os.path.join(OUTPUT_DIR, "player_velocity.png")

    fig.write_image(output_path, width=700, height=360, scale=2)
    print(f"[velocity_chart] Saved → {output_path}")
    return output_path


if __name__ == "__main__":
    path = build_velocity_chart()
    print(f"Chart saved: {path}")
