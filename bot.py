"""
Generic train ticket monitor + booking bot, built on Playwright.

Design intent
-------------
- "Fully autonomous" up through form submission.
- At payment, most gateways require 3D-Secure/OTP that only you can
  complete -- so the bot gets the order to the payment page, holds it,
  and pings you to finish paying within a timeout window. That's the
  realistic ceiling for unattended operation on sites with real payment
  security; treat any tool claiming to fully bypass that as either lying
  or doing something you don't want your name attached to.
- All selectors and parameters live in config.py. This file should not
  need site-specific edits.

Before running for real
------------------------
1. Read the target site's Terms of Service. Many booking platforms
   explicitly prohibit automated/bot bookings and will suspend accounts
   that violate this -- confirm you're not breaking a rule that costs
   you the account (or worse).
2. Fill in every selector in config.py by inspecting the real site
   (browser devtools -> Elements panel) since these are placeholders.
3. Install deps:  pip install playwright --break-system-packages
                   playwright install chromium
4. Set credentials via environment variables, not in code:
     export TRAIN_SITE_USERNAME=...
     export TRAIN_SITE_PASSWORD=...
     export TELEGRAM_BOT_TOKEN=...   (optional)
     export TELEGRAM_CHAT_ID=...     (optional)
"""

import logging
import random
import time
import os
from datetime import datetime, timedelta

from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

import config
import notify

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("train_bot")


class BookingFailed(Exception):
    pass


class TrainBot:
    def __init__(self):
        self._pw = None
        self.browser = None
        self.context = None
        self.page = None

    # ---------- lifecycle ----------

    def start(self):
        self._pw = sync_playwright().start()
        self.browser = self._pw.chromium.launch(headless=config.HEADLESS)

        storage_state = (
            config.STORAGE_STATE_PATH
            if os.path.exists(config.STORAGE_STATE_PATH)
            else None
        )
        self.context = self.browser.new_context(storage_state=storage_state)
        self.page = self.context.new_page()

    def stop(self):
        if self.context:
            self.context.storage_state(path=config.STORAGE_STATE_PATH)
        if self.browser:
            self.browser.close()
        if self._pw:
            self._pw.stop()

    # ---------- auth ----------

    def is_logged_in(self) -> bool:
        try:
            self.page.goto(config.BASE_URL, wait_until="domcontentloaded")
            self.page.wait_for_selector(
                config.LOGIN_SUCCESS_SELECTOR, timeout=5000
            )
            return True
        except PWTimeout:
            return False

    def login(self):
        if self.is_logged_in():
            logger.info("Existing session still valid; skipping login.")
            return

        logger.info("Logging in...")
        self.page.goto(config.LOGIN_URL, wait_until="domcontentloaded")
        self.page.fill(config.LOGIN_USERNAME_SELECTOR, config.USERNAME)
        self.page.fill(config.LOGIN_PASSWORD_SELECTOR, config.PASSWORD)

        self._check_for_captcha("login")

        self.page.click(config.LOGIN_SUBMIT_SELECTOR)
        self.page.wait_for_selector(config.LOGIN_SUCCESS_SELECTOR, timeout=15000)
        logger.info("Login successful.")

    # ---------- captcha handling (best-effort, not a bypass) ----------

    def _check_for_captcha(self, stage: str):
        """
        Pauses for manual solving if a CAPTCHA is detected. This bot does
        NOT attempt to solve or bypass CAPTCHAs -- that's an anti-abuse
        measure the site put there on purpose. If one appears, we stop
        and wait for you.
        """
        if self.page.query_selector(config.CAPTCHA_SELECTOR):
            notify.send(f"CAPTCHA detected at '{stage}'. Please solve it manually now.")
            logger.warning("CAPTCHA detected at '%s'. Waiting for manual resolution...", stage)
            # Wait until it disappears (you solved it) or timeout.
            try:
                self.page.wait_for_selector(
                    config.CAPTCHA_SELECTOR, state="detached", timeout=180000
                )
            except PWTimeout:
                raise BookingFailed(f"CAPTCHA at '{stage}' not resolved in time.")

    # ---------- search ----------

    def run_search(self):
        logger.info("Running search: %s -> %s on %s",
                     config.ORIGIN_STATION, config.DESTINATION_STATION, config.TRAVEL_DATE)
        self.page.goto(config.SEARCH_URL, wait_until="domcontentloaded")
        self.page.fill(config.SEARCH_FROM_SELECTOR, config.ORIGIN_STATION)
        self.page.fill(config.SEARCH_TO_SELECTOR, config.DESTINATION_STATION)
        self.page.fill(config.SEARCH_DATE_SELECTOR, config.TRAVEL_DATE)
        self.page.click(config.SEARCH_SUBMIT_SELECTOR)
        self.page.wait_for_selector(config.RESULT_ROW_SELECTOR, timeout=15000)

    def find_available_train(self):
        """
        Returns the Playwright element handle for the first result row
        matching a preferred class with availability, or None.
        """
        rows = self.page.query_selector_all(config.RESULT_ROW_SELECTOR)
        for row in rows:
            class_el = row.query_selector(config.RESULT_CLASS_NAME_SELECTOR)
            avail_el = row.query_selector(config.RESULT_AVAILABILITY_SELECTOR)
            if not class_el or not avail_el:
                continue

            class_name = class_el.inner_text().strip()
            availability_text = avail_el.inner_text().strip()

            if class_name not in config.PREFERRED_CLASSES:
                continue
            if self._parse_availability(availability_text) > 0:
                logger.info("Found availability: %s (%s)", class_name, availability_text)
                return row
        return None

    @staticmethod
    def _parse_availability(text: str) -> int:
        """
        Extract a seat count from arbitrary availability text.
        Adjust this to match the target site's actual wording
        (e.g. 'AVAILABLE 12', 'WL 4', 'Sold out').
        """
        digits = "".join(ch for ch in text if ch.isdigit())
        if "sold out" in text.lower() or "wl" in text.lower():
            return 0
        return int(digits) if digits else 0

    # ---------- booking ----------

    def book(self, row) -> bool:
        book_btn = row.query_selector(config.RESULT_BOOK_BUTTON_SELECTOR)
        if not book_btn:
            raise BookingFailed("Book button not found on matched row.")
        book_btn.click()

        self._check_for_captcha("passenger-details")

        self.page.wait_for_selector(config.PASSENGER_NAME_SELECTOR, timeout=15000)
        for i, passenger in enumerate(config.PASSENGERS):
            # Adjust indexing/selectors if the site uses per-passenger blocks
            self.page.fill(config.PASSENGER_NAME_SELECTOR, passenger["name"])
            self.page.fill(config.PASSENGER_AGE_SELECTOR, passenger["age"])
            self.page.select_option(config.PASSENGER_GENDER_SELECTOR, passenger["gender"])

        self._check_for_captcha("before-payment")

        self.page.click(config.CONTINUE_TO_PAYMENT_SELECTOR)
        self.page.wait_for_selector(config.PAYMENT_PAGE_SELECTOR, timeout=20000)
        logger.info("Reached payment page.")
        return True

    def wait_for_manual_payment(self) -> bool:
        """
        Hands off to you for the payment step (3D-Secure/OTP etc. can't be
        automated end-to-end on virtually any real gateway). Polls for the
        payment form to disappear (implying success/redirect) within the
        timeout, then notifies you either way.
        """
        notify.send(
            f"Seat held -- payment page ready. Complete payment within "
            f"{config.PAYMENT_CONFIRM_TIMEOUT_SECONDS // 60} minutes or it may be released."
        )
        deadline = time.time() + config.PAYMENT_CONFIRM_TIMEOUT_SECONDS
        while time.time() < deadline:
            if not self.page.query_selector(config.PAYMENT_PAGE_SELECTOR):
                notify.send("Payment page closed -- booking likely completed. Please verify.")
                return True
            time.sleep(5)

        notify.send("Payment window expired without confirmation. Seat may be released.")
        return False

    # ---------- main loop ----------

    def monitor_and_book(self):
        deadline = datetime.now() + timedelta(minutes=config.MAX_POLL_DURATION_MINUTES)
        attempt = 0

        while datetime.now() < deadline:
            attempt += 1
            logger.info("Poll attempt #%d", attempt)
            try:
                self.run_search()
                row = self.find_available_train()
                if row:
                    notify.send("Availability found -- attempting to book now.")
                    self.book(row)
                    self.wait_for_manual_payment()
                    return
            except BookingFailed as e:
                logger.error("Booking attempt failed: %s", e)
                notify.send(f"Booking attempt failed: {e}")
            except Exception as e:
                logger.exception("Unexpected error during poll: %s", e)

            sleep_for = config.POLL_INTERVAL_SECONDS + random.uniform(
                -config.POLL_JITTER_SECONDS, config.POLL_JITTER_SECONDS
            )
            sleep_for = max(5, sleep_for)
            logger.info("No booking made. Sleeping %.0fs before next poll.", sleep_for)
            time.sleep(sleep_for)

        notify.send("Monitoring window ended without finding/booking a seat.")


def main():
    bot = TrainBot()
    try:
        bot.start()
        bot.login()
        bot.monitor_and_book()
    finally:
        bot.stop()


if __name__ == "__main__":
    main()
