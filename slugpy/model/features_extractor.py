from abc import ABC, abstractmethod
from itertools import chain
import re

import spacy
from spacy.tokens import Doc
from spacy.language import Language
import torch

from slugpy.dataset.payload import ScriptLine, ScriptLinePayload


class FeatureExtractor(ABC):
    headers: list[str] = []

    def __init__(self):
        self.n_features = len(self.headers)

    def _get_empty_features(self) -> torch.FloatTensor:
        return torch.zeros(self.n_features)

    def extract_features(self, doc: Doc) -> torch.FloatTensor:
        if len(doc) == 0:  # TODO: Is that valid because it is the number of tokens
            return self._get_empty_features()
        return self._extract_features(doc)

    @abstractmethod
    def _extract_features(self, doc: Doc) -> torch.FloatTensor:
        raise NotImplementedError

    def __call__(self, doc: Doc) -> tuple[torch.FloatTensor, list[str]]:
        return self.extract_features(doc), self.headers


class Compose:
    def __init__(self, feat_extractors: list[FeatureExtractor]):
        self.feat_extractors = feat_extractors
        self.n_features = sum([feat_ext.n_features for feat_ext in self.feat_extractors])
        self.headers = list(chain([feat_ext.headers for feat_ext in self.feat_extractors]))

    def extract_features(self, doc: Doc) -> torch.FloatTensor:
        feat = []
        for feat_ext in self.feat_extractors:
            feat.append(feat_ext.extract_features(doc))
        return torch.cat(feat, dim=1)

    def __call__(self, doc: Doc) -> tuple[torch.FloatTensor, list[str]]:
        return self.extract_features(doc), self.headers


class ScriptLineFeaturesExtractor:
    def __init__(self, feat_extractors: FeatureExtractor | Compose, nlp: Language | None = None):
        self.feat_exts = feat_extractors if isinstance(feat_extractors, Compose) else Compose(feat_extractors)
        self.headers = self.feat_exts.headers
        self.nlp = nlp if nlp is not None else spacy.load("en_core_web_lg", disable=["parser"])

    def __call__(self, x: ScriptLine | ScriptLinePayload | str | list[str]) -> tuple[torch.FloatTensor, list[str]]:
        if isinstance(x, ScriptLine):
            texts = [x.line]
        elif isinstance(x, str):
            texts = [x]
        elif isinstance(x, ScriptLinePayload):
            texts = x.content
        else:
            texts = x
        features = []
        for doc in self.nlp.pipe(texts, batch_size=50):
            features.append(self.feat_exts.extract_features(doc))
        return torch.cat(features, dim=0), self.headers


class POSFeaturesExtractor(FeatureExtractor):
    headers = [
        "num_noun",
        "perc_noun",
        "num_verb",
        "prec_noun",
        "num_adjective",
        "perc_adjective",
        "num_adverb",
        "perc_adverb",
    ]

    def _extract_features(self, doc: Doc) -> torch.FloatTensor:
        features = []
        n_words = len(doc)
        for pos_prefix in ["NN", "VB", "JJ", "RB"]:
            n_pos_words = sum(token.tag_.startswith(pos_prefix) for token in doc)
            features.extend([n_pos_words, n_pos_words / n_words])
        return torch.FloatTensor(features)


class EntityFeaturesExtractor(FeatureExtractor):
    headers = [
        "num_person",
        "frac_person",
        "num_geopolitical",
        "frac_geopolitical",
        "num_location",
        "frac_location",
        "num_organization",
        "frac_organization",
        "num_time",
        "frac_time",
        "num_date",
        "frac_date",
    ]

    def _extract_features(self, doc: Doc) -> torch.FloatTensor:
        features = []
        n_words = len(doc)
        for label in ["PERSON", "GPE", "LOC", "ORG", "TIME", "DATE"]:
            n_ent_words = sum(token.ent_type_ == label for token in doc)
            features.extend([n_ent_words, n_ent_words / n_words])
        return torch.FloatTensor(features)


class LengthFeaturesExtractor(FeatureExtractor):
    headers = ["length"]

    def _extract_features(self, doc: Doc) -> torch.FloatTensor:
        return torch.FloatTensor([len(doc)])


class CapitalizationFeaturesExtractor(FeatureExtractor):
    headers = ["num_cap", "frac_cap"]

    def _extract_features(self, doc: Doc) -> torch.FloatTensor:
        n_cap_words = sum(token.is_upper for token in doc)
        return torch.FloatTensor([n_cap_words, n_cap_words / len(doc)])


class ParenthesesFeaturesExtractor(FeatureExtractor):
    headers = ["num_left_parentheses", "n_right_parentheses", "n_open_parentheses"]

    def _extract_features(self, doc: Doc) -> torch.FloatTensor:
        # TODO: Validate that len(doc) != 0 even when there a parentheses
        n_left = sum(ch in ("(", "[") for ch in doc.text)
        n_right = sum(ch in (")", "]") for ch in doc.text)
        return torch.FloatTensor([n_left, n_right, n_left - n_right])


class KeyphraseFeaturesExtractor(FeatureExtractor):
    _transition_keyphrases = [
        "cut to",
        "cut back to",
        "transition to",
        "close on",
        "dissolve to",
        "shock cut to",  # TODO: Should be removed as it is redundant with cut to
        "fade in",
        "fade up",
        "fade to",
        "fade out",
    ]
    _scene_keyphrases = ["int", "ext"]
    headers = ["contains_transition_keyphrase", "contains_scene_keyphrase"]

    def _extract_features(self, doc: Doc) -> torch.FloatTensor:
        features = []
        for kp_type in [self._transition_keyphrases, self._scene_keyphrases]:
            for kp in kp_type:
                if re.search(r"(\A|\W)" + re.escape(kp) + r"(\W|\Z)", doc.text.lower()) is not None:
                    features.append(1.0)
                    break
            else:
                features.append(0.0)
        return torch.FloatTensor(features)
