import requests
from bs4 import BeautifulSoup
from datetime import datetime
from PyPDF2 import PdfMerger
import io
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
import re

BASE_URL = "https://epaper.malaimurasu.com"

def fetch_available_dates():
    try:
        response = requests.get(BASE_URL, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        # Find all folder links matching date pattern YYYY/MM/DD
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
    except Exception as e:
        print(f"Error fetching dates from homepage: {e}")
        return []

def fetch_total_pages(date_url):
    try:
        response = requests.get(date_url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        page_select = soup.find('select', {'id': 'idGotoPageList'})
        if not page_select:
            print("Could not find page selection dropdown. Using fallback of 30 pages.")
            return 30
        pages = page_select.find_all('option')
        return len(pages)
    except Exception as e:
        print(f"Error fetching total pages: {e}")
        return 30

def download_pdf(page_num, base_url, date):
    urls = [
        f"{base_url}/{date}/Chennai/CHE_P{page_num:02d}.pdf",
        f"{base_url}/{date}/Chennai/CHE_P{page_num}.pdf"
    ]
    for url in urls:
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            print(f"Downloaded page {page_num} from {url}")
            return page_num, io.BytesIO(response.content)
        except Exception:
            continue
    print(f"Failed to download page {page_num}")
    return page_num, None

def download_and_merge_malaimurasu_epaper(date=None):
    if date is None:
        dates = fetch_available_dates()
        if not dates:
            print("❌ No available dates found, cannot proceed.")
            return None
        date = dates[-1]  # latest date
        print(f"Using latest available date: {date}")

    year, month, day = date.split('/')

    os.makedirs('downloads', exist_ok=True)
    date_url = f"{BASE_URL}/{date}/Chennai/"

    total_pages = fetch_total_pages(date_url)
    print(f"Attempting to download {total_pages} pages for date {date}")

    pdf_contents = {}
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(download_pdf, i, BASE_URL, date) for i in range(1, total_pages + 1)]
        for future in as_completed(futures):
            page_num, pdf = future.result()
            if pdf:
                pdf_contents[page_num] = pdf

    if not pdf_contents:
        print("No pages were downloaded successfully.")
        return None

    merger = PdfMerger()
    for i in range(1, total_pages + 1):
        if i in pdf_contents:
            merger.append(pdf_contents[i])

    output_filename = f"downloads/malaimurasu_{year}_{month}_{day}.pdf"
    merger.write(output_filename)
    merger.close()
    print(f"✅ PDF saved as: {output_filename}")
    return output_filename

if __name__ == "__main__":
    # Pass None for latest date, or specific "YYYY/MM/DD" string
    result = download_and_merge_malaimurasu_epaper(None)
    if not result:
        print("❌ Failed to download and merge PDFs.")
