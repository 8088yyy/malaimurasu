#!/usr/bin/env python3
"""
Makkal Kural E-Paper Downloader
Downloads all pages of the daily e-paper and combines them into a single PDF
Enhanced version with command-line arguments and better error handling
"""

import requests
import json
import logging
import argparse
from datetime import datetime
from pathlib import Path
import PyPDF2
from PyPDF2 import PdfWriter, PdfReader
import sys
import time
import os
from typing import List, Dict, Optional

# Configure logging
def setup_logging():
    """Setup logging configuration"""
    log_format = '%(asctime)s - %(levelname)s - %(message)s'
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[
            logging.FileHandler('log.txt', encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

class MakkalKuralDownloader:
    def __init__(self):
        self.base_url = "http://epaper.makkalkural.net"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.logger = setup_logging()
        self.temp_dir = Path("temp_pdfs")
        self.temp_dir.mkdir(exist_ok=True)
        
    def get_current_date(self) -> str:
        """Get current date in dd/mm/yyyy format"""
        return datetime.now().strftime("%d/%m/%Y")
    
    def validate_date(self, date_str: str) -> bool:
        """Validate date format"""
        try:
            datetime.strptime(date_str, "%d/%m/%Y")
            return True
        except ValueError:
            return False
    
    def get_all_pages(self, date: str) -> List[Dict]:
        """
        Get all page information for a given date
        
        Args:
            date: Date in dd/mm/yyyy format
            
        Returns:
            List of page information dictionaries
        """
        url = f"{self.base_url}/Home/GetAllpages"
        params = {
            'editionid': 1,
            'editiondate': date
        }
        
        try:
            self.logger.info(f"Fetching page list for date: {date}")
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            pages_data = response.json()
            self.logger.info(f"Found {len(pages_data)} pages")
            return pages_data
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error fetching page list: {e}")
            return []
        except json.JSONDecodeError as e:
            self.logger.error(f"Error parsing JSON response: {e}")
            return []
    
    def get_page_download_info(self, page_id: str, date: str) -> Optional[Dict]:
        """
        Get download information for a specific page
        
        Args:
            page_id: Page ID
            date: Date in dd/mm/yyyy format
            
        Returns:
            Dictionary containing download information
        """
        url = f"{self.base_url}/Home/downloadpdfedition_page"
        params = {
            'id': page_id,
            'type': 1,
            'EditionId': 1,
            'Date': date
        }
        
        try:
            self.logger.info(f"Getting download info for page ID: {page_id}")
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            download_info = response.json()
            return download_info
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error fetching download info for page {page_id}: {e}")
            return None
        except json.JSONDecodeError as e:
            self.logger.error(f"Error parsing download info JSON for page {page_id}: {e}")
            return None
    
    def download_pdf_page(self, filename: str, page_num: int) -> Optional[Path]:
        """
        Download a single PDF page
        
        Args:
            filename: Filename from the download info
            page_num: Page number for naming
            
        Returns:
            Path to downloaded file or None if failed
        """
        url = f"{self.base_url}/Home/Download"
        params = {'Filename': filename}
        
        try:
            self.logger.info(f"Downloading page {page_num}: {filename}")
            response = self.session.get(url, params=params, timeout=60, stream=True)
            response.raise_for_status()
            
            # Check if response is actually a PDF
            content_type = response.headers.get('content-type', '').lower()
            if 'pdf' not in content_type and len(response.content) < 1000:
                self.logger.warning(f"Page {page_num} might not be a valid PDF")
            
            # Save to temp directory
            file_path = self.temp_dir / f"page_{page_num:02d}.pdf"
            
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            # Verify the downloaded file is a valid PDF
            try:
                with open(file_path, 'rb') as f:
                    PdfReader(f)
                self.logger.info(f"Successfully downloaded and verified page {page_num}")
                return file_path
            except Exception as e:
                self.logger.error(f"Downloaded file for page {page_num} is not a valid PDF: {e}")
                file_path.unlink(missing_ok=True)
                return None
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error downloading page {page_num}: {e}")
            return None
    
    def combine_pdfs(self, pdf_files: List[Path], output_filename: str) -> bool:
        """
        Combine multiple PDF files into one
        
        Args:
            pdf_files: List of PDF file paths
            output_filename: Output filename
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.logger.info(f"Combining {len(pdf_files)} PDF files")
            pdf_writer = PdfWriter()
            
            for pdf_file in sorted(pdf_files):
                if pdf_file.exists():
                    try:
                        with open(pdf_file, 'rb') as f:
                            pdf_reader = PdfReader(f)
                            page_count = len(pdf_reader.pages)
                            for page in pdf_reader.pages:
                                pdf_writer.add_page(page)
                        self.logger.info(f"Added {pdf_file.name} ({page_count} pages) to combined PDF")
                    except Exception as e:
                        self.logger.error(f"Error processing {pdf_file}: {e}")
                        continue
            
            if len(pdf_writer.pages) == 0:
                self.logger.error("No valid pages to combine")
                return False
            
            # Write combined PDF
            with open(output_filename, 'wb') as output_file:
                pdf_writer.write(output_file)
            
            # Verify the combined PDF
            try:
                with open(output_filename, 'rb') as f:
                    reader = PdfReader(f)
                    total_pages = len(reader.pages)
                self.logger.info(f"Successfully created combined PDF: {output_filename} ({total_pages} pages)")
                return True
            except Exception as e:
                self.logger.error(f"Combined PDF verification failed: {e}")
                return False
            
        except Exception as e:
            self.logger.error(f"Error combining PDFs: {e}")
            return False
    
    def cleanup_temp_files(self):
        """Clean up temporary files"""
        try:
            for file in self.temp_dir.glob("*.pdf"):
                file.unlink()
            if self.temp_dir.exists():
                self.temp_dir.rmdir()
            self.logger.info("Cleaned up temporary files")
        except Exception as e:
            self.logger.warning(f"Error cleaning up temp files: {e}")
    
    def download_daily_paper(self, date: str = None) -> bool:
        """
        Download complete daily paper
        
        Args:
            date: Date in dd/mm/yyyy format (uses current date if None)
            
        Returns:
            True if successful, False otherwise
        """
        if date is None:
            date = self.get_current_date()
        
        if not self.validate_date(date):
            self.logger.error(f"Invalid date format: {date}. Expected dd/mm/yyyy")
            return False
        
        self.logger.info(f"Starting download for date: {date}")
        
        # Get all pages
        pages = self.get_all_pages(date)
        if not pages:
            self.logger.error("No pages found")
            return False
        
        downloaded_files = []
        
        # Process each page
        for i, page in enumerate(pages, 1):
            try:
                page_id = page.get('PageId')
                if not page_id:
                    self.logger.warning(f"No PageId found for page {i}")
                    continue
                
                # Get download info
                download_info = self.get_page_download_info(str(page_id), date)
                if not download_info:
                    self.logger.warning(f"No download info for page {i}")
                    continue
                
                filename = download_info.get('FileName')
                if not filename:
                    self.logger.warning(f"No filename found for page {i}")
                    continue
                
                # Download the PDF
                pdf_file = self.download_pdf_page(filename, i)
                if pdf_file:
                    downloaded_files.append(pdf_file)
                
                # Small delay between downloads
                time.sleep(1)
                
            except Exception as e:
                self.logger.error(f"Error processing page {i}: {e}")
                continue
        
        if not downloaded_files:
            self.logger.error("No files were downloaded successfully")
            return False
        
        # Combine all PDFs
        output_filename = f"MakkalKural_{date.replace('/', '-')}.pdf"
        success = self.combine_pdfs(downloaded_files, output_filename)
        
        # Cleanup
        self.cleanup_temp_files()
        
        if success:
            file_size = os.path.getsize(output_filename) / (1024 * 1024)  # MB
            self.logger.info(f"Successfully created: {output_filename} ({file_size:.2f} MB)")
            return True
        else:
            self.logger.error("Failed to create combined PDF")
            return False

def main():
    """Main function with command-line argument support"""
    parser = argparse.ArgumentParser(description='Download Makkal Kural E-Paper')
    parser.add_argument('--date', '-d', 
                       help='Date to download in dd/mm/yyyy format (default: today)',
                       type=str, default=None)
    
    args = parser.parse_args()
    
    downloader = MakkalKuralDownloader()
    
    try:
        success = downloader.download_daily_paper(args.date)
        if success:
            print("✅ Download completed successfully!")
            return 0
        else:
            print("❌ Download failed. Check log.txt for details.")
            return 1
    except KeyboardInterrupt:
        print("\n⏹️ Download interrupted by user")
        downloader.cleanup_temp_files()
        return 130
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        print("❌ An unexpected error occurred. Check log.txt for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
