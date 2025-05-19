import requests
from bs4 import BeautifulSoup
from PyPDF2 import PdfMerger
import os
import io
from datetime import datetime
import re
import time

def get_url_with_retry(url, retries=3, timeout=5):
    for i in range(retries):
        try:
            r = requests.get(url, timeout=timeout)
            r.raise_for_status()
            return r
        except Exception as e:
            print(f"Attempt {i+1} failed for {url}: {e}")
            if i < retries - 1:
                time.sleep(2)
    return None

def download_malaimurasu_latest():
    homepage = "https://epaper.malaimurasu.com/"
    r = get_url_with_retry(homepage)
    if not r:
        print(f"❌ Failed to access homepage after retries.")
        return None

    soup = BeautifulSoup(r.text, "html.parser")

    # Find all links matching date pattern YYYY/MM/DD
    links = soup.find_all("a", href=True)
    date_links = []
    for a in links:
        href = a['href']
        if re.match(r'^/\d{4}/\d{2}/\d{2}/$', href):
            date_links.append(href.strip('/'))

    if not date_links:
        print("❌ No date folders found on homepage.")
        return None

    latest_date = sorted(date_links)[-1]  # e.g. '2025/05/19'
    print(f"✅ Latest date found: {latest_date}")

    base_url = f"https://epaper.malaimurasu.com/{latest_date}/Chennai"
    year, month, day = latest_date.split('/')
    output_file = f"downloads/malaimurasu_{year}_{month}_{day}.pdf"

    os.makedirs("downloads", exist_ok=True)
    merger = PdfMerger()
    pages_downloaded = 0
    max_pages = 30

    for i in range(1, max_pages + 1):
        pdf_name = f"CHE_P{i:02d}.pdf"
        pdf_url = f"{base_url}/{pdf_name}"
        res = get_url_with_retry(pdf_url)
        if not res:
            break
        merger.append(io.BytesIO(res.content))
        print(f"✅ Downloaded page {i}")
        pages_downloaded += 1

    if pages_downloaded > 0:
        merger.write(output_file)
        merger.close()
        print(f"✅ Saved merged PDF: {output_file}")
        return output_file
    else:
        print("❌ No pages downloaded.")
        return None

if __name__ == "__main__":
    download_malaimurasu_latest()
