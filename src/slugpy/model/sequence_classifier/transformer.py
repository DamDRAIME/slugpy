from typing import Any

import torch
import torch.nn as nn
from transformers import AutoModel

from slugpy.dataset.label import N_LABELS
from slugpy.model.features_extractor import ScriptLineFeaturesExtractor
from slugpy.model.tokenizer import TokenizerWithCtx


class TransformerClassifier(nn.Module):
    def __init__(
        self, model_name: str, features_extractor: ScriptLineFeaturesExtractor | None = None, **tokenizer_kwargs
    ):
        super().__init__()
        self.tokenizer = TokenizerWithCtx(model_name, **tokenizer_kwargs)  # "microsoft/deberta-v3-base"
        self.transformer_model = AutoModel.from_pretrained(model_name)
        self.transformer_model.resize_token_embeddings(len(self.tokenizer))
        self.features_extractor = features_extractor
        self.n_labels = N_LABELS
        self.classifier_input_size = self.transformer_model.config.hidden_size
        if self.features_extractor is not None:
            self.classifier_input_size += self.features_extractor.n_features
        self.classifier = nn.Linear(self.classifier_input_size, self.n_labels)

    def forward(self, batch: dict[str, Any]) -> torch.LongTensor:
        # Tokenizer
        lines_with_ctx_tokenized = self.tokenizer(batch["line_with_ctx"])  # (B, 2*Ctx + 1, ~) -> (B, T)
        # Transformer
        outputs = self.transformer_model(**lines_with_ctx_tokenized)
        last_hidden = outputs.last_hidden_state  # (B, T, H)
        # Mean-pool the target line span
        line_span_mask = torch.broadcast_to(lines_with_ctx_tokenized["line_span_mask"].unsqueeze(-1), last_hidden.shape)
        line_span_mask = line_span_mask.to(torch.bool)
        masked_hidden = last_hidden.masked_fill(~line_span_mask, float("nan"))
        x = torch.nanmean(masked_hidden, 1)  # (B, H)
        if self.features_extractor is not None:
            # Feature Extractor + Concat
            lines_features, _headers = self.features_extractor(batch["line"], batch["line_with_ctx"])  # (B, n_features)
            x = torch.cat([lines_features, x], dim=1)  # (B, (H * (1 + bidirectional)) + n_features)
        # Classifier
        logits = self.classifier(x.to(torch.float32))  # (B, n_labels)
        return logits
