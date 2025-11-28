import os
import sys
import datetime
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

GITHUB_USERNAME = os.getenv("GITHUB_USERNAME")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def get_latest_push_event(username, token):
    """Fetches the latest PushEvent for the given user."""
    url = f"https://api.github.com/users/{username}/events/public"
    headers = {
        "Accept": "application/vnd.github.v3+json",
    }
    if token:
        headers["Authorization"] = f"token {token}"

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        events = response.json()
        
        for event in events:
            if event["type"] == "PushEvent":
                return event
        return None
    except requests.exceptions.RequestException as e:
        print(f"Error fetching GitHub events: {e}")
        return None

def send_notification(webhook_url, message):
    """Sends a notification to the specified webhook URL."""
    if not webhook_url:
        print("No webhook URL provided. Skipping notification.")
        return

    payload = {"content": message}
    try:
        response = requests.post(webhook_url, json=payload)
        response.raise_for_status()
        print("Notification sent successfully.")
    except requests.exceptions.RequestException as e:
        print(f"Error sending notification: {e}")

def send_telegram_notification(bot_token, chat_id, message):
    """Sends a notification to Telegram."""
    if not bot_token or not chat_id:
        print("No Telegram credentials provided. Skipping Telegram notification.")
        return

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message
    }
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        print("Telegram notification sent successfully.")
    except requests.exceptions.RequestException as e:
        print(f"Error sending Telegram notification: {e}")

def main():
    if not GITHUB_USERNAME:
        print("Error: GITHUB_USERNAME is not set.")
        sys.exit(1)

    print(f"Checking GitHub activity for user: {GITHUB_USERNAME}...")
    
    latest_push = get_latest_push_event(GITHUB_USERNAME, GITHUB_TOKEN)
    
    if not latest_push:
        print("No PushEvents found in recent public activity.")
        # Depending on logic, might want to alert if NO history found at all, 
        # but usually we care about *recent* history. 
        # If no events returned, it might mean no activity in the 90-day window 
        # or just no public push events. 
        # For safety, let's assume flatline if absolutely nothing is returned?
        # Or maybe just log it. Let's treat "no events" as "no recent push".
        last_push_time = None
    else:
        created_at = latest_push["created_at"]
        # GitHub returns UTC time in ISO 8601 format: YYYY-MM-DDTHH:MM:SSZ
        last_push_time = datetime.datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%SZ")
        last_push_time = last_push_time.replace(tzinfo=datetime.timezone.utc)

    now = datetime.datetime.now(datetime.timezone.utc)
    
    if last_push_time:
        time_diff = now - last_push_time
        hours_since_push = time_diff.total_seconds() / 3600
        print(f"Last push was {hours_since_push:.1f} hours ago at {last_push_time} UTC.")
        
        if hours_since_push > 24:
            message = f"⚠️ CodePulse Alert: Your coding pulse is flat — last push was {int(hours_since_push)}h ago."
            send_notification(WEBHOOK_URL, message)
            send_telegram_notification(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, message)
        else:
            print("Pulse is strong. Keep coding! 🚀")
    else:
        # No recent push event found
        print("No recent push events found.")
        message = f"⚠️ CodePulse Alert: Your coding pulse is flat — no recent push events found."
        send_notification(WEBHOOK_URL, message)
        send_telegram_notification(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, message)

if __name__ == "__main__":
    main()
