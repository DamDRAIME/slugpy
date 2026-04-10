from dataclasses import dataclass, field
from typing import Optional

from torch import LongTensor

from slugpy.dataset.label import to_multi_hot_encoding


@dataclass
class ScriptLine:
    line: str
    idx: int
    labels: Optional[list[str]] = None
    labels_encoding: Optional[LongTensor] = field(init=False)

    def __post_init__(self):
        self.labels_encoding = None if self.labels is None else to_multi_hot_encoding(self.labels)


@dataclass
class ScriptLinePayload:
    fname: str
    fpath: str
    line: ScriptLine
    pre_ctx: list[Optional[ScriptLine]]
    post_ctx: list[Optional[ScriptLine]]
