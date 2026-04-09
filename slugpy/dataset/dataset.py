from collections import deque
from contextlib import ExitStack
from copy import deepcopy
from dataclasses import dataclass, field
from itertools import islice
from pathlib import Path
from typing import Optional, TextIO

import numpy as np
from torch import LongTensor
from torch.utils.data import IterableDataset, get_worker_info

from slugpy.dataset.label import to_one_hot_encoding


@dataclass
class ScriptFileState:
    fname: str
    fpath: Path
    nbr_lines: int
    ctx_size: int
    fhandler: TextIO = None
    start_idx: int = field(default=0, init=False)
    curr_idx: int = field(default=0, init=False)
    _ctx_cache: deque[Optional[str]] = field(default_factory=deque, init=False)
    _looped: bool = False

    def initialize_context(self, start_idx: int) -> None:
        self.start_idx = start_idx
        self.skip_to_line(self.start_idx, init=True)

    def reset(self) -> None:
        self._looped = False
        self._ctx_cache = deque()
        self.fhandler.seek(0)
        self.start_idx = 0
        self.curr_idx = 0

    @property
    def exhausted(self) -> bool:
        return self._looped and self.curr_idx >= self.start_idx

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

        for new_idx, line in enumerate(self.fhandler, start=self.curr_idx + 1):
            if new_idx == idx:
                self.curr_idx = new_idx
                break


@dataclass
class ScriptLine:
    line: str
    idx: int
    labels: list[str]
    labels_encoding: LongTensor


@dataclass
class ScriptLinePayload:
    fname: str
    fpath: str
    line: ScriptLine
    pre_ctx: list[Optional[ScriptLine]]
    post_ctx: list[Optional[ScriptLine]]


class ScriptDataset(IterableDataset):
    def __init__(
        self,
        folder: Path | str,
        train: bool = True,
        ctx_size: int = 2,
        sep: str = "|",
        shuffle: bool = True,
        seed: int = 42,
    ):
        super().__init__()
        self.train = train
        self.seed = seed
        self.rng = np.random.default_rng(self.seed)
        self.sep = sep
        self.shuffle = shuffle
        self.ctx_size = ctx_size
        self.sfstates = self.init_file_states(Path(folder))

    def resetreset(self) -> None:
        for sfstate in self.sfstates.values():
            idx = int(self.rng.integers(self.ctx_size - 1, sfstate.nbr_lines - 1))
            sfstate.reset(idx)

    def init_file_states(self, folder: Path) -> dict[str, ScriptFileState]:
        sfstates = {}
        for fp in folder.rglob("*.script"):
            with fp.open("rb") as fh:
                nbr_lines = sum(1 for _ in fh)
            sfstates[fp.stem] = ScriptFileState(fname=fp.stem, fpath=fp, nbr_lines=nbr_lines, ctx_size=self.ctx_size)
        return sfstates

    def parse_line(self, line: str) -> tuple[int, list[str], str]:
        parts = line.split(self.sep, maxsplit=3)

        if len(parts) != 3:
            raise ValueError(f"Couldn't parse line index and labels from line: `{line}`")

        idx, labels, line = parts
        return int(idx), labels.split(","), line.rstrip("\n")

    def read_line_with_ctx(self, sfstate: ScriptFileState) -> deque[Optional[str]]:
        lines_with_ctx = deepcopy(sfstate._ctx_cache)

        # Update current index and context cache
        sfstate.curr_idx += 1
        sfstate._ctx_cache.popleft()
        sfstate._ctx_cache.append(sfstate.fhandler.readline())

        return lines_with_ctx

    def line_with_ctx_to_payload(
        self, line_with_ctx: deque[Optional[str]], sfstate: ScriptFileState
    ) -> ScriptLinePayload:

        for i, line in enumerate(line_with_ctx):
            if not line:
                line_with_ctx[i] = None
            else:
                idx, labels, line = self.parse_line(line)
                line_with_ctx[i] = ScriptLine(line, idx, labels, to_one_hot_encoding(labels))

        return ScriptLinePayload(
            fname=sfstate.fname,
            fpath=sfstate.fpath,
            pre_ctx=[line_with_ctx.popleft() for _ in range(self.ctx_size)],
            line=line_with_ctx.popleft(),
            post_ctx=[line_with_ctx.popleft() for _ in range(self.ctx_size)],
        )

    def _get_stream(self):
        with ExitStack() as stack:
            for sfstate in self.sfstates.values():
                sfstate.fhandler = stack.enter_context(sfstate.fpath.open("r"))
                sfstate.initialize_context(int(self.rng.integers(sfstate.ctx_size - 1, sfstate.nbr_lines - 1)))
            while not all(sfstate.exhausted for sfstate in self.sfstates.values()):
                sfs_candidates = [sfs for sfs in self.sfstates.values() if not sfs.exhausted]
                sfstate: ScriptFileState = self.rng.choice(sfs_candidates) if self.shuffle else sfs_candidates.pop()
                line_with_ctx = self.read_line_with_ctx(sfstate)
                yield self.line_with_ctx_to_payload(line_with_ctx, sfstate)
                if sfstate.is_eof():
                    sfstate.loop_back_to_bof()
            for sfstate in self.sfstates.values():
                sfstate.reset()
            raise StopIteration

    def __iter__(self):
        worker_info = get_worker_info()

        gen = self._get_stream()
        if worker_info is not None:  # Multi-process data loading
            worker_id = worker_info.id
            num_workers = worker_info.num_workers
            # Shard stream by line relative index
            gen = islice(gen, worker_id, None, num_workers)

        return gen
