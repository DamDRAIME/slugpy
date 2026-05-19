from typing import Any

import torch
from torch import nn
from transformers import AutoModel

from slugpy.dataset.label import N_LABELS
from slugpy.model.features_extractor import ScriptLineFeaturesExtractor
from slugpy.model.tokenizer import TokenizerWithCtx


class LSTMClassifier(nn.Module):
    def __init__(
        self,
        model_name: str,
        features_extractor: ScriptLineFeaturesExtractor | None = None,
        bidirectional: bool = True,
        lstm_hidden_size: int = 256,
        **tokenizer_kwargs,
    ):
        super().__init__()
        self.tokenizer = TokenizerWithCtx(model_name, **tokenizer_kwargs)  # "sentence-transformers/all-mpnet-base-v2"
        self.embedding_model = AutoModel.from_pretrained(model_name)
        self.embedding_model.resize_token_embeddings(len(self.tokenizer))
        self.features_extractor = features_extractor
        self.lstm_input_size = self.embedding_model.config.hidden_size
        self.lstm_hidden_size = lstm_hidden_size
        self.bidirectional = bidirectional
        self.lstm = nn.LSTM(
            self.lstm_input_size,
            self.lstm_hidden_size,
            batch_first=True,
            bidirectional=self.bidirectional,
        )
        self.init_lstm_weights()
        self.n_labels = N_LABELS
        lstm_output_size = (1 + int(self.bidirectional)) * self.lstm_hidden_size
        self.classifier_input_size = lstm_output_size
        if self.features_extractor is not None:
            self.classifier_input_size += self.features_extractor.n_features
        self.classifier = nn.Linear(self.classifier_input_size, self.n_labels)

    def init_lstm_weights(self):
        for name, param in self.lstm.named_parameters():
            if "weight_ih" in name:
                nn.init.xavier_uniform_(param.data)
            elif "weight_hh" in name:
                nn.init.orthogonal_(param.data)
            elif "bias" in name:
                param.data.fill_(0)
                # Optional: Set forget gate bias to 1 to help with long-term dependencies
                # The forget gate is usually the second 1/4 of the bias vector
                n = param.size(0)
                param.data[n // 4 : n // 2].fill_(1.0)

    def forward(self, batch: dict[str, Any]) -> torch.LongTensor:
        # Tokenizer
        lines_with_ctx_tokenized = self.tokenizer(batch["line_with_ctx"])  # (B, 2*Ctx + 1, ~) -> (B, T)
        # Embedding
        lines_embeddings = self.embedding_model(**lines_with_ctx_tokenized).last_hidden_state  # (B, T, H)
        # LSTM
        last_hidden, _ = self.lstm(lines_embeddings)  # (B, T, H * (1 + bidirectional))
        # Mean-pool the target line span
        line_span_mask = torch.broadcast_to(lines_with_ctx_tokenized["line_span_mask"].unsqueeze(-1), last_hidden.shape)
        line_span_mask = line_span_mask.to(torch.bool)
        masked_hidden = last_hidden.masked_fill(~line_span_mask, float("nan"))
        x = torch.nanmean(masked_hidden, 1)  # (B, H * (1 + bidirectional))
        if self.features_extractor is not None:
            # Feature Extractor + Concat
            lines_features, _headers = self.features_extractor(batch["line"], batch["line_with_ctx"])  # (B, n_features)
            x = torch.cat([lines_features, x], dim=1)  # (B, (H * (1 + bidirectional)) + n_features)
        # Classifier
        logits = self.classifier(x)  # (B, n_labels)
        return logits
