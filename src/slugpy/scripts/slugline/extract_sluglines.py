from pathlib import Path

from slugpy.dataset.dataset import Script


def validate_input(script_filepath_or_folderpath: Path, dst_filepath: Path) -> list[Path]:
    assert dst_filepath.suffix == ".txt", "Output file must be a .txt file"
    if script_filepath_or_folderpath.is_file():
        assert script_filepath_or_folderpath.suffix == ".screenplay", "Input file must be a .screenplay file"
        script_filepaths = [script_filepath_or_folderpath]
    elif script_filepath_or_folderpath.is_dir():
        script_filepaths = list(script_filepath_or_folderpath.glob("*.screenplay"))
        assert len(script_filepaths) > 0, "Input folder must contain .screenplay files"
    else:
        raise ValueError("Input path must be a .screenplay file or a folder containing .screenplay files")
    return script_filepaths


def extract_sluglines(script_filepath_or_folderpath: Path, dst_filepath: Path):
    script_filepaths = validate_input(script_filepath_or_folderpath, dst_filepath)

    with dst_filepath.open("a", encoding="utf-8") as f:
        for script_filepath in script_filepaths:
            check_for_labels = True
            skip_next_line = False
            for slp in Script(script_filepath, ctx_size=1, random_start=False, iter_as_dict=False):
                if skip_next_line:
                    skip_next_line = False
                    continue
                if check_for_labels:
                    if not slp.line.primary_label:
                        print(f"No annotations detected for {script_filepath}, skipping it.")
                        break
                    check_for_labels = False
                if slp.line.primary_label != "S":
                    continue
                slugline = slp.line.line.strip()
                if slp.post_ctx[0].primary_label == "S":
                    # If the next line is also a scene heading, they are probably part of the same scene and so we need to
                    # concatenate them. However, the current slugline may end with the scene id, which we should remove
                    # to avoid a semantic break in the scene heading. We can only be sure that the suffix of the slugline
                    # is a scene id if it is the same as its prefix.
                    # Example:
                    #   Pre-ctx     ANYTHING
                    #   cursor      "15B EXT. SILVERSTONE RACE COMPLEX - AERIAL - SAME     15"
                    #   post-ctx    "TIME - NIGHT"
                    removed_suffix = False
                    skip_next_line = True
                    slugline_parts = slugline.split(" ")
                    if len(slugline_parts) > 1 and slugline_parts[-1] == slugline_parts[0]:
                        slugline = " ".join(slugline_parts[:-1]).strip()
                        removed_suffix = True
                    slugline += " " + slp.post_ctx[0].line.strip()
                    if removed_suffix:
                        slugline += " " + slugline_parts[-1]
                f.write(slugline + "\n")
