from pathlib import Path

import torch

from slugpy.dataset.dataset import ScriptDataset
from slugpy.dataset.label import N_LABELS
from slugpy.typings import TaskType


def compute_class_distribution(scripts_folderpath: Path | str, task_type: TaskType) -> torch.FloatTensor:
    dataset = ScriptDataset(scripts_folderpath, ctx_size=0, shuffle=False, random_start=False, iter_as_dict=False)
    class_count = torch.ones(N_LABELS, dtype=torch.float32)
    for x in dataset:
        class_count += x.line.labels_encoding if task_type == TaskType.MULTI_LABEL else x.line.primary_label_encoding
    return class_count


def compute_class_weights(
    scripts_folderpath: Path | str, task_type: TaskType, normalized: bool = True
) -> torch.FloatTensor:
    class_distribution = compute_class_distribution(scripts_folderpath, task_type)
    class_weights = 1 / class_distribution
    if normalized:
        class_weights / class_distribution.sum()
    return class_weights
