import os
import time
import random
import pickle
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
import undetected_chromedriver as uc

class LinkedInAutomator:
    """
    Automates LinkedIn tasks like searching for profiles with human-like behavior
    to minimize the risk of detection and account restrictions.
    """
    def __init__(self, cookies_path="linkedin_cookies.pkl"):
        """
        Initializes the automator and launches the browser.

        Args:
            cookies_path (str): Path to store and retrieve session cookies.
        """
        self.cookies_path = cookies_path
        self.driver = self._launch_browser()

    def _launch_browser(self):
        """
        Launches a browser instance using undetected_chromedriver.
        Using a real browser profile is recommended for authenticity.
        """
        print("Launching browser...")
        options = uc.ChromeOptions()
        # To use your own browser profile for a more "real" session:
        # 1. Find your Chrome user data directory.
        #    - Windows: C:\\Users\\<YourUser>\\AppData\\Local\\Google\\Chrome\\User Data
        #    - macOS: ~/Library/Application Support/Google/Chrome
        #    - Linux: ~/.config/google-chrome
        # 2. Uncomment the line below and replace with your path.
        # options.add_argument(r'--user-data-dir=C:\Users\YourUser\AppData\Local\Google\Chrome\User Data')
        # options.add_argument(r'--profile-directory=Default') # Or your specific profile
        try:
            driver = uc.Chrome(options=options)
            return driver
        except Exception as e:
            print(f"Error launching browser: {e}")
            print("Please ensure you have Google Chrome installed.")
            return None

    def login(self):
        """
        Logs into LinkedIn using session cookies if available, otherwise
        prompts for manual login and saves the session.
        """
        if not self.driver:
            return

        self.driver.get("https://www.linkedin.com/")

        if os.path.exists(self.cookies_path):
            print("Loading cookies for login...")
            try:
                with open(self.cookies_path, "rb") as f:
                    cookies = pickle.load(f)
                for cookie in cookies:
                    if 'domain' in cookie and 'linkedin.com' in cookie['domain']:
                        self.driver.add_cookie(cookie)
                self.driver.refresh()
                time.sleep(random.uniform(3, 5))
                if "feed" not in self.driver.current_url and "login" in self.driver.current_url:
                    print("Cookies might be expired. Please log in manually.")
                    self.manual_login()
                else:
                    print("Logged in successfully using cookies.")
            except Exception as e:
                print(f"Could not load cookies: {e}. Please log in manually.")
                self.manual_login()
        else:
            self.manual_login()

    def manual_login(self):
        """
        Waits for the user to log in manually and then saves the session cookies.
        """
        print("Please log in to your LinkedIn account in the browser window.")
        print("The script will continue automatically once you are on your feed page.")
        while "feed" not in self.driver.current_url:
            time.sleep(5)
        print("Login successful. Saving cookies for future sessions...")
        with open(self.cookies_path, "wb") as f:
            pickle.dump(self.driver.get_cookies(), f)
        print(f"Cookies saved to {self.cookies_path}")

    def simulate_typing(self, element, text):
        """
        Simulates human-like typing into a web element with random delays.
        """
        for char in text:
            element.send_keys(char)
            time.sleep(random.uniform(0.1, 0.4))

    def search_profiles(self, query):
        """
        Performs a search on LinkedIn for a given query.
        """
        print(f"Searching for profiles with query: '{query}'")
        try:
            search_box = self.driver.find_element(By.CLASS_NAME, "search-global-typeahead__input")
            self.simulate_typing(search_box, query)
            search_box.send_keys(Keys.ENTER)
            time.sleep(random.uniform(3, 6))
            print("Search performed successfully.")
        except Exception:
            print("Could not find the main search box. Navigating directly.")
            self.driver.get(f"https://www.linkedin.com/search/results/people/?keywords={query}")
            time.sleep(random.uniform(3, 6))

    def extract_html(self, file_name):
        """
        Saves the current page's HTML source to a file for offline parsing.
        """
        print(f"Saving page HTML to {file_name}...")
        try:
            with open(file_name, "w", encoding="utf-8") as f:
                f.write(self.driver.page_source)
            print("HTML saved successfully.")
            return self.driver.page_source
        except Exception as e:
            print(f"Error saving HTML: {e}")
            return None

    def parse_data_from_html(self, html_content):
        """
        Parses HTML to extract profile information (name, title, link).
        """
        print("Parsing profile data from HTML...")
        soup = BeautifulSoup(html_content, 'html.parser')
        profiles = []
        search_results = soup.find_all('li', class_='reusable-search__result-container')

        if not search_results:
            print("No search results found. The page structure may have changed.")
            return []

        for item in search_results:
            try:
                name = item.find('span', {'aria-hidden': 'true'}).get_text(strip=True)
                title = item.find('div', class_='entity-result__primary-subtitle').get_text(strip=True)
                link = item.find('a', class_='app-aware-link')['href']
                if name:
                    profiles.append({"name": name, "title": title, "link": link})
            except Exception:
                continue # Skip if a profile entry is malformed

        return profiles

    def run_automation(self, search_query, pages_to_scrape=1):
        """
        Main automation cycle: logs in, searches, and extracts data.
        """
        if not self.driver:
            return

        self.login()
        self.search_profiles(search_query)

        for page_num in range(pages_to_scrape):
            print(f"--- Processing Page {page_num + 1} ---")
            time.sleep(random.uniform(2, 5)) # Wait before scrolling
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(random.uniform(3, 7)) # Wait for content to load

            file_name = f"linkedin_search_{search_query.replace(' ', '_')}_p{page_num + 1}.html"
            html = self.extract_html(file_name)

            if html:
                profiles = self.parse_data_from_html(html)
                print(f"Found {len(profiles)} profiles on page {page_num + 1}:")
                for profile in profiles:
                    print(f"  - Name: {profile['name']}, Title: {profile['title']}")

            # Navigate to next page
            try:
                next_button = self.driver.find_element(By.XPATH, "//button[@aria-label='Next']")
                if next_button.is_enabled():
                    print("Navigating to the next page...")
                    next_button.click()
                else:
                    print("No more pages to navigate.")
                    break
            except Exception:
                print("Could not find 'Next' button. Ending search.")
                break

        # Apply a final random delay to mimic human behavior
        print("Automation finished for this run. Applying final delay.")
        time.sleep(random.uniform(10, 20))

    def close_browser(self):
        """
        Closes the browser session.
        """
        if self.driver:
            print("Closing browser.")
            self.driver.quit()

if __name__ == "__main__":
    # --- Configuration ---
    # WARNING: Be cautious. Start with low numbers to avoid account restrictions.
    SEARCH_QUERY = "Data Scientist"
    PAGES_TO_SCRAPE = 1 # Number of search result pages to process

    automator = None
    try:
        automator = LinkedInAutomator()
        automator.run_automation(SEARCH_QUERY, PAGES_TO_SCRAPE)
    except Exception as e:
        print(f"A critical error occurred: {e}")
    finally:
        if automator:
            automator.close_browser()
