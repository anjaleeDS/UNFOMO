"""
Telegram bot for UNFOMO.
Daily: top 5 articles + emergence alerts.
Weekly: narrative digest + charts (sent as images) + podcast audio.
Commands: /today, /week, /emerging, /player <name>, /cost
"""
import asyncio
import os
from telegram import Bot
from telegram.constants import ParseMode

from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
from db import repository as db

bot = Bot(token=TELEGRAM_BOT_TOKEN)

PLAYER_EMOJI = {
    "anthropic": "🟣",
    "openai":    "🔵",
    "google":    "🟢",
    "other":     "⚪",
}

SIG_EMOJI = {5: "🔴", 4: "🟠", 3: "🟡", 2: "⚪", 1: "⚫"}


def _significance_emoji(sig):
    return SIG_EMOJI.get(sig, "⚪")


def _ai_player_emoji(player):
    return PLAYER_EMOJI.get(player, "⚪")


def format_article(article, index: int) -> str:
    sig = article.get("significance") or 0
    player = article.get("ai_player") or "other"
    title = article.get("title", "Untitled")
    url = article.get("url", "")
    summary = article.get("summary_text") or ""
    now_what = article.get("now_what") or ""
    source = article.get("source_name") or ""

    lines = [
        f"{index}\\. {_significance_emoji(sig)} [{_escape_markdown(title)}]({url})",
        f"   {_ai_player_emoji(player)} `{player}` · {_escape_markdown(source)}",
    ]
    if summary:
        lines.append(f"   _{_escape_markdown(summary)}_")
    if now_what:
        lines.append(f"   → {_escape_markdown(now_what)}")
    return "\n".join(lines)


def _escape_markdown(text: str) -> str:
    """Escape MarkdownV2 special characters."""
    for ch in r"\_*[]()~`>#+-=|{}.!":
        text = text.replace(ch, f"\\{ch}")
    return text


async def send_daily(chat_id: str = TELEGRAM_CHAT_ID):
    articles = db.get_recent_articles(days=1, min_significance=3)[:5]
    emerging = db.get_emerging_terms()

    if not articles and not emerging:
        await bot.send_message(chat_id, "UNFOMO: quiet day — no significant updates.")
        return

    lines = ["*UNFOMO Daily* — top signals\n"]

    for i, a in enumerate(articles, 1):
        lines.append(format_article(dict(a), i))
        lines.append("")

    if emerging:
        lines.append("*🌱 Emerging signals:*")
        for t in emerging[:3]:
            lines.append(f"  `{t['term']}` — {t['count_48h']} mentions in 48h")

    await bot.send_message(
        chat_id,
        "\n".join(lines),
        parse_mode=ParseMode.MARKDOWN_V2,
        disable_web_page_preview=True,
    )


async def send_weekly(chat_id: str = TELEGRAM_CHAT_ID,
                      topic_chart_path: str = None,
                      velocity_chart_path: str = None):
    digest = db.get_latest_digest("weekly")
    if not digest:
        await bot.send_message(chat_id, "No weekly digest available yet.")
        return

    # Send text digest (split if > 4096 chars)
    content = f"*UNFOMO Weekly Digest*\n\n{digest['content']}"
    chunks = [content[i:i+4000] for i in range(0, len(content), 4000)]
    for chunk in chunks:
        await bot.send_message(chat_id, chunk, parse_mode=ParseMode.MARKDOWN_V2)

    # Send charts as images
    for path, caption in [
        (topic_chart_path,    "Topic trends this week"),
        (velocity_chart_path, "Player velocity: this week vs last"),
    ]:
        if path and os.path.exists(path):
            with open(path, "rb") as f:
                await bot.send_photo(chat_id, f, caption=caption)

    # Send podcast audio if available
    if digest.get("podcast_audio_url"):
        await bot.send_message(chat_id, f"🎙 Podcast: {digest['podcast_audio_url']}")


# ── Polling bot for commands ──────────────────────────────────────────────
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram import Update


async def cmd_today(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    articles = db.get_recent_articles(days=1, min_significance=3)[:5]
    if not articles:
        await update.message.reply_text("No articles yet today.")
        return
    lines = ["*Today\\'s top signals:*\n"]
    for i, a in enumerate(articles, 1):
        lines.append(format_article(dict(a), i))
        lines.append("")
    await update.message.reply_text(
        "\n".join(lines),
        parse_mode=ParseMode.MARKDOWN_V2,
        disable_web_page_preview=True,
    )


async def cmd_week(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    digest = db.get_latest_digest("weekly")
    if not digest:
        await update.message.reply_text("No weekly digest available yet.")
        return
    await update.message.reply_text(digest["content"][:4000])


async def cmd_emerging(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    terms = db.get_emerging_terms()
    if not terms:
        await update.message.reply_text("No emerging signals detected yet.")
        return
    lines = ["*🌱 Emerging signals:*\n"]
    for t in terms:
        lines.append(f"`{t['term']}` — first seen {t['first_seen_at'].strftime('%b %d')}, "
                     f"{t['count_48h']} mentions in 48h")
    await update.message.reply_text(
        "\n".join(lines),
        parse_mode=ParseMode.MARKDOWN_V2,
    )


async def cmd_player(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    args = ctx.args
    player = args[0].lower() if args else ""
    if player not in ("anthropic", "openai", "google", "other"):
        await update.message.reply_text("Usage: /player anthropic|openai|google|other")
        return
    articles = db.get_recent_articles(days=7, min_significance=3)
    filtered = [a for a in articles if a.get("ai_player") == player][:5]
    if not filtered:
        await update.message.reply_text(f"No recent items for {player}.")
        return
    lines = [f"*{_escape_markdown(player)} — last 7 days:*\n"]
    for i, a in enumerate(filtered, 1):
        lines.append(format_article(dict(a), i))
        lines.append("")
    await update.message.reply_text(
        "\n".join(lines),
        parse_mode=ParseMode.MARKDOWN_V2,
        disable_web_page_preview=True,
    )


async def cmd_cost(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    rows = db.get_cost_summary()
    total = sum(r["total_cost_usd"] for r in rows)
    lines = ["*API costs \\(last 30 days\\):*\n"]
    for r in rows:
        lines.append(f"`{r['provider']}/{r['model']}`: ${r['total_cost_usd']:.4f} "
                     f"\\({r['call_count']} calls\\)")
    lines.append(f"\n*Total: ${total:.4f}*")
    await update.message.reply_text("\n".join(lines), parse_mode=ParseMode.MARKDOWN_V2)


def run_bot():
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("today",    cmd_today))
    app.add_handler(CommandHandler("week",     cmd_week))
    app.add_handler(CommandHandler("emerging", cmd_emerging))
    app.add_handler(CommandHandler("player",   cmd_player))
    app.add_handler(CommandHandler("cost",     cmd_cost))
    print("UNFOMO bot polling...")
    app.run_polling()


if __name__ == "__main__":
    run_bot()
