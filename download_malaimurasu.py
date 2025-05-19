import requests
from bs4 import BeautifulSoup
import re
import os
from datetime import datetime
from PyPDF2 import PdfMerger
import io

def download_and_merge_malaimurasu_epaper(date=None):
    """
    Downloads and merges Malaimurasu e-paper pages for the given date into a single PDF.
    """
    if date is None:
        date = datetime.now().strftime('%Y/%m/%d')

    year, month, day = date.split('/')
    base_url = "https://epaper.malaimurasu.com"

    if not os.path.exists('downloads'):
        os.makedirs('downloads')

    # Construct main page URL
    main_page_url = f"{base_url}/{year}/{month}/{day}/Chennai/index.shtml"

    try:
        response = requests.get(main_page_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Find total number of pages from JS variables or links
        script_tags = soup.find_all('script', text=re.compile(r'var totalPages'))
        total_pages = 10  # Fallback default
        for script in script_tags:
            match = re.search(r'var\s+totalPages\s*=\s*(\d+)', script.text)
            if match:
                total_pages = int(match.group(1))
                break

        print(f"Found {total_pages} pages to download.")
        merger = PdfMerger()

        for page_num in range(1, total_pages + 1):
            pdf_url = f"{base_url}/{year}/{month}/{day}/Chennai/CHE_P{page_num:02d}.pdf"
            print(f"Trying {pdf_url}")
            try:
                resp = requests.get(pdf_url)
                resp.raise_for_status()
                merger.append(io.BytesIO(resp.content))
                print(f"Downloaded page {page_num}")
            except Exception as e:
                print(f"Failed page {page_num}: {e}")
                continue

        output_filename = f"downloads/malaimurasu_{year}_{month}_{day}.pdf"
        merger.write(output_filename)
        merger.close()
        print(f"PDF saved as {output_filename}")
        return output_filename

    except Exception as e:
        print(f"Error: {e}")
        return None


if __name__ == "__main__":
    download_and_merge_malaimurasu_epaper()
