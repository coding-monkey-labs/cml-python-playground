"""Analytics service — hotspots, reopen patterns, developer metrics, health scores."""

from engineering_intelligence.graph.repository import GraphRepository
from engineering_intelligence.repositories.jira_repo import JiraRepository
from engineering_intelligence.schemas.analytics import (
    DeveloperMetrics,
    FeatureHealthScore,
    HotspotFeature,
    ReopenPattern,
)


class AnalyticsService:
    def __init__(
        self,
        graph_repo: GraphRepository | None = None,
        jira_repo: JiraRepository | None = None,
    ) -> None:
        self._graph = graph_repo
        self._jira_repo = jira_repo

    async def get_hotspot_features(self, limit: int = 10) -> list[HotspotFeature]:
        if not self._graph:
            return []
        rows = await self._graph.get_hotspot_features(limit=limit)
        return [
            HotspotFeature(
                feature=r["feature"],
                defect_count=r["defect_count"],
                total_weight=r["total_weight"],
            )
            for r in rows
        ]

    async def get_reopen_patterns(self, limit: int = 10) -> list[ReopenPattern]:
        if not self._graph:
            return []
        rows = await self._graph.get_reopen_patterns(limit=limit)
        return [
            ReopenPattern(
                defect=r["defect"],
                reopened_from=r["reopened_from"],
                summary=r.get("summary", ""),
            )
            for r in rows
        ]

    async def get_developer_metrics(self, email: str) -> DeveloperMetrics:
        if self._graph:
            rows = await self._graph.get_developer_metrics(email)
            total = sum(r.get("count", 0) for r in rows)
            return DeveloperMetrics(
                email=email,
                total_issues=total,
                avg_resolution_hours=None,
                reopen_rate=0.0,
                fix_completeness=0.0,
            )
        return DeveloperMetrics(
            email=email,
            total_issues=0,
            avg_resolution_hours=None,
            reopen_rate=0.0,
            fix_completeness=0.0,
        )

    async def get_feature_health(self, feature_name: str) -> FeatureHealthScore:
        if self._graph:
            risk_data = await self._graph.get_feature_risk_score(feature_name)
            if risk_data:
                r = risk_data[0]
                defect_count = r.get("defect_count", 0)
                reopen_count = r.get("reopen_count", 0)
                risk_weight = r.get("risk_weight", 0) or 0
                density = defect_count / max(1, defect_count + 10)
                health = max(0.0, 100.0 - (defect_count * 5) - (reopen_count * 10))
                volatility = min(1.0, risk_weight / 100.0)
                regression = min(1.0, reopen_count / max(1, defect_count))
                return FeatureHealthScore(
                    feature_name=feature_name,
                    health_score=round(health, 2),
                    defect_density=round(density, 4),
                    volatility_score=round(volatility, 4),
                    regression_likelihood=round(regression, 4),
                )
        return FeatureHealthScore(
            feature_name=feature_name,
            health_score=100.0,
            defect_density=0.0,
            volatility_score=0.0,
            regression_likelihood=0.0,
        )
