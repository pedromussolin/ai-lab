"""Result reranker using cross-encoder or simple score combination."""

from app.rag.retriever import RetrievalResult


class SimpleReranker:
    """
    Simple score-based reranker that merges and deduplicates results
    from multiple retrieval sources.
    """

    def rerank(
        self,
        results: list[RetrievalResult],
        top_k: int = 5,
        min_score: float = 0.0,
    ) -> list[RetrievalResult]:
        """Deduplicate by content, sort by score, return top_k."""
        seen: set[str] = set()
        unique: list[RetrievalResult] = []
        for r in results:
            key = r.content[:200]  # use first 200 chars as dedup key
            if key not in seen:
                seen.add(key)
                unique.append(r)

        filtered = [r for r in unique if r.score >= min_score]
        filtered.sort(key=lambda x: x.score, reverse=True)
        return filtered[:top_k]
