# CodePulse

CodePulse is a simple tool to keep your coding streak alive. It checks your GitHub activity daily and sends you a notification on Telegram if you haven't pushed any code in the last 24 hours.

## Features

-   **Daily Checks**: Runs automatically via GitHub Actions or Vercel Cron.
-   **Telegram Notifications**: Sends a friendly reminder (or a stern warning!) to your Telegram chat.
-   **Configurable**: Set your own thresholds and messages.

## Setup

1.  Clone the repo.
2.  Copy `.env.example` to `.env` and fill in your credentials:
    -   `GITHUB_USERNAME`
    -   `TELEGRAM_BOT_TOKEN`
    -   `TELEGRAM_CHAT_ID`
3.  Run locally:
    ```bash
    pip install -r requirements.txt
    python codepulse.py
    ```
