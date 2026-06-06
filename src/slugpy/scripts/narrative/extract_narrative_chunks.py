from pathlib import Path

from slugpy.helpers.abridger import abridge_narrative_only


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


def extract_narrative_chunks(
    script_filepath_or_folderpath: Path, dst_filepath: Path, chunk_soft_size: int = 500
) -> None:
    script_filepaths = validate_input(script_filepath_or_folderpath, dst_filepath)

    with dst_filepath.open("a", encoding="utf-8") as f:
        for script_filepath in script_filepaths:
            abridged_script = abridge_narrative_only(script_filepath)
            current_chunk = []
            current_chunk_size = 0
            for line in abridged_script:
                line = line.strip()
                if current_chunk and current_chunk_size >= chunk_soft_size:
                    f.write("\\n".join(current_chunk) + "\n")
                    current_chunk = []
                    current_chunk_size = 0
                current_chunk.append(line)
                current_chunk_size += len(line)
            if current_chunk:
                f.write("\\n".join(current_chunk) + "\n")
