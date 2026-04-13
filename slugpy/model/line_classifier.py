from itertools import chain

from sentence_transformers import SentenceTransformer
from torch import nn
import torch

from slugpy.dataset.label import N_LABELS
from slugpy.model.features_extractor import ScriptLineFeaturesExtractor


class ScriptLineClassifier(nn.Module):

    def __init__(self, features_extractor: ScriptLineFeaturesExtractor, bidirectional: bool):
        super().__init__()
        self.encoder = SentenceTransformer("all-mpnet-base-v2")
        self.features_extractor = features_extractor
        self.features_size = self.encoder.get_sentence_embedding_dimension() + self.features_extractor.n_features
        self.hidden_size = 256
        self.n_labels = N_LABELS
        self.bidirectional = bidirectional
        self.lstm = nn.LSTM(self.features_size, self.hidden_size, batch_first=True, bidirectional=bidirectional)
        self.classifier = nn.Linear((1 + int(self.bidirectional)) * self.hidden_size, self.n_labels)

    def forward(self, lines_batch: list[list[str]]) -> torch.LongTensor:
        batch_size = len(lines_batch)
        sequence_size = len(lines_batch[0])
        lines_flatten = chain([seq for seq in lines_batch])
        device = next(self.parameters()).device  # TODO: No better way?
        lines_embeddings = self.encoder.encode(lines_flatten, convert_to_tensor=True, device=device).reshape(
            batch_size, sequence_size, -1
        )
        lines_features = self.features_extractor(lines_flatten).reshape(batch_size, sequence_size, -1)
        input = torch.cat([lines_embeddings, lines_features], dim=2)
        output, _ = self.lstm(input)  # Check tensor shape
        logits = self.classifier(output)
        return logits.argmax(dim=2)
