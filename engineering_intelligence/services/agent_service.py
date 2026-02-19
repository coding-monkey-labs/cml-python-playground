"""Agent integration service — context, risk, duplicate check, review context for AI agents."""

from engineering_intelligence.graph.repository import GraphRepository
from engineering_intelligence.schemas.agent import (
    AgentContextRequest,
    AgentContextResponse,
    AgentDuplicateCheckRequest,
    AgentDuplicateCheckResponse,
    AgentReviewContextRequest,
    AgentReviewContextResponse,
    AgentRiskRequest,
    AgentRiskResponse,
)
from engineering_intelligence.services.rag_service import RAGService
from engineering_intelligence.schemas.rag import SimilarityQueryRequest


class AgentService:
    def __init__(
        self,
        graph_repo: GraphRepository | None = None,
        rag_service: RAGService | None = None,
    ) -> None:
        self._graph = graph_repo
        self._rag = rag_service

    async def get_context(self, request: AgentContextRequest) -> AgentContextResponse:
        defects: list[dict] = []
        reopens: list[dict] = []
        prs: list[dict] = []
        feature_summary: str | None = None

        if self._graph and request.feature_name:
            risk_data = await self._graph.get_feature_risk_score(request.feature_name)
            if risk_data:
                r = risk_data[0]
                feature_summary = (
                    f"Feature '{request.feature_name}': "
                    f"{r.get('defect_count', 0)} defects, "
                    f"{r.get('reopen_count', 0)} reopens"
                )

        if self._graph and request.jira_key:
            subtree = await self._graph.get_jira_subtree(request.jira_key)
            defects = subtree

        return AgentContextResponse(
            feature_summary=feature_summary,
            historical_defects=defects,
            reopen_history=reopens,
            pr_history=prs,
        )

    async def get_risk(self, request: AgentRiskRequest) -> AgentRiskResponse:
        defect_count = 0
        reopen_count = 0
        risk_score = 0.0
        patterns: list[str] = []

        if self._graph:
            risk_data = await self._graph.get_feature_risk_score(request.feature_name)
            if risk_data:
                r = risk_data[0]
                defect_count = r.get("defect_count", 0)
                reopen_count = r.get("reopen_count", 0)
                risk_weight = r.get("risk_weight", 0) or 0
                risk_score = min(10.0, risk_weight / 10.0)

            reopen_data = await self._graph.get_reopen_patterns(limit=5)
            patterns = [f"{r['defect']} reopened from {r['reopened_from']}"
                        for r in reopen_data]

        return AgentRiskResponse(
            feature_name=request.feature_name,
            risk_score=round(risk_score, 2),
            defect_count=defect_count,
            reopen_count=reopen_count,
            past_failure_patterns=patterns,
        )

    async def check_duplicate(
        self, request: AgentDuplicateCheckRequest
    ) -> AgentDuplicateCheckResponse:
        if not self._rag:
            return AgentDuplicateCheckResponse(
                similar_defects=[], highest_confidence=0.0
            )

        text = request.summary
        if request.description:
            text = f"{request.summary}\n\n{request.description}"

        result = await self._rag.similarity_search(
            SimilarityQueryRequest(text=text, n_results=5, filter_type="jira_issue")
        )

        similar = []
        max_conf = 0.0
        for r in result.results:
            conf = max(0.0, 1.0 - r.distance)
            max_conf = max(max_conf, conf)
            similar.append({
                "jira_key": r.metadata.get("jira_key", r.id) if r.metadata else r.id,
                "summary": r.document[:200],
                "confidence": round(conf, 3),
            })

        return AgentDuplicateCheckResponse(
            similar_defects=similar,
            highest_confidence=round(max_conf, 3),
        )

    async def get_review_context(
        self, request: AgentReviewContextRequest
    ) -> AgentReviewContextResponse:
        past_fixes: list[dict] = []
        jira_summaries: list[str] = []
        risk_areas: list[str] = []

        if self._graph and request.component_name:
            # Find issues affecting this component
            query = """
            MATCH (j)-[:AFFECTS_COMPONENT]->(c:Component {name: $name})
            OPTIONAL MATCH (p:PullRequest)-[:FIXES]->(j)
            RETURN j.key AS jira_key, j.summary AS summary,
                   p.number AS pr_number
            LIMIT 20
            """
            rows = await self._graph._client.execute_read(
                query, name=request.component_name
            )
            for r in rows:
                jira_summaries.append(f"{r.get('jira_key')}: {r.get('summary')}")
                if r.get("pr_number"):
                    past_fixes.append({
                        "pr_number": r["pr_number"],
                        "jira_key": r["jira_key"],
                    })

        return AgentReviewContextResponse(
            past_fixes=past_fixes,
            linked_jira_summaries=jira_summaries,
            risk_areas=risk_areas,
        )
