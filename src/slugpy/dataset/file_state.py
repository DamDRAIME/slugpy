from collections import deque
from copy import deepcopy
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, TextIO


@dataclass
class ScriptFileState:
    fpath: Path
    fname: str = field(init=False)
    ctx_size: int = 0
    nbr_lines: int = field(init=False)
    fhandler: TextIO = None
    start_idx: int = field(default=0, init=False)
    curr_idx: int = field(default=0, init=False)
    _ctx_cache: deque[Optional[str]] = field(default_factory=deque, init=False)
    _looped: bool = False

    def __post_init__(self) -> None:
        self.fname = self.fpath.stem
        with self.fpath.open("rb") as fh:
            self.nbr_lines = sum(1 for _ in fh)

    @property
    def exhausted(self) -> bool:
        return self._looped and self.curr_idx >= self.start_idx

    def readline_with_ctx(self) -> deque[Optional[str]]:
        lines_with_ctx = deepcopy(self._ctx_cache)

        # Update current index and context cache
        self.curr_idx += 1
        self._ctx_cache.popleft()
        self._ctx_cache.append(self.fhandler.readline().rstrip("\n"))

        return lines_with_ctx

    def initialize_context(self, start_idx: int) -> None:
        self.start_idx = start_idx
        self.skip_to_line(self.start_idx, init=True)

    def reset(self) -> None:
        self._looped = False
        self._ctx_cache = deque()
        self.fhandler.seek(0)
        self.start_idx = 0
        self.curr_idx = 0

    def is_eof(self) -> bool:
        return self.curr_idx >= self.nbr_lines

    def loop_back_to_bof(self) -> None:
        self._looped = True
        self.skip_to_line(0)

    def skip_to_line(self, idx: int, init: bool = False) -> None:
        if self.fhandler is None:
            raise ValueError("No File Handler set.")
        if idx > self.nbr_lines - 1:
            raise IndexError(f"Line Index {idx} out of range for script with {self.nbr_lines} lines.")

        if idx == self.curr_idx and not init:
            return

        self._ctx_cache.clear()

        idx_ctx_aware = idx - self.ctx_size

        while idx_ctx_aware < 0:
            self._ctx_cache.append(None)
            idx_ctx_aware += 1

        self._skip_to_line_without_ctx(idx_ctx_aware)

        while len(self._ctx_cache) < (self.ctx_size * 2) + 1:
            self._ctx_cache.append(self.fhandler.readline().rstrip("\n"))
        self.curr_idx = idx

    def _skip_to_line_without_ctx(self, idx: int) -> None:
        if idx == self.curr_idx:
            return

        if idx < self.curr_idx:
            self.fhandler.seek(0)
            self.curr_idx = 0
            if idx == 0:
                return

        for new_idx, _ in enumerate(self.fhandler, start=self.curr_idx + 1):
            if new_idx == idx:
                self.curr_idx = new_idx
                break
