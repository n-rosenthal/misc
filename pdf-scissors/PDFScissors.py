#!/usr/bin/env python3
"""
Extract a range of pages from a PDF.

Usage:
    python PDFScissors.py input.pdf output.pdf page_init page_end
"""

import sys
from pypdf import PdfReader, PdfWriter

def extract_pages(input_pdf: str, output_pdf: str, page_init: int, page_end: int) -> None:
    """
    Extract pages page_init through page_end (inclusive, 1-indexed) from input_pdf
    and write them to output_pdf.
    """
    reader = PdfReader(input_pdf)
    total_pages = len(reader.pages)

    # Validate page numbers
    if page_init < 1:
        raise ValueError(f"page_init must be >= 1, got {page_init}")
    if page_end > total_pages:
        raise ValueError(
            f"page_end ({page_end}) exceeds total number of pages ({total_pages})"
        )
    if page_init > page_end:
        raise ValueError(
            f"page_init ({page_init}) must be <= page_end ({page_end})"
        )

    writer = PdfWriter()
    # Convert to 0‑based indexing for slicing
    for page_num in range(page_init - 1, page_end):
        writer.add_page(reader.pages[page_num])

    with open(output_pdf, "wb") as out_file:
        writer.write(out_file)

    print(f"Successfully extracted pages {page_init}–{page_end} to '{output_pdf}'")

if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("Usage: python extract_pages.py input.pdf output.pdf page_init page_end")
        sys.exit(1)

    input_path = sys.argv[1]
    output_path = sys.argv[2]

    try:
        start = int(sys.argv[3])
        end = int(sys.argv[4])
    except ValueError:
        print("Error: page_init and page_end must be integers.")
        sys.exit(1)

    try:
        extract_pages(input_path, output_path, start, end)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
