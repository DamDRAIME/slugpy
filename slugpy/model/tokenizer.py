from transformers import DebertaV3TokenizerFast

from slugpy.dataset.payload import ScriptLinePayload


class TokenizerWithCtx:
    def __init__(
        self,
        model_name: str = "microsoft/deberta-v3-base",
        max_len: int = 256,
        padding: str = "max_length",
        truncation: bool = True,
    ):
        self.model_name = model_name
        self.max_len = max_len
        self.padding = padding
        self.truncation = truncation
        self.tokenizer = DebertaV3TokenizerFast.from_pretrained(self.model_name)
        # Special tokens to mark the target line in the input sequence (to distinguish it from its context lines)
        self.line_token_start = "<slt>"
        self.line_token_end = "</slt>"
        special_tokens = {"script_line_target": [self.line_token_start, self.line_token_end]}
        self.tokenizer.add_special_tokens(special_tokens)
        self.line_token_start_id = self.tokenizer.convert_tokens_to_ids(self.line_token_start)
        self.line_token_end_id = self.tokenizer.convert_tokens_to_ids(self.line_token_end)

    def __len__(self):
        return len(self.tokenizer)

    def __call__(self, x: ScriptLinePayload):
        if isinstance(x, ScriptLinePayload):
            return self._forward_slp_fn(x)
        if isinstance(x, str):
            return self._forward_str_fn(x)
        if isinstance(x, list):
            return self._forward_batch_fn(x)
        raise ValueError(f"Unsupported input type: {type(x)}")

    def forward(self, x: str):
        return self.tokenizer(
            x,
            max_length=self.max_len,
            padding=self.padding,
            truncation=self.truncation,
            return_tensors="pt",
        )

    def _forward_slp_fn(self, x: ScriptLinePayload):
        script_line_with_ctx = (
            "\n".join(x.pre_ctx) + "\n" + f"<slt> {x.line.line} </slt>" + "\n" + "\n".join(x.post_ctx)
        )
        return self.forward(script_line_with_ctx)

    def _forward_str_fn(self, x: str):
        return self.forward(f"<slt> {x} </slt>")

    def _forward_batch_fn(self, x: list[list[str]]):
        # Batch of lines (with context) - Shape: B, 2*ctx_size+1
        line_idx = len(x[0]) // 2
        for idx, lines_with_ctx in enumerate(x):
            x[idx] = "\n".join(
                lines_with_ctx[:line_idx]
                + [f"<slt> {lines_with_ctx[line_idx]} </slt>"]
                + lines_with_ctx[line_idx + 1 :]
            )
        return [self.forward(line) for line in x]
