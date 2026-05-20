"""Text chunking strategies for document processing."""

from dataclasses import dataclass
from typing import Any

import tiktoken

_TOKENIZER = tiktoken.get_encoding("cl100k_base")


@dataclass
class TextChunk:
    content: str
    index: int
    token_count: int
    metadata: dict[str, Any]


class RecursiveChunker:
    """
    Recursive character text splitter with token-aware chunking.
    Splits on paragraphs, then sentences, then words.
    """

    SEPARATORS = ["\n\n", "\n", ". ", "! ", "? ", ", ", " ", ""]

    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200) -> None:
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def _count_tokens(self, text: str) -> int:
        return len(_TOKENIZER.encode(text))

    def _split_by_separator(self, text: str, separator: str) -> list[str]:
        if separator:
            parts = text.split(separator)
            return [p + separator for p in parts[:-1]] + [parts[-1]] if parts else []
        return list(text)

    def chunk(self, text: str, metadata: dict[str, Any] | None = None) -> list[TextChunk]:
        """Split text into overlapping chunks."""
        metadata = metadata or {}
        chunks: list[str] = []
        self._split_recursive(text, self.SEPARATORS, chunks)

        result = []
        for i, chunk_text in enumerate(chunks):
            token_count = self._count_tokens(chunk_text)
            result.append(
                TextChunk(
                    content=chunk_text.strip(),
                    index=i,
                    token_count=token_count,
                    metadata={**metadata, "chunk_index": i},
                )
            )
        return [c for c in result if c.content]  # filter empty chunks

    def _split_recursive(self, text: str, separators: list[str], result: list[str]) -> None:
        if not text.strip():
            return

        token_count = self._count_tokens(text)
        if token_count <= self.chunk_size:
            result.append(text)
            return

        sep = separators[0] if separators else ""
        remaining_seps = separators[1:] if len(separators) > 1 else []

        parts = text.split(sep) if sep else [text[i:i+4] for i in range(0, len(text), 4)]

        current = ""
        for part in parts:
            candidate = current + (sep if current else "") + part
            if self._count_tokens(candidate) > self.chunk_size and current:
                result.append(current)
                # Overlap: keep last N tokens worth of text
                overlap_text = self._get_overlap_text(current)
                current = overlap_text + (sep if overlap_text else "") + part
            else:
                current = candidate

        if current.strip():
            if self._count_tokens(current) > self.chunk_size and remaining_seps:
                self._split_recursive(current, remaining_seps, result)
            else:
                result.append(current)

    def _get_overlap_text(self, text: str) -> str:
        """Get the last `chunk_overlap` tokens of text for overlap."""
        tokens = _TOKENIZER.encode(text)
        if len(tokens) <= self.chunk_overlap:
            return text
        overlap_tokens = tokens[-self.chunk_overlap:]
        return _TOKENIZER.decode(overlap_tokens)
