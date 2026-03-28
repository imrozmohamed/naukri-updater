"""
Naukri Profile Auto-Updater
Automatically updates your Naukri profile 3 times daily to stay visible to recruiters.
"""

import os
import time
import logging
import smtplib
import schedule
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

# ── Load environment variables ──────────────────────────────────────────────
load_dotenv()


NAUKRI_EMAIL    = os.getenv("NAUKRI_EMAIL")
NAUKRI_PASSWORD = os.getenv("NAUKRI_PASSWORD")
HEADLESS        = os.getenv("HEADLESS", "false").lower() == "true"

# Email alert config (optional)
ALERT_EMAIL         = os.getenv("ALERT_EMAIL")          # your Gmail
ALERT_EMAIL_PASSWORD= os.getenv("ALERT_EMAIL_PASSWORD") # Gmail app password
NOTIFY_EMAIL        = os.getenv("NOTIFY_EMAIL")         # where to send alerts (can be same)

# Schedule times (24-hr format)
SCHEDULE_TIMES = ["09:00", "13:00", "19:00"]

# ── Logging setup ────────────────────────────────────────────────────────────
LOG_FILE = "naukri_updater.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  [%(levelname)s]  %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
log = logging.getLogger(__name__)


# ── Email alert ──────────────────────────────────────────────────────────────
def send_alert(subject: str, body: str):
    """Send email alert if credentials are configured."""
    if not all([ALERT_EMAIL, ALERT_EMAIL_PASSWORD, NOTIFY_EMAIL]):
        return
    try:
        msg = MIMEMultipart()
        msg["From"]    = ALERT_EMAIL
        msg["To"]      = NOTIFY_EMAIL
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(ALERT_EMAIL, ALERT_EMAIL_PASSWORD)
            server.sendmail(ALERT_EMAIL, NOTIFY_EMAIL, msg.as_string())
        log.info("Alert email sent to %s", NOTIFY_EMAIL)
    except Exception as e:
        log.warning("Could not send alert email: %s", e)


# ── Browser setup ────────────────────────────────────────────────────────────
def get_driver() -> webdriver.Chrome:
    opts = Options()
    if HEADLESS:
        opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    opts.add_experimental_option("useAutomationExtension", False)
    opts.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
    driver = webdriver.Chrome(options=opts)
    driver.execute_script(
        "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    )
    driver.set_page_load_timeout(30)
    return driver


# ── Core update logic ────────────────────────────────────────────────────────
def login(driver: webdriver.Chrome, wait: WebDriverWait) -> bool:
    """Log in to Naukri. Returns True on success."""
    log.info("Navigating to Naukri login page…")
    driver.get("https://www.naukri.com/nlogin/login")
    time.sleep(3)

    try:
        email_field = wait.until(EC.presence_of_element_located((By.ID, "usernameField")))
        email_field.clear()
        email_field.send_keys(NAUKRI_EMAIL)
        time.sleep(0.5)

        pwd_field = driver.find_element(By.ID, "passwordField")
        pwd_field.clear()
        pwd_field.send_keys(NAUKRI_PASSWORD)
        time.sleep(0.5)

        # Click login button
        login_btn = driver.find_element(By.XPATH, "//button[@type='submit']")
        login_btn.click()
        time.sleep(4)

        # Verify login succeeded by checking URL or a post-login element
        if "nlogin" not in driver.current_url:
            log.info("Login successful. Current URL: %s", driver.current_url)
            return True
        else:
            log.error("Login may have failed. Still on: %s", driver.current_url)
            return False

    except TimeoutException:
        log.error("Login form not found within timeout.")
        return False


def update_profile(driver: webdriver.Chrome, wait: WebDriverWait) -> bool:
    """
    Navigate to profile and make a tiny invisible edit to 'resume headline'
    to trigger a profile-active timestamp update on Naukri.
    Returns True on success.
    """
    log.info("Navigating to profile page…")
    driver.get("https://www.naukri.com/mnjuser/profile?id=&altresid")
    time.sleep(4)

    try:
        # ── Strategy 1: Edit resume headline ────────────────────────────────
        # Click the edit (pencil) icon near the headline section
        edit_btns = driver.find_elements(
            By.XPATH,
            "//span[contains(@class,'edit') or contains(@class,'pencil') or @title='Edit']"
        )
        clicked = False
        for btn in edit_btns[:3]:
            try:
                driver.execute_script("arguments[0].click();", btn)
                time.sleep(2)
                clicked = True
                break
            except Exception:
                continue

        if not clicked:
            # Fallback: directly open the profile update overlay
            driver.get(
                "https://www.naukri.com/mnjuser/profile?id=&altresid&action=profilesummary"
            )
            time.sleep(3)

        # Find any text area or input that's currently active/focused
        try:
            active_input = wait.until(
                EC.presence_of_element_located(
                    (By.XPATH, "//textarea | //input[@type='text']")
                )
            )
            # Add an invisible trailing space and remove it — net-zero change
            current_val = active_input.get_attribute("value") or ""
            active_input.send_keys(Keys.END)
            active_input.send_keys(" ")   # add space
            time.sleep(0.5)
            active_input.send_keys(Keys.BACK_SPACE)  # remove space
            time.sleep(0.5)
        except Exception:
            log.warning("Could not interact with input field; attempting save anyway.")

        # ── Save / submit ────────────────────────────────────────────────────
        save_xpaths = [
            "//button[contains(translate(text(),'SAVE','save'),'save')]",
            "//button[@type='submit']",
            "//input[@type='submit']",
        ]
        saved = False
        for xpath in save_xpaths:
            btns = driver.find_elements(By.XPATH, xpath)
            for btn in btns:
                try:
                    if btn.is_displayed() and btn.is_enabled():
                        driver.execute_script("arguments[0].click();", btn)
                        time.sleep(2)
                        saved = True
                        log.info("Save button clicked.")
                        break
                except Exception:
                    continue
            if saved:
                break

        if not saved:
            log.warning("Save button not found; profile visit itself may count as activity.")

        log.info("Profile update step completed.")
        return True

    except Exception as e:
        log.error("Error during profile update: %s", e)
        return False


# ── Main job ─────────────────────────────────────────────────────────────────
def run_update():
    """Full update cycle: login → update → quit."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log.info("=" * 55)
    log.info("Starting Naukri update — %s", now)
    log.info("=" * 55)

    if not NAUKRI_EMAIL or not NAUKRI_PASSWORD:
        log.error("NAUKRI_EMAIL or NAUKRI_PASSWORD not set in .env!")
        return

    driver = None
    try:
        driver = get_driver()
        wait   = WebDriverWait(driver, 20)

        if not login(driver, wait):
            msg = f"Naukri login failed at {now}"
            log.error(msg)
            send_alert("❌ Naukri Updater — Login Failed", msg)
            return

        time.sleep(2)

        if update_profile(driver, wait):
            log.info("✅  Profile updated successfully at %s", now)
            send_alert(
                "✅ Naukri Profile Updated",
                f"Your Naukri profile was successfully updated at {now}."
            )
        else:
            msg = f"Profile update step failed at {now}"
            log.warning(msg)
            send_alert("⚠️ Naukri Updater — Update Step Failed", msg)

    except WebDriverException as e:
        msg = f"Browser/WebDriver error at {now}: {e}"
        log.error(msg)
        send_alert("❌ Naukri Updater — WebDriver Error", msg)

    except Exception as e:
        msg = f"Unexpected error at {now}: {e}"
        log.error(msg)
        send_alert("❌ Naukri Updater — Unexpected Error", msg)

    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass
        log.info("Browser closed.\n")


# ── Scheduler ────────────────────────────────────────────────────────────────
def main():
    log.info("Naukri Auto-Updater started.")
    log.info("Scheduled times: %s", ", ".join(SCHEDULE_TIMES))

    for t in SCHEDULE_TIMES:
        schedule.every().day.at(t).do(run_update)
        log.info("Scheduled update at %s", t)

    # Run once immediately on start (optional — comment out if not wanted)
    log.info("Running initial update now…")
    run_update()

    log.info("Scheduler running. Press Ctrl+C to stop.")
    while True:
        schedule.run_pending()
        time.sleep(30)


if __name__ == "__main__":
    main()
