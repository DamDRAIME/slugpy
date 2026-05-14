from pathlib import Path

import pdfplumber
from ocrmypdf import _progressbar as pb
from rich.console import Console

from slugpy.helpers.utils import add_text_layer, deduplicate_chars


def pdf2txt(
    pdf_filepath: Path | str,
    txt_filepath: Path | str,
    preserve_layout: bool = True,
    new_page_add_newline: bool = False,
    skip_duplicated_empty_lines: bool = True,
) -> list[str]:
    """
    Converts a PDF file to a text file, using OCR if necessary, while preserving the layout.

    This function extracts text from a PDF, applies OCR to pages without text if needed,
    and processes the lines to deduplicate characters and handle empty lines.

    Args:
        pdf_filepath (Path | str): Path to the input PDF file.
        txt_filepath (Path | str): Path where the output text file will be saved.
        preserve_layout (bool, optional): Whether to preserve the layout, i.e. indentation, when extracting text.
            Defaults to True.
        new_page_add_newline (bool, optional): Whether to add a newline after each page. Defaults to False.
        skip_duplicated_empty_lines (bool, optional): Whether to skip consecutive empty lines. Defaults to True.

    Returns:
        list[str]: Extracted text.
    """

    # Extracting text from PDF via OCR, if needed
    pdf = add_text_layer(pdf_filepath)

    with pdfplumber.open(pdf) as pdf_fh:
        txt_filepath = Path(txt_filepath)
        with txt_filepath.open("w", encoding="utf-8") as txt_fh:
            # Reusing OCRMyPDF's progress bar for consistent user experience.
            with pb.RichProgressBar(
                console=Console(stderr=True), desc="Parsing text", total=len(pdf_fh.pages)
            ) as progress_bar:
                for page in pdf_fh.pages:
                    text = page.extract_text(layout=preserve_layout)
                    lines = text.splitlines(keepends=True)
                    prev_line_empty = False
                    for line in lines:
                        # Checking for empty lines
                        if not line.strip():
                            if not prev_line_empty or not skip_duplicated_empty_lines:
                                txt_fh.write("\n")
                            prev_line_empty = True
                            continue

                        prev_line_empty = False

                        # Deduplicating characters: `MMIILLTTOONN ((CCOONNTT''DD))` -> `MILTON (CONT'D)`
                        # For some reasons, not linked to the OCR step, sone lines will have all their characters
                        # duplicated, e.g.: GGrreeeenn RReevv.. ((mmmm//dddd//yyyy)) 116633..
                        line = deduplicate_chars(line)

                        txt_fh.write(line)

                    if new_page_add_newline:
                        txt_fh.write("\n")

                    progress_bar.update()

    return txt_filepath
