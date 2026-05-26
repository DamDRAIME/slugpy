from dataclasses import dataclass

import torch
from torch.nn import functional as F


@dataclass
class Label:
    name: str
    id: int
    code: str


LABELS = [
    # Label("Audio guidance", 0, "A"),
    Label("Character", 0, "C"),
    Label("Deletion", 1, "D"),
    Label("Extension", 2, "E"),
    Label("Camera guidance", 3, "G"),
    Label("Introduction", 4, "I"),
    Label("Meta", 5, "M"),
    Label("Narrative", 6, "N"),
    Label("Omit", 7, "O"),
    Label("Parenthetical", 8, "P"),
    Label("Slugline", 9, "S"),
    Label("Transition", 10, "T"),
    Label("Utterance", 11, "U"),
]

N_LABELS = len(LABELS)

LABEL2ID = {label.code: label.id for label in LABELS}
ID2LABEL = {label.id: label.code for label in LABELS}
NAME2LABEL = {label.name: label.code for label in LABELS}


def to_multi_hot_encoding(labels: list[str], num_classes: int = -1) -> torch.LongTensor:
    num_classes = num_classes if num_classes > 0 else N_LABELS
    labels = torch.LongTensor([LABEL2ID[label] for label in labels])
    encoding = F.one_hot(labels, num_classes)
    return encoding.sum(dim=0).float()
