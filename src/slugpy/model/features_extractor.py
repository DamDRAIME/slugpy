import re
from abc import ABC, abstractmethod
from itertools import chain

import spacy
import torch
from spacy.language import Language
from spacy.tokens import Doc

from slugpy.helpers.utils import clamp


class FeatureExtractor(ABC):
    headers: list[str] = []

    def __init__(self):
        self.n_features = len(self.headers)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

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
        features = self.extract_features(doc).to(self.device)
        return features, self.headers


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
        "fade in",
        "fade up",
        "fade to",
        "fade out",
        "fade back to",
        "fade back in",
        "flashback to",
        "smash cut to",
        "flash to",
        "match cut to",
        "wipe to",
        "cross cut to",
        "jump cut to",
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


class IndentationFeaturesExtractor(FeatureExtractor):
    headers = ["indent"]

    def _extract_features(self, doc: Doc) -> torch.FloatTensor:
        text_lstrip = doc.text.lstrip()
        return torch.FloatTensor([len(doc.text) - len(text_lstrip)])


class FeatureExtractorWithCtx(ABC):
    pre_line_headers: list[str] = []

    def __init__(self, ctx_size: int):
        self.ctx_size = ctx_size
        self.headers = (self.pre_line_headers * ctx_size) + self.pre_line_headers + (self.pre_line_headers * ctx_size)
        self.n_features = len(self.headers)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    def extract_features(self, docs: list[Doc]) -> torch.FloatTensor:
        return self._extract_features(docs)

    @abstractmethod
    def _extract_features(self, doc: Doc) -> torch.FloatTensor:
        raise NotImplementedError

    def __call__(self, docs: list[Doc]) -> tuple[torch.FloatTensor, list[str]]:
        features = self.extract_features(docs).to(self.device)
        return features, self.headers


class RelativeIndentationFeaturesExtractor(FeatureExtractorWithCtx):
    pre_line_headers = ["relative_indent"]

    def _extract_features(self, doc_with_ctx: list[Doc]) -> torch.FloatTensor:
        indentations = []
        for line in doc_with_ctx:
            text_lstrip = line.text.lstrip()
            indentations.append(len(line.text) - len(text_lstrip))
        line_idx = len(indentations) // 2
        line_indentation = indentations[line_idx]
        indentations = [clamp(x - line_indentation, -1, 1) for x in indentations]
        return torch.FloatTensor(indentations)


class OpenParenthesesFeaturesExtractor(FeatureExtractorWithCtx):
    pre_line_headers = ["n_open_parentheses"]

    def _extract_features(self, doc_with_ctx: list[Doc]) -> torch.FloatTensor:
        parentheses = []
        for line in doc_with_ctx:
            n_left = sum(ch in ("(", "[") for ch in line.text)
            n_right = sum(ch in (")", "]") for ch in line.text)
            parentheses.append(n_left - n_right)
        return torch.FloatTensor(parentheses)


class Compose:
    def __init__(self, *feat_extractors: FeatureExtractor | FeatureExtractorWithCtx):
        self.feat_extractors = feat_extractors
        self.n_features = sum([feat_ext.n_features for feat_ext in self.feat_extractors])
        self.headers = list(chain(*[feat_ext.headers for feat_ext in self.feat_extractors]))
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    def extract_features(self, doc: Doc, doc_with_ctx: list[Doc]) -> torch.FloatTensor:
        feat = []
        for feat_ext in self.feat_extractors:
            feat.append(
                feat_ext.extract_features(doc if issubclass(type(feat_ext), FeatureExtractor) else doc_with_ctx)
            )
        features = torch.cat(feat).to(self.device)
        return features

    def __call__(self, doc: Doc, doc_with_ctx: list[Doc]) -> tuple[torch.FloatTensor, list[str]]:
        return self.extract_features(doc, doc_with_ctx), self.headers


class ScriptLineFeaturesExtractor:
    def __init__(
        self, feat_extractors: FeatureExtractor | FeatureExtractorWithCtx | Compose, nlp: Language | None = None
    ):
        self.feat_exts = feat_extractors if isinstance(feat_extractors, Compose) else Compose(feat_extractors)
        self.headers = self.feat_exts.headers
        self.nlp = nlp if nlp is not None else spacy.load("en_core_web_lg", disable=["parser"])
        self.n_features = self.feat_exts.n_features

    def __call__(
        self, lines: list[str] | None = None, lines_with_ctx: list[list[str]] | None = None
    ) -> tuple[torch.FloatTensor, list[str]]:
        if lines is None and lines_with_ctx is None:
            raise ValueError("`lines` and `lines_with_ctx` cannot be both None.")

        pipes = self.nlp.pipe(lines), [list(self.nlp.pipe(x)) for x in lines_with_ctx]

        features = []
        for doc, doc_with_ctx in zip(*pipes):
            features.append(self.feat_exts.extract_features(doc, doc_with_ctx))
        features = torch.stack(features)
        return features, self.headers
