from typing import Any

import torch
import torch.nn as nn
from transformers import AutoModel

from slugpy.dataset.label import N_LABELS
from slugpy.model.tokenizer import TokenizerWithCtx


class TransformerClassifier(nn.Module):
    def __init__(self, model_name: str, **tokenizer_kwargs):
        super().__init__()
        self.tokenizer = TokenizerWithCtx(model_name, **tokenizer_kwargs)
        self.model = AutoModel.from_pretrained(model_name)
        self.model.resize_token_embeddings(len(self.tokenizer))
        self.n_labels = N_LABELS
        hidden = self.model.config.hidden_size
        self.classifier = nn.Linear(hidden, self.n_labels)

    def forward(self, batch: dict[str, Any]) -> torch.LongTensor:
        lines_with_ctx_tokenized = self.tokenizer(batch["line_with_ctx"])  # (B, 2*Ctx + 1, ~) -> (B, T)
        input_ids = lines_with_ctx_tokenized["input_ids"]
        attention_mask = lines_with_ctx_tokenized["attention_mask"]
        outputs = self.model(input_ids=input_ids, attention_mask=attention_mask)
        last_hidden = outputs.last_hidden_state  # (B, T, H)
        # Mean-pool the target line span
        pooled = last_hidden[lines_with_ctx_tokenized["line_span_mask"]].mean(dim=1)  # (B, H)
        logits = self.classifier(pooled)  # (B, n_labels)
        return logits
