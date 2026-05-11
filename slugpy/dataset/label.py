from dataclasses import dataclass

import torch
from torch.nn import functional as F


@dataclass
class Label:
    name: str
    id: int
    code: str


LABELS = [
    Label("Audio guidance", 0, "A"),
    Label("Camera guidance", 1, "G"),
    Label("Character", 2, "C"),
    Label("Deletion", 3, "D"),
    Label("Extension", 4, "E"),
    Label("Introduction", 5, "I"),
    Label("Meta", 6, "M"),
    Label("Narrative", 7, "N"),
    Label("Omit", 8, "O"),
    Label("Parenthetical", 9, "P"),
    Label("Slugline", 10, "S"),
    Label("Transition", 11, "T"),
    Label("Utterance", 12, "U"),
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
