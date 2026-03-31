"""
Weekly job: digest → charts → podcast → Telegram weekly package.
Run manually: python scheduler/weekly_job.py
Or triggered by APScheduler in scheduler/jobs.py (runs Sundays at 8am)
"""
import asyncio
from processing import digest_builder
from viz import topic_chart, velocity_chart
from podcast import tts


def run():
    print("\n══ UNFOMO Weekly Job ═════════════════════════════")

    print("\n[1/4] Building weekly digest...")
    digest = digest_builder.build_weekly_digest()
    if not digest:
        print("      No articles found — aborting weekly job.")
        return

    print("\n[2/4] Generating charts...")
    topic_path    = topic_chart.build_topic_chart(days=7)
    velocity_path = velocity_chart.build_velocity_chart()

    print("\n[3/4] Rendering podcast audio...")
    if digest.get("podcast_script"):
        audio_path = tts.render_podcast(digest["podcast_script"])
    else:
        audio_path = None
        print("      No podcast script in digest.")

    print("\n[4/4] Sending Telegram weekly package...")
    from bot.telegram_bot import send_weekly
    asyncio.run(send_weekly(
        topic_chart_path=topic_path,
        velocity_chart_path=velocity_path,
    ))

    print("\n══ Weekly job complete ═══════════════════════════\n")


if __name__ == "__main__":
    run()
