import io
from pathlib import Path

import ocrmypdf


def deduplicate_chars(x: str) -> str:
    """
    Deduplicates consecutive identical characters (spaces excluded), if all non-space characters are duplicated.

    Preserves leading, internal, and trailing whitespace.

    If the string contains any non-consecutive identical pairs (excluding spaces), returns the original string.

    Examples:
        - "  AABB CC DDD\n" -> "  AB C D\n"
        - "  ABB CC DDD\n" -> "  ABB CC DDD\n" (no deduplication)

    Args:
        x (str): The input string to deduplicate.

    Returns:
        str: The deduplicated string, or the original if deduplication is not required.
    """
    newline = x.endswith("\n")
    n = len(x) - 1 - int(newline)
    deduplicated = ""
    i = 0
    while i < n:
        if x[i] == " ":  # Whitespaces are not duplicated
            deduplicated += " "
            i += 1
        elif (char := x[i]) == x[i + 1]:
            deduplicated += char
            i += 2
        else:
            return x
    return deduplicated + "\n" if newline else ""


def add_text_layer(pdf: Path | str) -> io.BytesIO:
    """
    Adds a text layer to a PDF using OCR if necessary.

    This function processes a PDF file and adds an OCR text layer to pages that lack extractable text,
    returning the modified PDF as a BytesIO stream.

    Args:
        pdf (Path | str): Path to the input PDF file.

    Returns:
        io.BytesIO: A BytesIO stream containing the PDF with added text layer.
    """
    output_stream = io.BytesIO()
    ocrmypdf.ocr(pdf, output_stream, skip_text=True)  # skip_text=True: Skip OCR for sections where text is extractable
    return output_stream
