import os
import datetime
import requests
from http.server import BaseHTTPRequestHandler
import json

# Note: Vercel automatically loads environment variables

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

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        GITHUB_USERNAME = os.environ.get("GITHUB_USERNAME")
        GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
        GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
        WEBHOOK_URL = os.environ.get("WEBHOOK_URL")
        TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
        TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

        if not GITHUB_USERNAME:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": "GITHUB_USERNAME is not set"}).encode('utf-8'))
            return

        latest_push = get_latest_push_event(GITHUB_USERNAME, GITHUB_TOKEN)
        
        last_push_time = None
        if latest_push:
            created_at = latest_push["created_at"]
            last_push_time = datetime.datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%SZ")
            # Make it timezone-aware (UTC) to match now()
            last_push_time = last_push_time.replace(tzinfo=datetime.timezone.utc)

        now = datetime.datetime.now(datetime.timezone.utc)
        
        result_message = ""
        
        if last_push_time:
            time_diff = now - last_push_time
            hours_since_push = time_diff.total_seconds() / 3600
            result_message = f"Last push was {hours_since_push:.1f} hours ago at {last_push_time}."
            
            if hours_since_push > 24:
                message = f"⚠️ CodePulse Alert: Your coding pulse is flat — last push was {int(hours_since_push)}h ago."
                send_notification(WEBHOOK_URL, message)
                send_telegram_notification(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, message)
                result_message += " Alert sent."
            else:
                result_message += " Pulse is strong. Keep coding! 🚀"
        else:
            result_message = "No recent push events found."
            message = f"⚠️ CodePulse Alert: Your coding pulse is flat — no recent push events found."
            send_notification(WEBHOOK_URL, message)
            send_telegram_notification(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, message)
            result_message += " Alert sent."

        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({"status": "success", "message": result_message}).encode('utf-8'))
