"""Unit tests for the RAG chunker."""

import pytest

from app.rag.chunker import RecursiveChunker


class TestRecursiveChunker:
    def test_short_text_returns_single_chunk(self):
        chunker = RecursiveChunker(chunk_size=1000, chunk_overlap=100)
        text = "This is a short text that fits in one chunk."
        chunks = chunker.chunk(text)
        assert len(chunks) == 1
        assert chunks[0].content == text

    def test_long_text_is_split(self):
        chunker = RecursiveChunker(chunk_size=50, chunk_overlap=10)
        text = "word " * 200  # ~200 tokens
        chunks = chunker.chunk(text)
        assert len(chunks) > 1

    def test_chunk_metadata_is_preserved(self):
        chunker = RecursiveChunker(chunk_size=1000)
        chunks = chunker.chunk("Some text.", metadata={"source": "test.pdf"})
        assert chunks[0].metadata["source"] == "test.pdf"

    def test_empty_text_returns_no_chunks(self):
        chunker = RecursiveChunker()
        chunks = chunker.chunk("   ")
        assert len(chunks) == 0

    def test_chunk_indices_are_sequential(self):
        chunker = RecursiveChunker(chunk_size=50, chunk_overlap=5)
        text = "sentence. " * 100
        chunks = chunker.chunk(text)
        for i, chunk in enumerate(chunks):
            assert chunk.index == i
