from enum import StrEnum, auto
from typing import Any

import torch
from torch import nn
from transformers.modeling_outputs import SequenceClassifierOutput

from slugpy.model.sequence_classifier.lstm import LSTMClassifier
from slugpy.model.sequence_classifier.transformer import TransformerClassifier
from slugpy.typings import TaskType

SEQCLASSIFIER_MAPPING = {"lstm": LSTMClassifier, "transformer": TransformerClassifier}


SequenceClassifierType = StrEnum("SequenceClassifierType", {x.upper(): auto() for x in SEQCLASSIFIER_MAPPING.keys()})


class SequenceClassifier(nn.Module):
    def __init__(
        self,
        model_type: "SequenceClassifierType",
        task_type: TaskType,
        class_weights: torch.FloatTensor | None = None,
        **kwargs,
    ):
        super().__init__()
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model_type = SEQCLASSIFIER_MAPPING[model_type.value]
        self.model = self.model_type(**kwargs)
        self.model.to(self.device)
        self.task_type = task_type
        criterion = nn.BCEWithLogitsLoss if self.task_type == TaskType.MULTI_LABEL else nn.CrossEntropyLoss
        self.loss_fn = criterion(class_weights.to(self.device))

    def forward(self, batch: dict[str, Any]) -> SequenceClassifierOutput:
        logits = self.model.forward(batch)
        loss = None
        if self.task_type == TaskType.MULTI_LABEL and "labels_encoding" in batch:
            loss = self.loss_fn(logits, batch["labels_encoding"])
        elif self.task_type == TaskType.MULTI_CLASS and "primary_label_encoding" in batch:
            loss = self.loss_fn(logits, batch["primary_label_encoding"])
        return SequenceClassifierOutput(loss, logits)
