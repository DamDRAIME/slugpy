from collections import deque
from itertools import chain, islice
from pathlib import Path
from typing import Callable, Optional

import numpy as np
import torch
from torch.utils.data import DataLoader, IterableDataset, default_collate, get_worker_info

from slugpy.dataset.file_state import ScriptFileState
from slugpy.dataset.payload import ScriptLine, ScriptLinePayload

Label = str
Line = str


class Script(IterableDataset):
    def __init__(
        self,
        filepath: Path | str,
        ctx_size: int = 2,
        inference: bool = False,
        sep: str = "|",
        random_start: bool = True,
        transforms: Optional[list[Callable]] = None,
        iter_as_dict: bool = True,
        skip_empty_lines: bool = False,
        seed: int = 42,
    ):
        super().__init__()
        self.filepath = Path(filepath)
        self.ctx_size = ctx_size
        self.inference = inference
        self.sep = sep
        self.random_start = random_start
        self.transforms = [] if transforms is None else transforms
        self.iter_as_dict = iter_as_dict
        self.skip_empty_lines = skip_empty_lines
        self.seed = seed
        self.rng = np.random.default_rng(self.seed)
        self.state = ScriptFileState(self.filepath, self.ctx_size)

    def parse_line(self, line: str) -> tuple[Line, Optional[list[Label]]]:
        if self.inference:
            return line, None

        parts = line.split(self.sep, maxsplit=2)

        if len(parts) != 2:
            raise ValueError(f"Couldn't parse line: `{line}` at {self.filepath}, line {self.state.curr_idx}")

        labels, line = parts
        return line, labels.split(",")

    def build_payload(self, line_with_ctx: deque[Optional[str]]) -> ScriptLinePayload:
        for i, line in enumerate(line_with_ctx):
            if not line:
                line_with_ctx[i] = None
            else:
                line, labels = self.parse_line(line)
                line_with_ctx[i] = ScriptLine(line, -self.ctx_size - 1 + i + self.state.curr_idx, labels)

        return ScriptLinePayload(
            fname=self.state.fname,
            fpath=str(self.state.fpath),
            pre_ctx=[line_with_ctx.popleft() for _ in range(self.ctx_size)],
            line=line_with_ctx.popleft(),
            post_ctx=[line_with_ctx.popleft() for _ in range(self.ctx_size)],
        )

    def get_start_idx(self) -> int:
        if self.inference or not self.random_start:
            return 0
        return int(self.rng.integers(self.ctx_size - 1, self.state.nbr_lines - 1))

    def __iter__(self):
        with self.filepath.open("r", encoding="utf-8") as fh:
            self.state.fhandler = fh
            self.state.initialize_context(self.get_start_idx())

            while not self.state.exhausted:
                line_with_ctx = self.state.readline_with_ctx()
                payload = self.build_payload(line_with_ctx)

                for trf in self.transforms:
                    payload = trf(payload)

                if self.skip_empty_lines and not payload.line.line.strip():
                    pass
                else:
                    yield payload.to_dict() if self.iter_as_dict else payload

                if self.state.is_eof():
                    self.state.loop_back_to_bof()
            self.state.reset()  # Reset for next iteration/epoch with new start idx


class ScriptDataset(IterableDataset):
    def __init__(
        self,
        folder: Path | str,
        ctx_size: int = 2,
        inference: bool = False,
        sep: str = "|",
        shuffle: bool = True,
        random_start: bool = True,
        transforms: Optional[list[Callable]] = None,
        iter_as_dict: bool = True,
        skip_empty_lines: bool = False,
        seed: int = 42,
    ):
        super().__init__()
        self.seed = seed
        self.rng = np.random.default_rng(self.seed)
        self.sep = sep
        self.inference = inference
        self.shuffle = shuffle
        self.random_start = random_start
        self.transforms = [] if transforms is None else transforms
        self.ctx_size = ctx_size
        self.scripts = self.init_file_states(Path(folder), skip_empty_lines, iter_as_dict)

    def init_file_states(self, folder: Path, skip_empty_lines: bool, iter_as_dict: bool) -> dict[str, ScriptFileState]:
        scripts = {}
        for fp in folder.rglob("*.screenplay"):
            scripts[fp.stem] = Script(
                fp,
                ctx_size=self.ctx_size,
                inference=self.inference,
                sep=self.sep,
                random_start=self.random_start,
                transforms=self.transforms,
                iter_as_dict=iter_as_dict,
                skip_empty_lines=skip_empty_lines,
                seed=int(self.rng.integers(0, 200)),
            )
        return scripts

    def _get_stream(self):
        if self.inference or not self.shuffle:
            yield from chain.from_iterable(self.scripts.values())
        else:
            script_iterators = {key: iter(script) for key, script in self.scripts.items()}
            while script_iterators:
                key = self.rng.choice(list(script_iterators.keys()))
                try:
                    yield next(script_iterators[key])
                except StopIteration:  # Script was exhausted and got reset
                    script_iterators.pop(key)

    def __iter__(self):
        worker_info = get_worker_info()

        gen = self._get_stream()
        if worker_info is not None:  # Multi-process data loading
            worker_id = worker_info.id
            num_workers = worker_info.num_workers
            # Shard stream by line relative index
            gen = islice(gen, worker_id, None, num_workers)

        yield from gen


class ScriptDataLoader(DataLoader):
    def __init__(self, dataset: ScriptDataset, batch_size: int = 32, num_workers: int = 0):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        for script in dataset.scripts.values():
            script.iter_as_dict = True
            script.skip_empty_lines = True
        super().__init__(dataset, batch_size=batch_size, num_workers=num_workers, collate_fn=self.collate_fn)

    def collate_fn(self, data):
        batch = default_collate(data)
        # Transpose line_with_ctx to shape (B, 2*ctx_size+1) instead of (2*ctx_size+1, B)
        batch["line_with_ctx"] = [list(row) for row in zip(*batch["line_with_ctx"])]
        for k, v in batch.items():
            if issubclass(type(v), torch.Tensor):
                batch[k] = v.to(self.device)
        return batch
