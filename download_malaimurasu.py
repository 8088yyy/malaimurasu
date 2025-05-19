import time
import requests
from bs4 import BeautifulSoup
import re

BASE_URL = "https://epaper.malaimurasu.com"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/114.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
}

def fetch_available_dates(retries=3, backoff=3):
    for attempt in range(1, retries + 1):
        try:
            response = requests.get(BASE_URL, headers=HEADERS, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            links = soup.find_all('a', href=True)
            date_pattern = re.compile(r'(\d{4}/\d{2}/\d{2})/')
            dates = []
            for link in links:
                match = date_pattern.search(link['href'])
                if match:
                    dates.append(match.group(1))
            dates = sorted(dates)
            if not dates:
                print("No date folders found on homepage.")
            return dates
        except requests.exceptions.RequestException as e:
            print(f"Attempt {attempt} - Error fetching dates: {e}")
            if attempt < retries:
                print(f"Retrying in {backoff} seconds...")
                time.sleep(backoff)
            else:
                print("Max retries reached, giving up.")
                return []
