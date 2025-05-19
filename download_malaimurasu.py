# download_malaimurasu.py

import requests
from bs4 import BeautifulSoup
from datetime import datetime
from PyPDF2 import PdfMerger
import io
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

def fetch_total_pages(main_page_url):
    try:
        response = requests.get(main_page_url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        page_select = soup.find('select', {'id': 'idGotoPageList'})
        if not page_select:
            print("Could not find the page selection dropdown.")
            return 0
        pages = page_select.find_all('option')
        return len(pages)
    except Exception as e:
        print(f"Error fetching total pages: {e}")
        return 0

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
        except:
            continue
    print(f"Failed to download page {page_num}")
    return page_num, None

def download_and_merge_malaimurasu_epaper():
    date = datetime.now().strftime('%Y/%m/%d')
    year, month, day = date.split('/')
    base_url = "https://epaper.malaimurasu.com"
    os.makedirs('downloads', exist_ok=True)

    total_pages = fetch_total_pages(base_url)
    if total_pages == 0:
        return None

    pdf_contents = {}
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(download_pdf, i, base_url, date) for i in range(1, total_pages + 1)]
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
    print(f"PDF saved as: {output_filename}")
    return output_filename

if __name__ == "__main__":
    result = download_and_merge_malaimurasu_epaper()
    if result:
        print(f"✅ PDF saved as: {result}")
    else:
        print("❌ Failed to download and merge PDFs.")
