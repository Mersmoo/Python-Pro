"""
Site-specific configuration for the train ticket bot.

Fill these in for whichever booking site you're targeting.
Everything selector-related lives here so bot.py never needs editing
when you switch sites.
"""

# ---- Site URLs ----
BASE_URL = "https://example-railway-site.com"
LOGIN_URL = f"{BASE_URL}/login"
SEARCH_URL = f"{BASE_URL}/search"

# ---- Credentials (better: load from environment variables, not hardcoded) ----
import os
USERNAME = os.environ.get("TRAIN_SITE_USERNAME", "")
PASSWORD = os.environ.get("TRAIN_SITE_PASSWORD", "")

# ---- Login page selectors ----
LOGIN_USERNAME_SELECTOR = "#username"
LOGIN_PASSWORD_SELECTOR = "#password"
LOGIN_SUBMIT_SELECTOR = "button[type='submit']"
LOGIN_SUCCESS_SELECTOR = ".account-menu"  # something only present after login

# ---- Search form selectors ----
SEARCH_FROM_SELECTOR = "#origin-station"
SEARCH_TO_SELECTOR = "#destination-station"
SEARCH_DATE_SELECTOR = "#travel-date"
SEARCH_SUBMIT_SELECTOR = "#search-button"

# ---- Search parameters ----
ORIGIN_STATION = "CityA"
DESTINATION_STATION = "CityB"
TRAVEL_DATE = "2026-10-01"  # format depends on the site's date picker
PREFERRED_CLASSES = ["Sleeper", "AC 3-Tier"]  # in priority order

# ---- Results page selectors ----
# CSS selector for each train "row" in the results list
RESULT_ROW_SELECTOR = ".train-result-row"
# Within a row: selector for the seat-availability text, and the class name
RESULT_AVAILABILITY_SELECTOR = ".seat-count"
RESULT_CLASS_NAME_SELECTOR = ".class-name"
RESULT_BOOK_BUTTON_SELECTOR = ".book-now-btn"

# ---- Passenger details form ----
PASSENGER_NAME_SELECTOR = "#passenger-name"
PASSENGER_AGE_SELECTOR = "#passenger-age"
PASSENGER_GENDER_SELECTOR = "#passenger-gender"
PASSENGERS = [
    {"name": "Jane Doe", "age": "30", "gender": "F"},
]

CONTINUE_TO_PAYMENT_SELECTOR = "#proceed-to-payment"

# ---- CAPTCHA detection (best-effort) ----
CAPTCHA_SELECTOR = "iframe[src*='captcha'], .g-recaptcha, .captcha-container"

# ---- Payment page ----
PAYMENT_PAGE_SELECTOR = "#payment-form"

# ---- Polling behavior ----
POLL_INTERVAL_SECONDS = 45
POLL_JITTER_SECONDS = 15  # random +/- added to interval to avoid a robotic pattern
MAX_POLL_DURATION_MINUTES = 180

# ---- Notifications (Telegram example; swap for email/SMS as you like) ----
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

# How long to wait for the user to confirm/complete payment manually
# before the bot gives up and releases the held seat.
PAYMENT_CONFIRM_TIMEOUT_SECONDS = 300

# ---- Browser behavior ----
HEADLESS = False  # keep visible while you're tuning selectors; True once stable
STORAGE_STATE_PATH = "session_state.json"  # persisted cookies/session
