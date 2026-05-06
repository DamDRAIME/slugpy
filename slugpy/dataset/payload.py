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

    def __len__(self) -> int:
        return 1 + (self.ctx_size * 2)

    @property
    def sequence_size(self) -> int:
        return len(self)

    @property
    def ctx_size(self) -> int:
        return len(self.pre_ctx)

    def to_dict(self) -> dict:
        return {
            "fname": self.fname,
            "fpath": str(self.fpath),
            "line": self.line.line,
            "idx": self.line.idx,
            "ctx_size": self.ctx_size,
            "line_with_ctx": self.content,
            "labels": self.line.labels_encoding,
        }
