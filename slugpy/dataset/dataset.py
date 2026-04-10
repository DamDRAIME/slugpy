from collections import deque
from contextlib import ExitStack
from copy import deepcopy
from dataclasses import dataclass, field
from itertools import islice
from pathlib import Path
from typing import Callable, Optional, TextIO

import numpy as np
from torch import LongTensor
from torch.utils.data import IterableDataset, get_worker_info

from slugpy.dataset.label import to_multi_hot_encoding

LineIdx = int
Label = str
Line = str


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

    @property
    def exhausted(self) -> bool:
        return self._looped and self.curr_idx >= self.start_idx

    def readline_with_ctx(self) -> deque[Optional[str]]:
        lines_with_ctx = deepcopy(self._ctx_cache)

        # Update current index and context cache
        self.curr_idx += 1
        self._ctx_cache.popleft()
        self._ctx_cache.append(self.fhandler.readline())

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


@dataclass
class ScriptLine:
    line: Line
    idx: LineIdx
    labels: Optional[list[Label]] = None
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


class ScriptDataset(IterableDataset):
    def __init__(
        self,
        folder: Path | str,
        ctx_size: int = 2,
        sep: str = "|",
        shuffle: bool = True,
        transforms: Optional[list[Callable]] = None,
        seed: int = 42,
    ):
        super().__init__()
        self.seed = seed
        self.rng = np.random.default_rng(self.seed)
        self.sep = sep
        self.shuffle = shuffle
        self.transforms = [] if transforms is None else transforms
        self.ctx_size = ctx_size
        self.sfstates = self.init_file_states(Path(folder))

    def init_file_states(self, folder: Path) -> dict[str, ScriptFileState]:
        sfstates = {}
        for fp in folder.rglob("*.script"):
            with fp.open("rb") as fh:
                nbr_lines = sum(1 for _ in fh)
            sfstates[fp.stem] = ScriptFileState(fname=fp.stem, fpath=fp, nbr_lines=nbr_lines, ctx_size=self.ctx_size)
        return sfstates

    def sanitize_line(self, line: str) -> str:
        return line.rstrip("\n")

    def parse_line(self, line: str) -> tuple[LineIdx, list[Label], Line]:
        parts = line.split(self.sep, maxsplit=3)

        if len(parts) != 3:
            raise ValueError(f"Couldn't parse line index and labels from line: `{line}`")

        idx, labels, line = parts
        return int(idx), labels.split(","), self.sanitize_line(line)

    def line_with_ctx_to_payload(
        self, line_with_ctx: deque[Optional[str]], sfstate: ScriptFileState
    ) -> ScriptLinePayload:

        for i, line in enumerate(line_with_ctx):
            if not line:
                line_with_ctx[i] = None
            else:
                idx, labels, line = self.parse_line(line)
                line_with_ctx[i] = ScriptLine(line, idx, labels)

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
                line_with_ctx = sfstate.readline_with_ctx()
                payload = self.line_with_ctx_to_payload(line_with_ctx, sfstate)
                for trf in self.transforms:
                    payload = trf(payload)
                yield payload
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


class InferenceScript(IterableDataset):
    def __init__(self, filepath: Path | str, ctx_size: int = 2):
        super().__init__()
        self.filepath = Path(filepath)
        self.ctx_size = ctx_size

    def init_ctx_cache(self, fhandler: TextIO) -> deque[Optional[ScriptLine]]:
        ctx_cache = deque()
        for _ in range(self.ctx_size):
            ctx_cache.append(None)

        idx = self.ctx_size
        ctx_cache.append(ScriptLine(self.sanitize_line(fhandler.readline()), idx))
        idx += 1

        for _ in range(self.ctx_size):
            ctx_cache.append(ScriptLine(self.sanitize_line(fhandler.readline()), idx))
            idx += 1
        return ctx_cache

    def sanitize_line(self, line: str) -> Line:
        return line.rstrip("\n")

    def build_payload(self, ctx_cache: deque[Optional[ScriptLine]]) -> ScriptLinePayload:
        lines_with_ctx = deepcopy(ctx_cache)
        return ScriptLinePayload(
            fname=self.filepath.stem,
            fpath=self.filepath,
            pre_ctx=[lines_with_ctx.popleft() for _ in range(self.ctx_size)],
            line=lines_with_ctx.popleft(),
            post_ctx=[lines_with_ctx.popleft() for _ in range(self.ctx_size)],
        )

    def _get_stream(self):
        with self.filepath.open("r") as fh:
            ctx_cache = self.init_ctx_cache(fh)
            idx = len(ctx_cache)

            for line in fh:
                yield self.build_payload(ctx_cache)

                ctx_cache.popleft()
                ctx_cache.append(ScriptLine(self.sanitize_line(line), idx))
                idx += 1

            for _ in range(self.ctx_size + 1):
                yield self.build_payload(ctx_cache)

                ctx_cache.popleft()
                ctx_cache.append(None)
                idx += 1

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
