"""Neo4j graph database client."""

from functools import lru_cache

from neo4j import AsyncGraphDatabase, AsyncDriver

from engineering_intelligence.config import get_settings


class GraphClient:
    """Manages the Neo4j async driver lifecycle."""

    def __init__(self, uri: str, user: str, password: str) -> None:
        self._driver: AsyncDriver = AsyncGraphDatabase.driver(uri, auth=(user, password))

    async def close(self) -> None:
        await self._driver.close()

    async def execute_read(self, query: str, **params: object) -> list[dict]:
        async with self._driver.session() as session:
            result = await session.run(query, params)
            return [record.data() async for record in result]

    async def execute_write(self, query: str, **params: object) -> list[dict]:
        async with self._driver.session() as session:
            result = await session.run(query, params)
            return [record.data() async for record in result]

    async def ensure_constraints(self) -> None:
        """Create uniqueness constraints and indexes for graph nodes."""
        constraints = [
            "CREATE CONSTRAINT IF NOT EXISTS FOR (f:Feature) REQUIRE f.name IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (e:Epic) REQUIRE e.key IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (s:Story) REQUIRE s.key IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (t:Task) REQUIRE t.key IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (d:Defect) REQUIRE d.key IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (p:PullRequest) REQUIRE p.number IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (dev:Developer) REQUIRE dev.email IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (c:Component) REQUIRE c.name IS UNIQUE",
        ]
        async with self._driver.session() as session:
            for constraint in constraints:
                await session.run(constraint)


@lru_cache
def get_graph_client() -> GraphClient:
    settings = get_settings()
    return GraphClient(
        uri=settings.neo4j_uri,
        user=settings.neo4j_user,
        password=settings.neo4j_password,
    )
