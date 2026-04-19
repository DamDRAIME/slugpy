import io
from pathlib import Path

import ocrmypdf
import pdfplumber
from ocrmypdf import _progressbar as pb
from rich.console import Console

from slugpy.parse.utils import deduplicate_chars


def pdf_to_txt(
    pdf_filepath: Path | str,
    txt_filepath: Path | str,
    preserve_layout: bool = True,
    new_page_add_newline: bool = False,
    skip_duplicated_empty_lines: bool = True,
) -> Path:
    # Extracting text from PDF via OCR, if needed
    pdf = add_text_layer(pdf_filepath)

    with pdfplumber.open(pdf) as pdf_fh:
        txt_filepath = Path(txt_filepath)
        with txt_filepath.open("w", encoding="utf-8") as txt_fh:
            with pb.RichProgressBar(
                console=Console(stderr=True), desc="Parsing text", total=len(pdf_fh.pages)
            ) as progressbar:
                for page in pdf_fh.pages:
                    text = page.extract_text(layout=preserve_layout)
                    lines = text.splitlines(keepends=True)
                    prev_line_empty = False
                    for line in lines:
                        line_stripped = line.lstrip()

                        # Checking for empty lines
                        if not line_stripped:
                            if not prev_line_empty or not skip_duplicated_empty_lines:
                                txt_fh.write("\n")
                            prev_line_empty = True
                            continue

                        prev_line_empty = False

                        # Deduplicating characters: `MMIILLTTOONN ((CCOONNTT''DD))` -> `MILTON (CONT'D)`
                        # For some reasons, not linked to the OCR, sone lines will have all their characters duplicated,
                        # e.g.: GGrreeeenn RReevv.. ((mmmm//dddd//yyyy)) 116633..
                        line = deduplicate_chars(line)
                        txt_fh.write(line)

                    if new_page_add_newline:
                        txt_fh.write("\n")

                    progressbar.update()

    return txt_filepath


def add_text_layer(pdf: Path | str) -> io.BytesIO:
    output_stream = io.BytesIO()
    ocrmypdf.ocr(pdf, output_stream, skip_text=True)  # skip_text=True: Skip OCR for sections where text is extractable
    return output_stream
