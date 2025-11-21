import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, "/mnt/Games/abogen")

try:
    from abogen import book_handler
    print("Successfully imported book_handler")
except ImportError as e:
    print(f"Failed to import book_handler: {e}")
    sys.exit(1)

try:
    if hasattr(book_handler, "extract_epub_chapters"):
        print("extract_epub_chapters exists")
    else:
        print("extract_epub_chapters DOES NOT exist")
        
    if hasattr(book_handler, "extract_pdf_pages"):
        print("extract_pdf_pages exists")
    else:
        print("extract_pdf_pages DOES NOT exist")

except Exception as e:
    print(f"Error checking attributes: {e}")
