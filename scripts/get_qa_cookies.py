#!/usr/bin/env python3
"""
Script to semi-automatically extract Azure App Proxy cookies after manual login.
Opens a browser, waits for user to log in manually, then extracts
and prints Azure App Proxy cookies in a usable Python format.
"""

import logging
import traceback
from pathlib import Path
import sys
import os
import json # To format the output nicely
import time # For timing

# Setup basic logging
# Create logs directory if it doesn't exist
log_dir = Path(__file__).parent / "logs_cookie_extractor"
log_dir.mkdir(exist_ok=True)
log_file = log_dir / f"cookie_extractor_{time.strftime('%Y%m%d_%H%M%S')}.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler() # Also print logs to console
    ]
)

# Try importing Playwright
try:
    from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext
except ImportError:
    logging.error("Error: Playwright library not found.")
    logging.error("Please install it using: pip install playwright")
    logging.error("Then install browser binaries: playwright install")
    sys.exit(1)

logger = logging.getLogger(__name__)

# --- Main Function ---
def extract_cookies_after_manual_login(playwright: sync_playwright):
    """
    Opens a browser, waits for user to log in manually, then extracts
    and prints Azure App Proxy cookies.
    """
    browser: Browser | None = None
    context: BrowserContext | None = None
    page: Page | None = None
    status = "Failed"

    initial_url = "https://hashkalqa.israelpost.co.il/transactions-page/" # Start here, will redirect
    expected_domain = "hashkalqa.israelpost.co.il" # Domain for filtering cookies

    # Define a common User-Agent string
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"

    try:
        logger.info("Launching headed Chromium browser...")
        browser = playwright.chromium.launch(headless=False, slow_mo=50)

        logger.info("Creating browser context...")
        context = browser.new_context(
            viewport={"width": 1400, "height": 900}, # Slightly smaller viewport
            locale="he-IL",
            user_agent=user_agent,
            accept_downloads=True,
            # ignore_https_errors=True # Uncomment ONLY if facing certificate issues in QA
        )

        # Add listener for page errors
        def handle_page_error(error):
            logger.error(f"Browser Page Error: {error}")
        page.on("pageerror", handle_page_error)


        page = context.new_page()
        logger.info(f"Navigating to initial URL to trigger login: {initial_url}")
        try:
            # Wait only for DOM content, not full load, as redirects might happen
            page.goto(initial_url, wait_until='domcontentloaded', timeout=60000)
            logger.info(f"Initial navigation attempted. Current URL: {page.url}")
        except Exception as initial_nav_err:
            # It's okay if initial navigation times out or redirects quickly
             logger.warning(f"Initial navigation might have redirected quickly or failed: {initial_nav_err}")
             logger.info(f"Current URL after initial attempt: {page.url}")
             logger.info("Proceeding to wait for manual login.")


        # --- Wait for Manual Login ---
        print("\n" + "*" * 70)
        print("ACTION REQUIRED")
        print("*" * 70)
        print("A browser window has been opened.")
        print("\nPlease complete the login process MANUALLY in that window.")
        print("\nUse Windows Hello, PIN, or whatever method is required.")
        print("\nEnsure you are fully logged in and have reached the target page:")
        print(f"===> '{initial_url}' <===")
        print("(Even if the initial URL redirected, finish login until you see the transactions page)")
        print("*" * 70)
        input("======> Press Enter here AFTER you have logged in and reached the target page <======")
        # --- User Confirmed Login ---

        logger.info("User pressed Enter. Assuming login is complete. Extracting cookies...")

        # Optional: Verify the URL is the target page now
        current_url = page.url
        logger.info(f"Current URL after manual login: {current_url}")
        if expected_domain not in current_url:
            logger.warning(f"URL '{current_url}' does not seem to be on the expected domain '{expected_domain}'. Cookies might be incorrect.")
            # Continue anyway, but warn the user

        # Get all cookies from the current context
        # Filter by the expected domain to be more specific
        all_cookies = context.cookies(urls=[f"https://{expected_domain}"])
        logger.info(f"Total cookies found for domain '{expected_domain}': {len(all_cookies)}")

        # Filter for Azure App Proxy cookies specifically
        azure_cookies = [
            cookie for cookie in all_cookies
            if "AzureAppProxy" in cookie.get("name", "")
        ]

        if not azure_cookies:
            logger.warning(f"No Azure App Proxy cookies found for domain '{expected_domain}'! Were you successfully logged in?")
            print("\n" + "-"*30)
            print("  No Azure App Proxy Cookies Found ")
            print("-"*30)
            print(f"Could not find cookies starting with 'AzureAppProxy' for domain '{expected_domain}'.")
            print("Please ensure you were fully logged in and on the correct page before pressing Enter.")
            print("\nAll cookies found for the domain (for debugging):")
            print(json.dumps(all_cookies, indent=4)) # Print all found cookies if Azure ones are missing
        else:
            logger.info(f"Found {len(azure_cookies)} Azure App Proxy cookies.")
            # Print the cookies in a usable Python list format
            print("\n" + "="*70)
            print("  Extracted Azure App Proxy Cookies (for Python) ")
            print("="*70)
            print("# Copy the list below (starting with '[') and paste it")
            print("# into the 'cookies_to_inject = [...]' variable in your other script.")
            print("# Make sure boolean values (True/False) are capitalized correctly in Python.")
            print("[")
            for i, cookie in enumerate(azure_cookies):
                # Format booleans as Python literals (True/False)
                http_only_py = str(cookie.get('httpOnly', False)).capitalize()
                secure_py = str(cookie.get('secure', False)).capitalize()
                # Format expires correctly (keep as number or -1)
                expires_py = cookie.get('expires', -1)
                # Format sameSite - keep as string
                same_site_py = cookie.get('sameSite', 'None') # Default to 'None' if missing

                print("    {")
                print(f"        \"name\": \"{cookie.get('name')}\",")
                print(f"        \"value\": \"{cookie.get('value')}\",")
                print(f"        \"domain\": \"{cookie.get('domain')}\",")
                print(f"        \"path\": \"{cookie.get('path')}\",")
                print(f"        \"expires\": {expires_py},")
                print(f"        \"httpOnly\": {http_only_py},")
                print(f"        \"secure\": {secure_py},")
                print(f"        \"sameSite\": \"{same_site_py}\"")
                print("    }" + ("," if i < len(azure_cookies) - 1 else "")) # Add comma except for last item
            print("]")
            print("="*70)
            status = "Success"

    except Exception as e:
        logger.error("--- Script Failed Critically ---")
        logger.error(f"Error: {e}")
        traceback.print_exc()
        status = f"Failed: {e}"
        print(f"\nAn error occurred: {e}")
        print("Please check the log file for details:", log_file)
    finally:
        # Close browser resources
        logger.info("Closing browser...")
        if browser:
            try:
                browser.close()
                logger.info("Browser closed.")
            except Exception as e:
                 logger.error(f"Error closing browser: {e}")

    logger.info(f"Cookie extraction process finished with status: {status}")
    return status == "Success"


# --- Execution Entry Point ---
if __name__ == "__main__":
    start_time = time.time()
    logger.info("--- Starting Cookie Extraction Script ---")
    print(f"Log file: {log_file}") # Show log file path at start

    success = False
    try:
        with sync_playwright() as playwright_instance:
            success = extract_cookies_after_manual_login(playwright_instance)
    except Exception as runner_err:
         logger.critical(f"Failed to initialize Playwright or run extraction function: {runner_err}")
         traceback.print_exc()
         print(f"\nA critical error occurred during setup: {runner_err}")
         print("Please check the log file for details:", log_file)


    end_time = time.time()
    logger.info("--- Script Execution Finished ---")
    logger.info(f"Status: {'Success' if success else 'Failed'}")
    logger.info(f"Total execution time: {end_time - start_time:.2f} seconds")
    print(f"\nScript finished. Status: {'Success' if success else 'Failed'}")

    # Exit with appropriate code
    sys.exit(0 if success else 1)