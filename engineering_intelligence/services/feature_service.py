"""Feature service — feature graph and metrics."""

from sqlalchemy.ext.asyncio import AsyncSession

from engineering_intelligence.db.models import Feature
from engineering_intelligence.graph.repository import GraphRepository
from engineering_intelligence.repositories.feature_repo import FeatureRepository
from engineering_intelligence.schemas.features import (
    FeatureCreate,
    FeatureMetrics,
    FeatureResponse,
    FeatureTreeNode,
)


class FeatureService:
    def __init__(
        self,
        feature_repo: FeatureRepository,
        graph_repo: GraphRepository | None = None,
    ) -> None:
        self._repo = feature_repo
        self._graph = graph_repo

    async def create_feature(self, data: FeatureCreate) -> FeatureResponse:
        feature = Feature(
            name=data.name,
            description=data.description,
            file_path=data.file_path,
            parent_id=data.parent_id,
        )
        feature = await self._repo.create(feature)

        if self._graph:
            await self._graph.upsert_feature(
                name=feature.name,
                description=feature.description,
                file_path=feature.file_path,
            )
            if data.parent_id:
                parent = await self._repo.get_by_id(data.parent_id)
                if parent:
                    await self._graph.add_subfeature(parent.name, feature.name)

        return FeatureResponse.model_validate(feature)

    async def get_feature_tree(self) -> list[FeatureTreeNode]:
        if self._graph:
            rows = await self._graph.get_feature_tree()
            return [FeatureTreeNode(name=r["feature"], children=r["children"]) for r in rows]
        # Fallback to relational
        features = await self._repo.get_root_features()
        return [
            FeatureTreeNode(
                name=f.name,
                children=[c.name for c in f.children],
            )
            for f in features
        ]

    async def get_feature_metrics(self, feature_name: str) -> FeatureMetrics | None:
        feature = await self._repo.get_by_name(feature_name)
        if not feature:
            return None

        if self._graph:
            risk_data = await self._graph.get_feature_risk_score(feature_name)
            if risk_data:
                r = risk_data[0]
                defect_count = r.get("defect_count", 0)
                reopen_count = r.get("reopen_count", 0)
                density = defect_count / max(1, defect_count + 10)  # Normalized
                health = max(0, 100 - (defect_count * 5) - (reopen_count * 10))
                return FeatureMetrics(
                    feature_name=feature_name,
                    defect_count=defect_count,
                    reopen_count=reopen_count,
                    defect_density=density,
                    health_score=health,
                )

        return FeatureMetrics(
            feature_name=feature_name,
            defect_count=feature.defect_count,
            reopen_count=0,
            defect_density=0.0,
            health_score=feature.health_score,
        )

    async def get_defect_density(self, feature_name: str) -> float:
        metrics = await self.get_feature_metrics(feature_name)
        return metrics.defect_density if metrics else 0.0
