from itertools import chain
from typing import Any

import torch
from sentence_transformers import SentenceTransformer
from torch import nn

from slugpy.dataset.label import N_LABELS
from slugpy.model.features_extractor import ScriptLineFeaturesExtractor
from slugpy.model.tokenizer import TokenizerWithCtx


class ScriptLineClassifier(nn.Module):
    def __init__(self, tokenizer_model_name: str, features_extractor: ScriptLineFeaturesExtractor, bidirectional: bool):
        super().__init__()
        self.tokenizer = TokenizerWithCtx(model_name=tokenizer_model_name)  # "sentence-transformers/all-mpnet-base-v2"
        self.features_extractor = features_extractor
        self.features_size = self.tokenizer.dim + self.features_extractor.n_features
        self.hidden_size = 256
        self.n_labels = N_LABELS
        self.bidirectional = bidirectional
        self.lstm = nn.LSTM(self.features_size, self.hidden_size, batch_first=True, bidirectional=bidirectional)
        self.classifier = nn.Linear((1 + int(self.bidirectional)) * self.hidden_size, self.n_labels)

    def forward(self, batch: dict[str, Any]) -> torch.LongTensor:
        lines_with_ctx_tokenized = self.tokenizer(
            batch["line_with_ctx"], return_line_span_mask=True, return_attention_mask=False
        )  # (B, 2*Ctx + 1, ~) -> (B, T)
        lines_features = self.features_extractor(batch["line"])  # (B, n_features)
        input = torch.cat([lines_with_ctx_tokenized["input_ids"], lines_features], dim=1)  # (B, T + n_features)
        last_hidden, _ = self.lstm(input)  # (B, T + n_features, H * (1 + bidirectional))
        # Mean-pool the target line span
        line_span_mask = lines_with_ctx_tokenized["line_span_mask"]
        tokens_pooled = last_hidden[:, : self.tokenizer.dim][line_span_mask].mean(dim=1)  # (B, H* (1 + bidirectional))
        features_pooled = last_hidden[:, self.tokenizer.dim :].mean(dim=1)  # (B, H* (1 + bidirectional))
        pooled = torch.cat([tokens_pooled, features_pooled], dim=1)  # (B, H * (1 + bidirectional) * 2)
        logits = self.classifier(pooled)
        return logits.argmax(dim=1)
