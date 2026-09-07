# For educational purposes; check the target site's ToS before use; you are responsible for compliance

# Train Ticket Reservation Bot (generic template)

A Playwright-based bot that logs in, polls a train search page for
availability in preferred classes, auto-fills passenger details, and
submits the booking — then hands the payment step to you.

## Why payment isn't automated end-to-end

Most real payment gateways require 3D-Secure / OTP confirmation on your
phone or bank app. There's no way to complete that without you, on any
legitimate site — so "fully autonomous" here means autonomous through
form submission, then an alert asking you to finish paying within a
time window. Anything claiming to fully automate past bank OTP either
isn't touching a real payment gateway or is doing something you don't
want to be involved in.

## Before you use this for real

1. **Read the target site's Terms of Service.** Many booking platforms
   (rail and otherwise) explicitly ban third-party automated booking
   and will suspend accounts that use it. This template doesn't make
   that decision for you.
2. **CAPTCHAs are not bypassed.** If one appears, the bot pauses and
   pings you to solve it manually — it doesn't attempt to defeat it.
3. **Selectors in `config.py` are placeholders.** Every real site has a
   different DOM. Open the target site in a browser, inspect the login
   form, search form, results list, and passenger form, and fill in the
   actual CSS selectors.

## Setup

```bash
pip install -r requirements.txt --break-system-packages
playwright install chromium

export TRAIN_SITE_USERNAME="your_username"
export TRAIN_SITE_PASSWORD="your_password"
# optional, for alerts:
export TELEGRAM_BOT_TOKEN="..."
export TELEGRAM_CHAT_ID="..."
```

Edit `config.py`: URLs, selectors, station names, travel date, preferred
classes, passenger list.

Run:

```bash
python bot.py
```

Leave `HEADLESS = False` in `config.py` while you're getting selectors
right, so you can see what's happening. Switch to `True` once it's
reliable.

## Files

- `config.py` — every site-specific value; edit this, not the others
- `bot.py` — login, polling, booking, and payment-handoff logic
- `notify.py` — Telegram alert helper (swap for email/SMS if preferred)
- `requirements.txt` — Python dependencies
