import os
import io
import re
import requests
from datetime import datetime
from PyPDF2 import PdfMerger
from bs4 import BeautifulSoup

def download_and_merge_malaimurasu_epaper(date=None):
    if date is None:
        date = datetime.now().strftime('%Y/%m/%d')

    year, month, day = date.split('/')
    base_url = "https://epaper.malaimurasu.com"

    out_dir = 'downloads'
    os.makedirs(out_dir, exist_ok=True)

    # Setup session with retry
    session = requests.Session()
    session.headers.update({'User-Agent': 'Mozilla/5.0'})
    adapter = requests.adapters.HTTPAdapter(max_retries=2)
    session.mount("https://", adapter)

    try:
        index_url = f"{base_url}/{date}/Chennai/index.shtml"
        response = session.get(index_url, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        scripts = soup.find_all("script")
        page_count = 8  # Fallback default

        for script in scripts:
            match = re.search(r'var totalPages\s*=\s*(\d+);', script.text)
            if match:
                page_count = int(match.group(1))
                break

        merger = PdfMerger()
        for page in range(1, page_count + 1):
            pdf_name = f"CHE_P{page:02d}.pdf"
            pdf_url = f"{base_url}/{date}/Chennai/{pdf_name}"
            print(f"Trying {pdf_url}")
            try:
                res = session.get(pdf_url, timeout=10)
                res.raise_for_status()
                merger.append(io.BytesIO(res.content))
                print(f"Page {page} added.")
            except:
                print(f"Failed: {pdf_url}")

        output_file = os.path.join(out_dir, f"malaimurasu_{year}_{month}_{day}.pdf")
        merger.write(output_file)
        merger.close()

        print(f"Saved: {output_file}")
        return output_file

    except Exception as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    download_and_merge_malaimurasu_epaper()
