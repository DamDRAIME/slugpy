from dataclasses import dataclass
from typing import Optional

from torch import LongTensor

from slugpy.dataset.label import to_multi_hot_encoding


@dataclass
class ScriptLine:
    line: str
    idx: int
    labels: Optional[list[str]] = None

    @property
    def labels_encoding(self) -> Optional[LongTensor]:
        return None if self.labels is None else to_multi_hot_encoding(self.labels)


@dataclass
class ScriptLinePayload:
    fname: str
    fpath: str
    line: ScriptLine
    pre_ctx: list[Optional[ScriptLine]]
    post_ctx: list[Optional[ScriptLine]]

    @property
    def content(self) -> list[str]:
        content = []
        for ctx in self.pre_ctx:
            content.append("" if ctx is None else ctx.line)
        content.append(self.line.line)
        for ctx in self.post_ctx:
            content.append("" if ctx is None else ctx.line)
        return content
