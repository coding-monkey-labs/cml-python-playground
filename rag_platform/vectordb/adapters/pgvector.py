"""PostgreSQL + pgvector adapter."""

from typing import Any

import asyncpg

from rag_platform.core.config import get_settings
from rag_platform.core.exceptions import VectorDBConnectionError, VectorDBOperationError
from rag_platform.core.logging import get_logger
from rag_platform.vectordb.base import (
    CollectionInfo,
    VectorDBAdapter,
    VectorDocument,
    VectorSearchResult,
)

logger = get_logger(__name__)


class PgvectorAdapter(VectorDBAdapter):
    """Adapter for PostgreSQL with pgvector extension.

    Uses a separate connection pool to the pgvector-enabled PostgreSQL.
    Each collection maps to a table: rag_vec_{collection_name}.
    """

    def __init__(self, pool: asyncpg.Pool | None = None):
        self._pool = pool
        self._settings = get_settings()

    async def _get_pool(self) -> asyncpg.Pool:
        """Lazily create the connection pool."""
        if self._pool is None:
            # Convert asyncpg URL from SQLAlchemy format
            dsn = self._settings.pgvector_url
            self._pool = await asyncpg.create_pool(dsn, min_size=2, max_size=10)
            # Ensure pgvector extension exists
            async with self._pool.acquire() as conn:
                await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
        return self._pool

    def _table_name(self, collection: str) -> str:
        """Sanitize collection name for use as table name."""
        safe = collection.replace("-", "_").replace(" ", "_").lower()
        return f"rag_vec_{safe}"

    async def create_collection(
        self, name: str, dimension: int, metadata: dict[str, Any] | None = None
    ) -> None:
        try:
            pool = await self._get_pool()
            table = self._table_name(name)
            async with pool.acquire() as conn:
                await conn.execute(f"""
                    CREATE TABLE IF NOT EXISTS {table} (
                        id TEXT PRIMARY KEY,
                        content TEXT NOT NULL,
                        embedding vector({dimension}),
                        metadata JSONB DEFAULT '{{}}'::jsonb,
                        created_at TIMESTAMPTZ DEFAULT NOW()
                    )
                """)
                await conn.execute(f"""
                    CREATE INDEX IF NOT EXISTS idx_{table}_embedding
                    ON {table} USING ivfflat (embedding vector_cosine_ops)
                    WITH (lists = 100)
                """)
            logger.info("Created pgvector table", table=table, dimension=dimension)
        except Exception as e:
            raise VectorDBOperationError(
                f"Failed to create pgvector collection '{name}': {e}"
            ) from e

    async def delete_collection(self, name: str) -> None:
        try:
            pool = await self._get_pool()
            table = self._table_name(name)
            async with pool.acquire() as conn:
                await conn.execute(f"DROP TABLE IF EXISTS {table}")
            logger.info("Deleted pgvector table", table=table)
        except Exception as e:
            raise VectorDBOperationError(
                f"Failed to delete pgvector collection '{name}': {e}"
            ) from e

    async def collection_exists(self, name: str) -> bool:
        try:
            pool = await self._get_pool()
            table = self._table_name(name)
            async with pool.acquire() as conn:
                result = await conn.fetchval(
                    "SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = $1)",
                    table,
                )
                return result
        except Exception as e:
            raise VectorDBConnectionError(
                f"Failed to check pgvector collection existence: {e}"
            ) from e

    async def get_collection_info(self, name: str) -> CollectionInfo:
        try:
            pool = await self._get_pool()
            table = self._table_name(name)
            async with pool.acquire() as conn:
                count = await conn.fetchval(f"SELECT COUNT(*) FROM {table}")
                return CollectionInfo(
                    name=name,
                    document_count=count or 0,
                    dimension=0,
                    metadata={"table_name": table, "type": "pgvector"},
                )
        except Exception as e:
            raise VectorDBOperationError(
                f"Failed to get pgvector collection info for '{name}': {e}"
            ) from e

    async def insert_documents(self, collection: str, documents: list[VectorDocument]) -> int:
        try:
            import json

            pool = await self._get_pool()
            table = self._table_name(collection)
            async with pool.acquire() as conn:
                for doc in documents:
                    embedding_str = "[" + ",".join(str(x) for x in doc.embedding) + "]"
                    await conn.execute(
                        f"""
                        INSERT INTO {table} (id, content, embedding, metadata)
                        VALUES ($1, $2, $3::vector, $4::jsonb)
                        ON CONFLICT (id) DO UPDATE SET
                            content = EXCLUDED.content,
                            embedding = EXCLUDED.embedding,
                            metadata = EXCLUDED.metadata
                        """,
                        doc.id,
                        doc.content,
                        embedding_str,
                        json.dumps(doc.metadata),
                    )
            logger.info(
                "Inserted documents into pgvector",
                collection=collection,
                count=len(documents),
            )
            return len(documents)
        except Exception as e:
            raise VectorDBOperationError(
                f"Failed to insert into pgvector collection '{collection}': {e}"
            ) from e

    async def delete_documents(self, collection: str, ids: list[str]) -> int:
        try:
            pool = await self._get_pool()
            table = self._table_name(collection)
            async with pool.acquire() as conn:
                result = await conn.execute(
                    f"DELETE FROM {table} WHERE id = ANY($1)", ids
                )
                count = int(result.split()[-1])
            logger.info("Deleted documents from pgvector", collection=collection, count=count)
            return count
        except Exception as e:
            raise VectorDBOperationError(
                f"Failed to delete from pgvector collection '{collection}': {e}"
            ) from e

    async def delete_by_metadata(self, collection: str, metadata_filter: dict[str, Any]) -> int:
        try:
            import json

            pool = await self._get_pool()
            table = self._table_name(collection)

            # Build JSONB containment query
            filter_json = json.dumps(metadata_filter)
            async with pool.acquire() as conn:
                result = await conn.execute(
                    f"DELETE FROM {table} WHERE metadata @> $1::jsonb",
                    filter_json,
                )
                count = int(result.split()[-1])

            logger.info(
                "Deleted by metadata from pgvector",
                collection=collection,
                count=count,
            )
            return count
        except Exception as e:
            raise VectorDBOperationError(
                f"Failed to delete by metadata from pgvector '{collection}': {e}"
            ) from e

    async def query(
        self,
        collection: str,
        query_embedding: list[float],
        top_k: int = 10,
        metadata_filter: dict[str, Any] | None = None,
    ) -> list[VectorSearchResult]:
        try:
            import json

            pool = await self._get_pool()
            table = self._table_name(collection)
            embedding_str = "[" + ",".join(str(x) for x in query_embedding) + "]"

            query_sql = f"""
                SELECT id, content, metadata,
                       1 - (embedding <=> $1::vector) as score
                FROM {table}
            """
            params: list[Any] = [embedding_str]

            if metadata_filter:
                filter_json = json.dumps(metadata_filter)
                query_sql += " WHERE metadata @> $2::jsonb"
                params.append(filter_json)

            query_sql += " ORDER BY embedding <=> $1::vector LIMIT $" + str(len(params) + 1)
            params.append(top_k)

            async with pool.acquire() as conn:
                rows = await conn.fetch(query_sql, *params)

            search_results = []
            for row in rows:
                meta = json.loads(row["metadata"]) if row["metadata"] else {}
                search_results.append(
                    VectorSearchResult(
                        id=row["id"],
                        content=row["content"],
                        score=float(row["score"]),
                        metadata=meta,
                    )
                )

            return search_results
        except Exception as e:
            raise VectorDBOperationError(
                f"Failed to query pgvector collection '{collection}': {e}"
            ) from e

    async def health_check(self) -> dict[str, Any]:
        try:
            pool = await self._get_pool()
            async with pool.acquire() as conn:
                version = await conn.fetchval("SELECT version()")
                has_vector = await conn.fetchval(
                    "SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'vector')"
                )
            return {
                "status": "healthy",
                "type": "pgvector",
                "pg_version": version,
                "pgvector_installed": has_vector,
            }
        except Exception as e:
            return {"status": "unhealthy", "type": "pgvector", "error": str(e)}

    async def get_document_count(self, collection: str) -> int:
        try:
            pool = await self._get_pool()
            table = self._table_name(collection)
            async with pool.acquire() as conn:
                count = await conn.fetchval(f"SELECT COUNT(*) FROM {table}")
                return count or 0
        except Exception as e:
            raise VectorDBOperationError(
                f"Failed to get document count for pgvector '{collection}': {e}"
            ) from e
