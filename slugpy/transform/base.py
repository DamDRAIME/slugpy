from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional

import torch

from slugpy.dataset.label import to_multi_hot_encoding
from slugpy.dataset.payload import ScriptLine, ScriptLinePayload

Label = str


@dataclass
class Condition:
    has: list[Label]
    exclude: list[Label]
    _has_encoding: torch.LongTensor = field(init=False)
    _exclude_encoding: torch.LongTensor = field(init=False)

    def __post_init__(self) -> None:
        self._has_encoding = to_multi_hot_encoding(self.has)
        self._exclude_encoding = to_multi_hot_encoding(self.exclude)

    def is_satified(self, x: ScriptLine | ScriptLinePayload | None) -> bool:
        if x is None:
            return False
        x = x if isinstance(x, ScriptLine) else x.line
        if not (self._has_encoding * x.labels_encoding).sum().item() == self._has_encoding.sum().item():
            return False
        return (self._exclude_encoding * x.labels_encoding).sum().item() == 0


@dataclass
class ConditionWithCtx:
    line: Condition
    pre_ctx: Optional[list[Condition | None]] = None
    post_ctx: Optional[list[Condition | None]] = None

    def is_satified(self, x: ScriptLinePayload) -> bool:
        if not self.line.is_satified(x.line):
            return False
        for suffix in ["pre", "post"]:
            if conditions := getattr(self, f"{suffix}_ctx"):
                for condition, ctx in zip(conditions, getattr(x, f"{suffix}_ctx")):
                    if condition:
                        if not condition.is_satified(ctx):
                            return False
        return True


class Transform(ABC):
    def __init__(
        self,
        condition: Optional[Condition | ConditionWithCtx] = None,
        p: float = 0.5,
    ):
        if not (0.0 <= p <= 1.0):
            raise ValueError("`p` should be a floating point value in the interval [0.0, 1.0].")

        self.p = p
        self.condition = condition

    def should_apply(self, x: ScriptLinePayload) -> bool:
        if torch.rand(1) >= self.p:
            return False
        if self.condition is None:
            return True
        return self.condition.is_satified(x)

    @abstractmethod
    def apply(self, x: ScriptLinePayload) -> ScriptLinePayload:
        raise NotImplementedError

    def __call__(self, x: ScriptLinePayload) -> ScriptLinePayload:
        if not self.should_apply(x):
            return x
        return self.apply(x)


class Compose:
    def __init__(self, transforms: list[Transform]):
        self.transforms = transforms

    def __call__(self, x: ScriptLinePayload) -> ScriptLinePayload:
        for trf in self.transforms:
            x = trf(x)
        return x
