"""
Simple notification helper. Defaults to Telegram (easiest to set up: talk to
@BotFather, create a bot, get the token, message it once, then use
https://api.telegram.org/bot<token>/getUpdates to find your chat_id).

Swap send() for email/SMS/Pushover/whatever you prefer -- the rest of the
bot only calls notify.send(text), so this is the one place to change.
"""

import logging
import urllib.request
import urllib.parse
import config

logger = logging.getLogger("train_bot.notify")


def send(text: str) -> None:
    logger.info("NOTIFY: %s", text)

    if not config.TELEGRAM_BOT_TOKEN or not config.TELEGRAM_CHAT_ID:
        logger.warning("Telegram not configured; notification only logged, not sent.")
        return

    url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage"
    data = urllib.parse.urlencode({
        "chat_id": config.TELEGRAM_CHAT_ID,
        "text": text,
    }).encode()

    try:
        with urllib.request.urlopen(url, data=data, timeout=10) as resp:
            resp.read()
    except Exception as e:
        logger.error("Failed to send Telegram notification: %s", e)
