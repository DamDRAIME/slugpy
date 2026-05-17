from pathlib import Path

import torch

from slugpy.dataset.dataset import ScriptDataset
from slugpy.dataset.label import LABEL2ID, N_LABELS
from slugpy.typings import TaskType


def compute_class_distribution(
    scripts_folderpath: Path | str, task_type: TaskType, skip_empty_lines: bool = True
) -> torch.FloatTensor:
    dataset = ScriptDataset(
        scripts_folderpath,
        ctx_size=0,
        shuffle=False,
        random_start=False,
        iter_as_dict=False,
        skip_empty_lines=skip_empty_lines,
    )
    class_count = torch.ones(N_LABELS, dtype=torch.float32)
    for x in dataset:
        class_count += x.line.labels_encoding if task_type == TaskType.MULTI_LABEL else x.line.primary_label_encoding
    return class_count


def compute_class_weights(
    scripts_folderpath: Path | str, task_type: TaskType, skip_empty_lines: bool = True, normalized: bool = True
) -> torch.FloatTensor:
    class_distribution = compute_class_distribution(scripts_folderpath, task_type, skip_empty_lines)
    class_weights = 1 / class_distribution
    if normalized:
        class_weights / class_distribution.sum()
    return class_weights


def labels_sanity_check(scripts_folderpath: Path | str) -> None:
    dataset = ScriptDataset(
        scripts_folderpath,
        ctx_size=0,
        shuffle=False,
        random_start=False,
        iter_as_dict=False,
        skip_empty_lines=False,
    )
    for x in dataset:
        if x.line is None:
            print(f"Potential empty line(s) at the end of file: {x.fpath}")
            continue
        if any(s in x.line.line for s in ["EXT", "INT"]) and "S" not in x.line.labels:
            print(f"Potential omission of label `S` for line `{x.line.line}` in {x.fpath}, line {x.line.idx + 1}")
        if (
            any(
                s in x.line.line.lower()
                for s in [
                    "close ",
                    "close-up",
                    "pull ",
                    "angle",
                    "stay on",
                    " pan ",
                    "shot ",
                    "camera",
                    "black",
                    "insert",
                ]
            )
            and "G" not in x.line.labels
        ):
            print(f"Potential omission of label `G` for line `{x.line.line}` in {x.fpath}, line {x.line.idx + 1}")
        if any(s in x.line.line.lower() for s in ["playback", "flashback", "title"]) and "M" not in x.line.labels:
            print(f"Potential omission of label `M` for line `{x.line.line}` in {x.fpath}, line {x.line.idx + 1}")
        if (
            any(s in x.line.line.lower() for s in ["cut ", "transition", "fade", "smash", "dissolve", "flash ", "wipe"])
            and "T" not in x.line.labels
        ):
            print(f"Potential omission of label `T` for line `{x.line.line}` in {x.fpath}, line {x.line.idx + 1}")
        for label in x.line.labels:
            if label not in LABEL2ID:
                print(f"Unsupported label (`{label}`) in {x.fpath}, line {x.line.idx + 1}")
            if label == "C":
                if "(" in x.line.line and "E" not in x.line.labels:
                    print(
                        f"Potential omission of label `E` for line `{x.line.line}` in {x.fpath}, line {x.line.idx + 1}"
                    )
