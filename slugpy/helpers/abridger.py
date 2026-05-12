from pathlib import Path

from slugpy.dataset.dataset import Script
from slugpy.helpers.utils import split_at_indentation


def abridge(script_filepath: Path | str, based_on_labels: bool = False) -> list[str]:
    """
    Condenses a screenplay by newlines between lines of the same nature, based on annotations if available, otherwise
    (default) based on heuristics.

    Dialogue blocks will be condensed into one line, when `based_on_labels`.
    Example:

                JAME (V.O.)         |
        Fucking...                  |
            (with a long, quiet     >   JAME (V.O.): Fucking... (with a long, quiet hissing exhale) Fuuuuuuuuuuuuuuuck.
            hissing exhale)         |
        Fuuuuuuuuuuuuuuuck.         |


    Args:
        script_filepath (Path | str): Path to the input screenplay text file.
        based_on_labels (bool, optional): Whether to use annotations to regroupe lines. Defaults to False, in which
            case heuristics are used such as indentation and case.

    Returns:
        list[str]: The abridged screenplay as a list of lines.
    """
    # TODO: Try to regroup in one line a dialogue block for heuristics-based approach
    abridged_script = []
    accumulated_line = []
    prev_indent_or_label = None
    for slp in Script(script_filepath, ctx_size=0, random_start=False, iter_as_dict=False):
        if slp.line.labels and not based_on_labels:
            print("Annotations have been detected and will be ignored as `based_on_annotations` is set to False.")
        elif based_on_labels and not slp.line.labels:
            raise ValueError("No annotations detected in script!")

        line = slp.line.line.rstrip()
        line, indent = split_at_indentation(line)
        if not line:
            continue
        label = slp.line.primary_label
        if based_on_labels:
            if label == "O":
                continue
            if label == "C":
                line += ":"  # Regroup dialogue block into one line > C (E?): U (P?) U

        indent_or_label = label if based_on_labels else indent
        if based_on_labels and label in ("P", "U", "E") and prev_indent_or_label in ("C", "U", "P", "E"):
            # Regroup dialogue block into one line > C (E?): U (P?) U
            pass
        elif prev_indent_or_label is not None and indent_or_label != prev_indent_or_label:
            abridged_script.append(" ".join(accumulated_line))
            accumulated_line = []

        accumulated_line.append(line)
        prev_indent_or_label = indent_or_label
    if accumulated_line:
        abridged_script.append(" ".join(accumulated_line))
    return abridged_script
