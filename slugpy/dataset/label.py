from dataclasses import dataclass

import torch
from torch.nn import functional as F


@dataclass
class Label:
    name: str
    index: int
    code: str


LABELS = [
    Label("Camera guidance", 0, "G"),
    Label("Character", 1, "C"),
    Label("Character introduction", 2, "I"),
    Label("Deletion", 3, "D"),
    Label("Extension", 4, "E"),
    Label("Meta", 5, "M"),
    Label("Narrative/Action line", 6, "N"),
    Label("Omit", 7, "O"),
    Label("Parentheticals", 8, "P"),
    Label("Slugline", 9, "S"),
    Label("Transition", 10, "T"),
    Label("Utterance", 11, "U"),
]

N_LABELS = len(LABELS)

LABELS_CODE2INDEX_MAPPING = {label.code: label.index for label in LABELS}


def to_one_hot_encoding(labels: list[str], num_classes: int = -1) -> torch.LongTensor:
    num_classes = num_classes if num_classes > 0 else N_LABELS
    labels = torch.LongTensor([LABELS_CODE2INDEX_MAPPING[label] for label in labels])
    encoding = F.one_hot(labels, num_classes)
    return encoding.sum(dim=0).float()
