"""Prompt compressor — deterministic token reduction before the LLM call.

A lightweight stand-in for LLMLingua-style compression: collapses redundant
whitespace and trims over-long context blocks while preserving the instruction.
Off by default; useful on the large fixed system prefixes Graphiti prompts carry.
"""
from __future__ import annotations

import re

_WS = re.compile(r"[ \t]{2,}")
_BLANK = re.compile(r"\n{3,}")
_EXAMPLES = re.compile(r"<<<EXAMPLES.*?>>>", re.DOTALL)


class PromptCompressor:
    """Quality-neutral input-token reduction.

    Two techniques, both safe because they don't change the instruction or the
    grounded input: (1) prune the few-shot EXAMPLES block (bounded by markers),
    (2) collapse redundant whitespace. Over-long messages are head/tail trimmed.
    """

    def __init__(self, max_chars_per_message: int = 6000, prune_examples: bool = True) -> None:
        self.max_chars = max_chars_per_message
        self.prune_examples = prune_examples

    def compress(self, messages: list[dict[str, str]]) -> list[dict[str, str]]:
        out: list[dict[str, str]] = []
        for m in messages:
            content = m.get("content", "")
            if self.prune_examples:
                content = _EXAMPLES.sub("", content)
            content = _WS.sub(" ", content)
            content = _BLANK.sub("\n\n", content).strip()
            if len(content) > self.max_chars:
                head = content[: int(self.max_chars * 0.7)]
                tail = content[-int(self.max_chars * 0.3):]
                content = f"{head}\n…[compressed]…\n{tail}"
            out.append({**m, "content": content})
        return out
