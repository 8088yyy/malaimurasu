import requests
from bs4 import BeautifulSoup
from PyPDF2 import PdfMerger
from datetime import datetime
import os
import io
import re

def download_malaimurasu_latest():
    homepage = "https://epaper.malaimurasu.com/"
    try:
        r = requests.get(homepage, timeout=20)
        r.raise_for_status()
    except Exception as e:
        print(f"Failed to access homepage: {e}")
        return None

    soup = BeautifulSoup(r.text, "html.parser")
    iframe = soup.find("iframe")

    if not iframe or not iframe.get("src"):
        print("No iframe found.")
        return None

    # Extract date path from iframe src
    match = re.search(r'(\d{4}/\d{2}/\d{2})/Chennai', iframe["src"])
    if not match:
        print("Date path not found in iframe URL.")
        return None

    date_path = match.group(1)
    year, month, day = date_path.split("/")

    base_url = f"https://epaper.malaimurasu.com/{date_path}/Chennai"
    output_file = f"downloads/malaimurasu_{year}_{month}_{day}.pdf"

    os.makedirs("downloads", exist_ok=True)
    merger = PdfMerger()

    for i in range(1, 50):  # Try up to 50 pages max
        for variant in [f"CHE_P{i:02d}.pdf", f"CHE_P{i}.pdf"]:
            pdf_url = f"{base_url}/{variant}"
            try:
                res = requests.get(pdf_url, timeout=10)
                res.raise_for_status()
                merger.append(io.BytesIO(res.content))
                print(f"Downloaded page {i}")
                break  # Page added, go to next
            except:
                continue
        else:
            print(f"Stopped at page {i - 1}")
            break

    if merger.pages:
        merger.write(output_file)
        merger.close()
        print(f"Saved merged PDF as {output_file}")
        return output_file
    else:
        print("No pages downloaded.")
        return None

if __name__ == "__main__":
    download_malaimurasu_latest()
