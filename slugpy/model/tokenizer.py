import torch
from transformers import AutoTokenizer, BatchEncoding

from slugpy.dataset.payload import ScriptLinePayload


class TokenizerWithCtx:
    def __init__(
        self,
        model_name: str = "microsoft/deberta-v3-base",
        max_len: int = 256,
        padding: str = "max_length",
        truncation: bool = True,
        use_fast: bool = True,
    ):
        self.model_name = model_name
        self.max_len = max_len
        self.padding = padding
        self.truncation = truncation
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name, use_fast=use_fast)
        # Special tokens to mark the target line in the input sequence (to distinguish it from its context lines)
        self.line_token_start = "<slt>"  # "slt" stands for 'script line target'
        self.line_token_end = "</slt>"
        special_tokens = {"extra_special_tokens": [self.line_token_start, self.line_token_end]}
        self.tokenizer.add_special_tokens(special_tokens)
        self.line_token_start_id = self.tokenizer.convert_tokens_to_ids(self.line_token_start)
        self.line_token_end_id = self.tokenizer.convert_tokens_to_ids(self.line_token_end)

    def __len__(self):
        return len(self.tokenizer)

    def __call__(
        self, x: ScriptLinePayload | str | list[list[str]], return_line_span_mask: bool = True
    ) -> BatchEncoding:
        if isinstance(x, ScriptLinePayload):
            prep_x = self._pre_process_slp_fn(x)
        elif isinstance(x, str):
            prep_x = self._pre_process_str_fn(x)
        elif isinstance(x, list):
            prep_x = self._pre_process_batch_fn(x)
        else:
            ValueError(f"Unsupported input type: {type(x)}")
        return self.encode(prep_x, return_line_span_mask=return_line_span_mask)

    def decode(self, token_ids: torch.Tensor, skip_special_tokens: bool = True) -> list[str]:
        return self.tokenizer.batch_decode(token_ids, skip_special_tokens=skip_special_tokens)

    def encode(self, x: str | list[str], return_line_span_mask: bool = True) -> BatchEncoding:
        encoding = self.tokenizer(
            x,
            max_length=self.max_len,
            padding=self.padding,
            truncation=self.truncation,
            return_tensors="pt",
        )
        encoding["line_start_idx"] = (encoding["input_ids"] == self.line_token_start_id).nonzero()[:, -1]
        encoding["line_end_idx"] = (encoding["input_ids"] == self.line_token_end_id).nonzero()[:, -1]
        if not return_line_span_mask:
            return encoding
        line_span_mask = torch.zeros_like(encoding["input_ids"], dtype=torch.uint8)
        for i in range(encoding["input_ids"].size(0)):
            start = encoding["line_start_idx"][i].item()
            end = encoding["line_end_idx"][i].item()
            line_span_mask[i, start + 1 : end] = 1  # exclude the special token itself
        encoding["line_span_mask"] = line_span_mask
        return encoding

    def _pre_process_slp_fn(self, x: ScriptLinePayload) -> str:
        return (
            "\n".join([x if x else "" for x in x.pre_ctx])
            + "\n"
            + f"{self.line_token_start} {x.line.line} {self.line_token_end}"
            + "\n"
            + "\n".join([x if x else "" for x in x.post_ctx])
        )

    def _pre_process_str_fn(self, x: str) -> str:
        return f"{self.line_token_start} {x} {self.line_token_end}"

    def _pre_process_batch_fn(self, x: list[list[str]]) -> list[str]:
        # Batch of lines (with context) - Shape: B, 2*ctx_size+1
        line_idx = len(x[0]) // 2
        for idx, lines_with_ctx in enumerate(x):
            x[idx] = "\n".join(
                lines_with_ctx[:line_idx]
                + [f"{self.line_token_start} {lines_with_ctx[line_idx]} {self.line_token_end}"]
                + lines_with_ctx[line_idx + 1 :]
            )
        return x
