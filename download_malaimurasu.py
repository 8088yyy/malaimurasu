import os
import re
import time
import io
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from PyPDF2 import PdfMerger

BASE_URL = "https://epaper.malaimurasu.com"
HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) "
                   "Chrome/114.0.0.0 Safari/537.36"),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
}

def fetch_available_dates(retries=3, backoff=3):
    for attempt in range(1, retries + 1):
        try:
            resp = requests.get(BASE_URL, headers=HEADERS, timeout=10)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, 'html.parser')
            links = soup.find_all('a', href=True)
            date_pattern = re.compile(r'(\d{4}/\d{2}/\d{2})/')
            dates = []
            for link in links:
                match = date_pattern.search(link['href'])
                if match:
                    dates.append(match.group(1))
            dates = sorted(set(dates))
            if not dates:
                print("❌ No date folders found on homepage.")
            return dates
        except requests.RequestException as e:
            print(f"Attempt {attempt} - Error fetching dates: {e}")
            if attempt < retries:
                print(f"Retrying in {backoff} seconds...")
                time.sleep(backoff)
            else:
                print("Max retries reached, giving up.")
                return []

def fetch_total_pages(date):
    url = f"{BASE_URL}/{date}/Chennai/"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')
        select = soup.find('select', id='idGotoPageList')
        if not select:
            print("Could not find page selection dropdown.")
            return 0
        options = select.find_all('option')
        return len(options)
    except requests.RequestException as e:
        print(f"Error fetching total pages for {date}: {e}")
        return 0

def download_pdf(page_num, date):
    urls = [
        f"{BASE_URL}/{date}/Chennai/CHE_P{page_num:02d}.pdf",
        f"{BASE_URL}/{date}/Chennai/CHE_P{page_num}.pdf"
    ]
    for url in urls:
        try:
            resp = requests.get(url, headers=HEADERS, timeout=10)
            resp.raise_for_status()
            print(f"Downloaded page {page_num} from {url}")
            return page_num, io.BytesIO(resp.content)
        except requests.RequestException:
            continue
    print(f"Failed to download page {page_num}")
    return page_num, None

def download_and_merge_epaper(date=None):
    if date is None:
        date = datetime.now().strftime('%Y/%m/%d')
    os.makedirs('downloads', exist_ok=True)

    dates = fetch_available_dates()
    if not dates or date not in dates:
        print(f"❌ Date {date} not available on homepage.")
        return None

    total_pages = fetch_total_pages(date)
    if total_pages == 0:
        print(f"❌ No pages found for date {date}.")
        return None

    print(f"Attempting to download {total_pages} pages for date {date}")

    pdf_pages = {}
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(download_pdf, i, date) for i in range(1, total_pages + 1)]
        for future in as_completed(futures):
            page_num, pdf = future.result()
            if pdf:
                pdf_pages[page_num] = pdf

    if not pdf_pages:
        print("❌ No pages were downloaded successfully.")
        return None

    merger = PdfMerger()
    for i in range(1, total_pages + 1):
        if i in pdf_pages:
            merger.append(pdf_pages[i])

    year, month, day = date.split('/')
    output_path = f"downloads/malaimurasu_{year}_{month}_{day}.pdf"
    merger.write(output_path)
    merger.close()
    print(f"✅ PDF saved as: {output_path}")
    return output_path

if __name__ == "__main__":
    # Change date here to test or None for today's date
    target_date = None
    result = download_and_merge_epaper(target_date)
    if not result:
        print("❌ Failed to download and merge PDFs.")
