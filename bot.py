import json
import os
import random
import sys
from pathlib import Path

import requests

ROOT = Path(__file__).parent
PROBLEMS_FILE = ROOT / "problems.json"
LOG_FILE = ROOT / "sent_log.json"

DIFFICULTY_COLOR = {
    "Easy": 0x2ECC71,   # green
    "Medium": 0xF1C40F,  # yellow
    "Hard": 0xE74C3C,    # red
}


def load_json(path, default):
    if not path.exists():
        return default
    with open(path, "r") as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


def pick_problem(problems, sent_titles):
    unsent = [p for p in problems if p["title"] not in sent_titles]
    if not unsent:
        # Everyone's been sent — reset the cycle and start fresh.
        sent_titles = []
        unsent = problems
    return random.choice(unsent), sent_titles


def build_payload(problem):
    difficulty = problem.get("difficulty", "Unknown")
    color = DIFFICULTY_COLOR.get(difficulty, 0x7289DA)
    premium_note = "  (Premium)" if problem.get("premium") else ""

    embed = {
        "title": f" Today's problem: {problem['title']}{premium_note}",
        "url": problem["link"],
        "color": color,
        "fields": [
            {"name": "Difficulty", "value": difficulty, "inline": True},
            {"name": "Category", "value": problem.get("category", "—"), "inline": True},
        ],
    }
    return {"embeds": [embed]}


def send_to_discord(webhook_url, payload):
    resp = requests.post(webhook_url, json=payload, timeout=15)
    resp.raise_for_status()


def main():
    webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        print("ERROR: DISCORD_WEBHOOK_URL environment variable not set.", file=sys.stderr)
        sys.exit(1)

    problems = load_json(PROBLEMS_FILE, [])
    if not problems:
        print("ERROR: problems.json is empty or missing.", file=sys.stderr)
        sys.exit(1)

    sent_titles = load_json(LOG_FILE, [])

    problem, sent_titles = pick_problem(problems, sent_titles)
    payload = build_payload(problem)

    send_to_discord(webhook_url, payload)
    print(f"Sent: {problem['title']} ({problem.get('difficulty', '?')})")

    sent_titles.append(problem["title"])
    save_json(LOG_FILE, sent_titles)


if __name__ == "__main__":
    main()