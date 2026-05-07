"""Feature repository."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from engineering_intelligence.db.models import Feature


class FeatureRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_by_id(self, feature_id: int) -> Feature | None:
        result = await self._db.execute(
            select(Feature).where(Feature.id == feature_id)
        )
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> Feature | None:
        result = await self._db.execute(
            select(Feature).where(Feature.name == name)
        )
        return result.scalar_one_or_none()

    async def get_all(self) -> list[Feature]:
        result = await self._db.execute(
            select(Feature).options(selectinload(Feature.children))
        )
        return list(result.scalars().unique().all())

    async def get_root_features(self) -> list[Feature]:
        result = await self._db.execute(
            select(Feature)
            .where(Feature.parent_id.is_(None))
            .options(selectinload(Feature.children))
        )
        return list(result.scalars().unique().all())

    async def create(self, feature: Feature) -> Feature:
        self._db.add(feature)
        await self._db.flush()
        return feature

    async def update_health(self, feature_id: int, health_score: float,
                            defect_count: int) -> Feature | None:
        feature = await self.get_by_id(feature_id)
        if feature:
            feature.health_score = health_score
            feature.defect_count = defect_count
            await self._db.flush()
        return feature
