from pathlib import Path

from slugpy.helpers.utils import split_at_indentation


def abridge(script_filepath: Path | str, based_on_annotations: bool = False) -> list[str]:
    """
    Abridges a screenplay by newlines between lines of the same nature, based on annotations if available, otherwise
    (default) based on heuristics.

    Args:
        script_filepath (Path | str): Path to the input screenplay text file.
        based_on_annotations (bool, optional): Whether to use annotations to line's nature. Defaults to False, in which
            case heuristics are used such as indentation and case.

    Returns:
        list[str]: The abridged screenplay as a list of lines.
    """
    # TODO: Try to regroup in one line a dialogue block -> C (E?): U (P?) U
    abridged_script = []
    accumulated_line = []
    prev_indent_tag = None
    tags_flag = False
    with open(script_filepath, "r", encoding="utf-8") as f:
        line = f.readline()
        parts = line.split("|", maxsplit=1)
        if len(parts) > 1:
            tags_flag = True
            if not based_on_annotations:
                print("Annotations have been detected and will be ignored as `based_on_annotations` is set to False.")
        if based_on_annotations and not tags_flag:
            raise ValueError("No tags detected in script!")
        f.seek(0)
        for line in f:
            if tags_flag:
                tags, line = line.split("|", maxsplit=1)
                tag = tags.split(",", maxsplit=1)[0]
            line = line.rstrip()
            line, indent = split_at_indentation(line)
            if not line:
                continue
            if based_on_annotations and "O" in tags:
                continue

            key = tag if based_on_annotations else indent
            if prev_indent_tag is not None and key != prev_indent_tag:
                abridged_script.append(" ".join(accumulated_line))
                accumulated_line = []

            accumulated_line.append(line)
            prev_indent_tag = key
        if accumulated_line:
            abridged_script.append(" ".join(accumulated_line))
    return abridged_script
