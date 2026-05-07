"""RAG service — similarity search, duplicate detection, defect summaries."""

from typing import Any

import httpx

from engineering_intelligence.config import get_settings
from engineering_intelligence.schemas.rag import (
    DuplicateCheckRequest,
    DuplicateCheckResponse,
    DuplicateCheckResult,
    SimilarityQueryRequest,
    SimilarityQueryResponse,
    SimilarityQueryResult,
)
from engineering_intelligence.vector.client import VectorStore


class RAGService:
    def __init__(self, vector_store: VectorStore) -> None:
        self._store = vector_store
        self._settings = get_settings()

    async def generate_embedding(self, text: str) -> list[float]:
        """Generate embedding via OpenAI API."""
        if not self._settings.openai_api_key:
            # Return zero vector as fallback when no API key
            return [0.0] * self._settings.embedding_dimensions

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://api.openai.com/v1/embeddings",
                headers={"Authorization": f"Bearer {self._settings.openai_api_key}"},
                json={
                    "model": self._settings.embedding_model,
                    "input": text,
                    "dimensions": self._settings.embedding_dimensions,
                },
                timeout=30.0,
            )
            resp.raise_for_status()
            data = resp.json()
            return data["data"][0]["embedding"]

    async def index_document(
        self,
        doc_id: str,
        text: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Generate embedding and store document in vector DB."""
        embedding = await self.generate_embedding(text)
        self._store.add_documents(
            ids=[doc_id],
            documents=[text],
            embeddings=[embedding],
            metadatas=[metadata] if metadata else None,
        )

    async def index_jira_issue(
        self,
        jira_key: str,
        summary: str,
        description: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Index a Jira issue for RAG."""
        text = summary
        if description:
            text = f"{summary}\n\n{description}"
        base_meta = {"jira_key": jira_key, "type": "jira_issue"}
        if metadata:
            base_meta.update(metadata)
        await self.index_document(f"jira:{jira_key}", text, base_meta)

    async def index_pr(
        self,
        pr_number: int,
        repo: str,
        title: str,
        description: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Index a PR for RAG."""
        text = title
        if description:
            text = f"{title}\n\n{description}"
        base_meta = {"pr_number": pr_number, "repo": repo, "type": "pull_request"}
        if metadata:
            base_meta.update(metadata)
        await self.index_document(f"pr:{repo}:{pr_number}", text, base_meta)

    async def similarity_search(
        self, request: SimilarityQueryRequest
    ) -> SimilarityQueryResponse:
        """Search for similar documents."""
        embedding = await self.generate_embedding(request.text)
        where = None
        if request.filter_type:
            where = {"type": request.filter_type}
        raw = self._store.similarity_search(
            query_embedding=embedding,
            n_results=request.n_results,
            where=where,
        )
        results = []
        if raw.get("ids") and raw["ids"][0]:
            for i, doc_id in enumerate(raw["ids"][0]):
                results.append(SimilarityQueryResult(
                    id=doc_id,
                    document=raw["documents"][0][i] if raw.get("documents") else "",
                    distance=raw["distances"][0][i] if raw.get("distances") else 0.0,
                    metadata=raw["metadatas"][0][i] if raw.get("metadatas") else None,
                ))
        return SimilarityQueryResponse(query=request.text, results=results)

    async def check_duplicates(
        self, request: DuplicateCheckRequest
    ) -> DuplicateCheckResponse:
        """Check for duplicate defects using similarity search."""
        text = request.summary
        if request.description:
            text = f"{request.summary}\n\n{request.description}"

        search_result = await self.similarity_search(
            SimilarityQueryRequest(text=text, n_results=5, filter_type="jira_issue")
        )

        duplicates = []
        for r in search_result.results:
            confidence = max(0.0, 1.0 - r.distance)
            jira_key = r.metadata.get("jira_key", r.id) if r.metadata else r.id
            duplicates.append(DuplicateCheckResult(
                jira_key=jira_key,
                summary=r.document[:200],
                confidence=round(confidence, 3),
                is_likely_duplicate=confidence >= request.threshold,
            ))

        return DuplicateCheckResponse(
            input_summary=request.summary,
            duplicates=duplicates,
        )

    def get_document_count(self) -> int:
        return self._store.count()
