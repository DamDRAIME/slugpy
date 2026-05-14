from pathlib import Path
from typing import Annotated, Literal

import typer

from slugpy.helpers import abridger, parser

app = typer.Typer()


@app.callback()
def callback():
    """Slugpy"""


@app.command()
def abridge(
    src_filepath: Annotated[Path, typer.Argument(help="Filepath of the script to abridge.")],
    dst_filepath: Annotated[Path, typer.Argument(help="Filepath where to save the abridged script.")],
    based_on_labels: Annotated[bool, typer.Option(help="Whether to use annotations to regroup lines.")] = True,
):
    """Condenses a screenplay by newlines between lines of the same nature."""
    if not based_on_labels:
        abridged_script = abridger.abridge(src_filepath, based_on_labels)
    elif typer.confirm("`U`tterances and `P`arentheticals only?"):
        abridged_script = abridger.abridge_utterances_and_parentheticals_only(src_filepath)
    elif typer.confirm("`N`arrative only?"):
        abridged_script = abridger.abridge_narrative_only(src_filepath)
    else:
        ignore_labels = typer.prompt(
            "Labels to ignore",
            default=["O", "D", "T"],
            type=list[Literal["A", "D", "E", "G", "I", "M", "N", "O", "P", "S", "T", "U"]],
        )
        abridged_script = abridger.abridge(src_filepath, based_on_labels, ignore_labels)

    with dst_filepath.open("w", encoding="utf-8") as fh:
        fh.writelines(abridged_script)


@app.command()
def pdf2txt(
    src_filepath: Annotated[Path, typer.Argument(help="Filepath (.pdf) of the script to convert.")],
    dst_filepath: Annotated[Path, typer.Argument(help="Filepath (.txt) where to save the converted script.")],
    preserve_layout: Annotated[
        bool, typer.Option(help="Whether to preserve the layout, i.e. indentation, when extracting text.")
    ] = True,
    new_page_add_newline: Annotated[bool, typer.Option(help="Whether to add a newline after each page.")] = False,
    skip_duplicated_empty_lines: Annotated[bool, typer.Option(help="Whether to skip consecutive empty lines.")] = True,
):
    """Converts a PDF file to a text file, using OCR if necessary, while preserving the layout."""
    converted_script = parser.pdf2txt(src_filepath, preserve_layout, new_page_add_newline, skip_duplicated_empty_lines)
    with dst_filepath.open("w", encoding="utf-8") as fh:
        fh.writelines(converted_script)
