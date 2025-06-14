import os
import json
import re
import requests
import logging
from flask import current_app as app
from helpers.db import User, KeyValueStore, db
from helpers.config import TELEGRAM_BOT_TOKEN

logger = logging.getLogger(__name__)

INTERNSHIP_LIST_URL = "https://raw.githubusercontent.com/vanshb03/Summer2026-Internships/dev/README.md"


def parse_latest_internship():
    response = requests.get(INTERNSHIP_LIST_URL)
    if not response.ok:
        logger.error("❌ Failed to fetch internship list")
        return None

    lines = response.text.splitlines()
    table_started = False
    internships = []

    for line in lines:
        if line.strip().startswith("| Company | Role | Location"):
            table_started = True
            continue

        if table_started and line.strip().startswith("|"):
            parts = [p.strip() for p in line.strip().split("|")[1:-1]]
            if len(parts) >= 4:
                company_raw = parts[0]
                role = parts[1]
                link_raw = parts[3]
                date = parts[4] if len(parts) > 4 else "N/A"

                # Extract company name
                match = re.search(r'\[(.*?)\]\((.*?)\)', company_raw)
                company = match.group(1) if match else company_raw

                # Extract application link
                url_match = re.search(r'href="(.*?)"', link_raw)
                apply_link = url_match.group(1) if url_match else "https://github.com/vanshb03/Summer2026-Internships"

                internships.append({
                    "company": company,
                    "role": role,
                    "url": apply_link,
                    "date": date
                })

    return internships[0] if internships else None


def load_last_internship():
    record = KeyValueStore.query.get("last_internship")
    if record:
        try:
            return json.loads(record.value)
        except json.JSONDecodeError:
            logger.warning("⚠️ Could not decode last_internship JSON")
            return None
    return None


def save_last_internship(internship):
    record = KeyValueStore.query.get("last_internship")
    if not record:
        record = KeyValueStore(key="last_internship")

    record.value = json.dumps({
        "company": internship["company"],
        "role": internship["role"],
        "date": internship["date"]
    })

    db.session.add(record)
    db.session.commit()


def send_internship_alert():
    logger.info("📤 Checking internship list...")

    try:
        with app.app_context():
            internship = parse_latest_internship()
            if not internship:
                logger.warning("⚠️ No internship found to send")
                return

            # Check if already sent
            last = load_last_internship()
            if last and (
                last["company"] == internship["company"] and
                last["role"] == internship["role"] and
                last["date"] == internship["date"]
            ):
                logger.info("⏩ No new internship to notify about.")
                return

            # Compose message
            message = f"""📢 *New Internship Alert!*  
                    🏢 *Company:* {internship['company']}  
                    💼 *Role:* {internship['role']}  
                    📅 *Posted:* {internship['date']}  
                    🔗 [Apply here]({internship['url']})"""

            users = User.query.filter(User.telegram_id.isnot(None)).all()
            if not users:
                logger.warning("⚠️ No users with telegram_id found")
                return

            for user in users:
                payload = {
                    "chat_id": user.telegram_id,
                    "text": message,
                    "parse_mode": "Markdown"
                }
                url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
                response = requests.post(url, json=payload)

                if response.ok:
                    logger.info(f"✅ Sent internship alert to user {user.id}")
                else:
                    logger.error(f"❌ Failed to send to {user.id}: {response.text}")

            save_last_internship(internship)

    except Exception as e:
        logger.error(f"❌ Error sending internship alert: {str(e)}")
        raise