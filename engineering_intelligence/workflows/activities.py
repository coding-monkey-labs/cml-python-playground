"""Temporal activity definitions — the actual work units invoked by workflows."""

from dataclasses import dataclass

from temporalio import activity

from engineering_intelligence.config import get_settings


@dataclass
class JiraIngestionInput:
    epic_keys: list[str]


@dataclass
class PRIngestionInput:
    repo: str
    pr_numbers: list[int] | None = None


@dataclass
class HotspotComputeInput:
    feature_names: list[str] | None = None


@dataclass
class RAGRebuildInput:
    collection_name: str | None = None


# ── Jira Activities ────────────────────────────────────────────────────────────


@activity.defn
async def fetch_jira_issues(input: JiraIngestionInput) -> dict:
    """Fetch Jira issues for given epic keys from Jira API and persist to DB."""
    from engineering_intelligence.db.session import async_session_factory
    from engineering_intelligence.graph.client import GraphClient
    from engineering_intelligence.graph.repository import GraphRepository
    from engineering_intelligence.repositories.jira_repo import JiraRepository
    from engineering_intelligence.services.jira_service import JiraService

    settings = get_settings()
    total_fetched = 0

    async with async_session_factory() as db:
        jira_repo = JiraRepository(db)
        try:
            graph_client = GraphClient(settings.neo4j_uri, settings.neo4j_user, settings.neo4j_password)
            graph_repo = GraphRepository(graph_client)
        except Exception:
            graph_repo = None

        service = JiraService(jira_repo, graph_repo)

        for epic_key in input.epic_keys:
            activity.logger.info(f"Fetching Jira issues for epic: {epic_key}")
            issues = await service.fetch_from_jira_api(epic_key)
            for issue_data in issues:
                await service.upsert_issue(issue_data)
                total_fetched += 1
            activity.heartbeat(f"Processed epic {epic_key}: {len(issues)} issues")

        await db.commit()

        if graph_repo:
            try:
                await graph_client.close()
            except Exception:
                pass

    return {"epics_processed": len(input.epic_keys), "issues_fetched": total_fetched}


@activity.defn
async def update_jira_graph(input: JiraIngestionInput) -> dict:
    """Rebuild the Jira knowledge graph for given epics from DB state."""
    from engineering_intelligence.db.session import async_session_factory
    from engineering_intelligence.graph.client import GraphClient
    from engineering_intelligence.graph.repository import GraphRepository
    from engineering_intelligence.repositories.jira_repo import JiraRepository

    settings = get_settings()
    nodes_updated = 0

    async with async_session_factory() as db:
        jira_repo = JiraRepository(db)
        try:
            graph_client = GraphClient(settings.neo4j_uri, settings.neo4j_user, settings.neo4j_password)
            graph_repo = GraphRepository(graph_client)
        except Exception:
            activity.logger.warning("Neo4j unavailable, skipping graph update")
            return {"status": "skipped", "reason": "neo4j_unavailable"}

        try:
            for epic_key in input.epic_keys:
                issues = await jira_repo.get_by_epic(epic_key)
                for issue in issues:
                    await graph_repo.upsert_jira_node(
                        key=issue.jira_key,
                        issue_type=issue.issue_type.value,
                        summary=issue.summary,
                        status=issue.status.value,
                        severity=issue.severity,
                    )
                    if issue.epic_key:
                        await graph_repo.link_epic_child(
                            epic_key=issue.epic_key,
                            child_key=issue.jira_key,
                            child_type=issue.issue_type.value,
                        )
                    if issue.assignee_email:
                        await graph_repo.link_developer(
                            email=issue.assignee_email, jira_key=issue.jira_key
                        )
                    nodes_updated += 1
                activity.heartbeat(f"Graph updated for epic {epic_key}")
        finally:
            await graph_client.close()

    return {"status": "graph_updated", "nodes_updated": nodes_updated}


@activity.defn
async def generate_jira_embeddings(input: JiraIngestionInput) -> dict:
    """Generate embeddings for Jira issues and store in vector DB."""
    from engineering_intelligence.db.session import async_session_factory
    from engineering_intelligence.repositories.jira_repo import JiraRepository
    from engineering_intelligence.services.rag_service import RAGService
    from engineering_intelligence.vector.client import VectorStore

    settings = get_settings()
    indexed = 0

    async with async_session_factory() as db:
        jira_repo = JiraRepository(db)
        try:
            store = VectorStore(settings.chroma_host, settings.chroma_port, settings.chroma_collection)
            rag_service = RAGService(store)
        except Exception:
            activity.logger.warning("ChromaDB unavailable, skipping embedding generation")
            return {"status": "skipped", "reason": "chromadb_unavailable"}

        for epic_key in input.epic_keys:
            issues = await jira_repo.get_by_epic(epic_key)
            for issue in issues:
                await rag_service.index_jira_issue(
                    jira_key=issue.jira_key,
                    summary=issue.summary,
                    description=issue.description,
                    metadata={
                        "issue_type": issue.issue_type.value,
                        "status": issue.status.value,
                        "epic_key": issue.epic_key or "",
                        "severity": issue.severity or "",
                    },
                )
                indexed += 1
            activity.heartbeat(f"Embeddings generated for epic {epic_key}")

    return {"status": "embeddings_generated", "documents_indexed": indexed}


# ── PR Activities ──────────────────────────────────────────────────────────────


@activity.defn
async def fetch_pr_metadata(input: PRIngestionInput) -> dict:
    """Fetch PR metadata from GitHub API and persist to DB."""
    from engineering_intelligence.db.session import async_session_factory
    from engineering_intelligence.repositories.jira_repo import JiraRepository
    from engineering_intelligence.repositories.pr_repo import PRRepository
    from engineering_intelligence.services.github_service import GitHubService
    from engineering_intelligence.services.pr_service import PRService

    parts = input.repo.split("/")
    if len(parts) != 2:
        return {"status": "error", "reason": f"Invalid repo format: {input.repo}"}
    owner, repo = parts

    github = GitHubService()
    total_fetched = 0

    async with async_session_factory() as db:
        pr_repo = PRRepository(db)
        jira_repo = JiraRepository(db)
        pr_service = PRService(pr_repo, jira_repo)

        if input.pr_numbers:
            for pr_num in input.pr_numbers:
                pr_data = await github.fetch_pr_with_details(owner, repo, pr_num)
                if pr_data:
                    await pr_service.upsert_pr(pr_data)
                    total_fetched += 1
                activity.heartbeat(f"Fetched PR #{pr_num}")
        else:
            # Fetch recent PRs (paginated)
            page = 1
            while True:
                prs = await github.fetch_prs(owner, repo, per_page=100, page=page)
                if not prs:
                    break
                for pr_data in prs:
                    await pr_service.upsert_pr(pr_data)
                    total_fetched += 1
                activity.heartbeat(f"Fetched page {page}: {len(prs)} PRs")
                if len(prs) < 100:
                    break
                page += 1

        await db.commit()

    return {"repo": input.repo, "prs_fetched": total_fetched}


@activity.defn
async def extract_pr_jira_mappings(input: PRIngestionInput) -> dict:
    """Extract Jira issue keys from PR titles/descriptions and create mappings."""
    from engineering_intelligence.db.session import async_session_factory
    from engineering_intelligence.repositories.jira_repo import JiraRepository
    from engineering_intelligence.repositories.pr_repo import PRRepository
    from engineering_intelligence.services.jira_service import JiraService

    mappings_created = 0

    async with async_session_factory() as db:
        pr_repo = PRRepository(db)
        jira_repo = JiraRepository(db)

        prs = await pr_repo.search(repo=input.repo, limit=1000)
        for pr in prs:
            text = f"{pr.title} {pr.description or ''}"
            jira_keys = JiraService.extract_jira_keys(text)
            for key in jira_keys:
                jira_issue = await jira_repo.get_by_key(key)
                if jira_issue:
                    existing = await pr_repo.get_mappings(pr.id)
                    already_mapped = {m.jira_issue_id for m in existing}
                    if jira_issue.id not in already_mapped:
                        await pr_repo.add_jira_mapping(
                            pr_id=pr.id,
                            jira_issue_id=jira_issue.id,
                            mapping_type="explicit",
                        )
                        mappings_created += 1
            activity.heartbeat(f"Processed PR #{pr.pr_number}")

        await db.commit()

    return {"status": "mappings_extracted", "mappings_created": mappings_created}


@activity.defn
async def infer_pr_jira_mappings(input: PRIngestionInput) -> dict:
    """Use embedding similarity to infer PR-Jira mappings when explicit keys are missing."""
    from engineering_intelligence.db.session import async_session_factory
    from engineering_intelligence.repositories.jira_repo import JiraRepository
    from engineering_intelligence.repositories.pr_repo import PRRepository
    from engineering_intelligence.services.jira_service import JiraService
    from engineering_intelligence.services.rag_service import RAGService
    from engineering_intelligence.vector.client import VectorStore
    from engineering_intelligence.schemas.rag import SimilarityQueryRequest

    settings = get_settings()
    inferred = 0

    async with async_session_factory() as db:
        pr_repo = PRRepository(db)
        jira_repo = JiraRepository(db)

        try:
            store = VectorStore(settings.chroma_host, settings.chroma_port, settings.chroma_collection)
            rag_service = RAGService(store)
        except Exception:
            return {"status": "skipped", "reason": "chromadb_unavailable"}

        prs = await pr_repo.search(repo=input.repo, limit=1000)
        for pr in prs:
            # Skip PRs that already have explicit mappings
            text = f"{pr.title} {pr.description or ''}"
            explicit_keys = JiraService.extract_jira_keys(text)
            if explicit_keys:
                continue

            # Use similarity search to find related Jira issues
            search_result = await rag_service.similarity_search(
                SimilarityQueryRequest(text=text, n_results=3, filter_type="jira_issue")
            )

            for result in search_result.results:
                confidence = max(0.0, 1.0 - result.distance)
                if confidence >= 0.75 and result.metadata:
                    jira_key = result.metadata.get("jira_key")
                    if jira_key:
                        issue = await jira_repo.get_by_key(jira_key)
                        if issue:
                            await pr_repo.add_jira_mapping(
                                pr_id=pr.id,
                                jira_issue_id=issue.id,
                                mapping_type="inferred",
                                confidence=round(confidence, 3),
                            )
                            inferred += 1
            activity.heartbeat(f"Inferred mappings for PR #{pr.pr_number}")

        await db.commit()

    return {"status": "inferred_mappings_completed", "inferred_count": inferred}


# ── Feature Graph Activities ──────────────────────────────────────────────────


@activity.defn
async def parse_react_codebase(codebase_path: str) -> dict:
    """Parse React codebase to detect components, routes, modules."""
    from engineering_intelligence.services.feature_parser import parse_codebase

    activity.logger.info(f"Parsing React codebase at: {codebase_path}")
    result = parse_codebase(codebase_path)
    activity.logger.info(
        f"Found {len(result.components)} components, "
        f"{len(result.routes)} routes, "
        f"{len(result.feature_groups)} feature groups"
    )
    return result.to_dict()


@activity.defn
async def build_feature_hierarchy(parsed_data: dict) -> dict:
    """Build Feature -> SubFeature hierarchy from parsed data and persist to graph + DB."""
    from engineering_intelligence.db.session import async_session_factory
    from engineering_intelligence.graph.client import GraphClient
    from engineering_intelligence.graph.repository import GraphRepository
    from engineering_intelligence.repositories.feature_repo import FeatureRepository
    from engineering_intelligence.db.models import Feature

    settings = get_settings()
    features_created = 0

    feature_groups = parsed_data.get("feature_groups", {})

    async with async_session_factory() as db:
        feature_repo = FeatureRepository(db)

        try:
            graph_client = GraphClient(settings.neo4j_uri, settings.neo4j_user, settings.neo4j_password)
            graph_repo = GraphRepository(graph_client)
        except Exception:
            graph_repo = None

        try:
            for group_name, component_names in feature_groups.items():
                # Create parent feature
                parent = await feature_repo.get_by_name(group_name)
                if not parent:
                    parent = await feature_repo.create(Feature(name=group_name))
                    features_created += 1

                if graph_repo:
                    await graph_repo.upsert_feature(name=group_name)

                # Create child features (individual components)
                for comp_name in component_names:
                    child = await feature_repo.get_by_name(comp_name)
                    if not child:
                        child = await feature_repo.create(
                            Feature(name=comp_name, parent_id=parent.id)
                        )
                        features_created += 1

                    if graph_repo:
                        await graph_repo.upsert_feature(name=comp_name)
                        await graph_repo.add_subfeature(group_name, comp_name)

                activity.heartbeat(f"Built hierarchy for {group_name}")

            await db.commit()
        finally:
            if graph_repo:
                try:
                    await graph_client.close()
                except Exception:
                    pass

    return {"status": "hierarchy_built", "features_created": features_created}


# ── Analytics Activities ───────────────────────────────────────────────────────


@activity.defn
async def compute_hotspots(input: HotspotComputeInput) -> dict:
    """Compute defect hotspots, reopen frequency, defect density per feature."""
    from engineering_intelligence.db.session import async_session_factory
    from engineering_intelligence.graph.client import GraphClient
    from engineering_intelligence.graph.repository import GraphRepository
    from engineering_intelligence.repositories.feature_repo import FeatureRepository
    from engineering_intelligence.repositories.jira_repo import JiraRepository

    settings = get_settings()

    async with async_session_factory() as db:
        feature_repo = FeatureRepository(db)
        jira_repo = JiraRepository(db)

        try:
            graph_client = GraphClient(settings.neo4j_uri, settings.neo4j_user, settings.neo4j_password)
            graph_repo = GraphRepository(graph_client)
        except Exception:
            graph_repo = None

        try:
            # Aggregate defect counts
            defect_stats = await jira_repo.count_defects_by_feature()
            activity.logger.info(f"Computed defect stats for {len(defect_stats)} groups")

            # Update feature health scores
            if input.feature_names:
                features_to_process = []
                for name in input.feature_names:
                    f = await feature_repo.get_by_name(name)
                    if f:
                        features_to_process.append(f)
            else:
                features_to_process = await feature_repo.get_all()

            for feature in features_to_process:
                if graph_repo:
                    risk_data = await graph_repo.get_feature_risk_score(feature.name)
                    if risk_data:
                        r = risk_data[0]
                        defect_count = r.get("defect_count", 0)
                        reopen_count = r.get("reopen_count", 0)
                        health = max(0.0, 100.0 - (defect_count * 5) - (reopen_count * 10))
                        await feature_repo.update_health(feature.id, health, defect_count)
                activity.heartbeat(f"Updated health for {feature.name}")

            await db.commit()
        finally:
            if graph_repo:
                try:
                    await graph_client.close()
                except Exception:
                    pass

    return {"status": "hotspots_computed", "features_processed": len(features_to_process)}


@activity.defn
async def detect_reopen_patterns(input: HotspotComputeInput) -> dict:
    """Detect repeated defect clusters and recurring root causes via graph analysis."""
    from engineering_intelligence.graph.client import GraphClient
    from engineering_intelligence.graph.repository import GraphRepository

    settings = get_settings()

    try:
        graph_client = GraphClient(settings.neo4j_uri, settings.neo4j_user, settings.neo4j_password)
        graph_repo = GraphRepository(graph_client)
    except Exception:
        return {"status": "skipped", "reason": "neo4j_unavailable"}

    try:
        patterns = await graph_repo.get_reopen_patterns(limit=50)
        activity.logger.info(f"Found {len(patterns)} reopen patterns")

        # Detect clusters: defects that share common reopened-from ancestors
        clusters: dict[str, list[str]] = {}
        for p in patterns:
            root = p.get("reopened_from", "")
            defect = p.get("defect", "")
            if root not in clusters:
                clusters[root] = []
            clusters[root].append(defect)

        recurring = {k: v for k, v in clusters.items() if len(v) >= 2}
        activity.logger.info(f"Found {len(recurring)} recurring defect clusters")
    finally:
        await graph_client.close()

    return {
        "status": "patterns_detected",
        "total_patterns": len(patterns),
        "recurring_clusters": len(recurring),
    }


@activity.defn
async def update_graph_weights(input: HotspotComputeInput) -> dict:
    """Update graph edge weights based on computed metrics."""
    from engineering_intelligence.db.session import async_session_factory
    from engineering_intelligence.graph.client import GraphClient
    from engineering_intelligence.graph.repository import GraphRepository
    from engineering_intelligence.repositories.jira_repo import JiraRepository

    settings = get_settings()

    try:
        graph_client = GraphClient(settings.neo4j_uri, settings.neo4j_user, settings.neo4j_password)
        graph_repo = GraphRepository(graph_client)
    except Exception:
        return {"status": "skipped", "reason": "neo4j_unavailable"}

    edges_updated = 0

    try:
        async with async_session_factory() as db:
            jira_repo = JiraRepository(db)
            defect_stats = await jira_repo.count_defects_by_feature()

            for stat in defect_stats:
                epic_key = stat.get("epic_key")
                defect_count = stat.get("defect_count", 0)
                total_reopens = stat.get("total_reopens", 0) or 0
                if not epic_key:
                    continue

                # Update weight on LINKED_TO_FEATURE edges based on defect density
                weight = defect_count + (total_reopens * 2)
                query = """
                MATCH (d:Defect)-[r:LINKED_TO_FEATURE]->(f:Feature)
                WHERE d.key STARTS WITH $prefix
                SET r.weight = $weight
                RETURN count(r) AS updated
                """
                prefix = epic_key.split("-")[0] if "-" in epic_key else epic_key
                results = await graph_client.execute_write(
                    query, prefix=prefix, weight=float(weight)
                )
                if results:
                    edges_updated += results[0].get("updated", 0)

                activity.heartbeat(f"Updated weights for {epic_key}")
    finally:
        await graph_client.close()

    return {"status": "weights_updated", "edges_updated": edges_updated}


# ── RAG Activities ─────────────────────────────────────────────────────────────


@activity.defn
async def rebuild_vector_index(input: RAGRebuildInput) -> dict:
    """Full rebuild of the vector DB index from all Jira issues and PRs."""
    from engineering_intelligence.db.session import async_session_factory
    from engineering_intelligence.db.models import JiraIssue, PullRequest
    from engineering_intelligence.services.rag_service import RAGService
    from engineering_intelligence.vector.client import VectorStore
    from sqlalchemy import select

    settings = get_settings()
    collection = input.collection_name or settings.chroma_collection

    try:
        store = VectorStore(settings.chroma_host, settings.chroma_port, collection)
        rag_service = RAGService(store)
    except Exception:
        return {"status": "error", "reason": "chromadb_unavailable"}

    indexed = 0

    async with async_session_factory() as db:
        # Index all Jira issues
        result = await db.execute(select(JiraIssue))
        issues = result.scalars().all()
        for issue in issues:
            await rag_service.index_jira_issue(
                jira_key=issue.jira_key,
                summary=issue.summary,
                description=issue.description,
                metadata={
                    "issue_type": issue.issue_type.value,
                    "status": issue.status.value,
                    "epic_key": issue.epic_key or "",
                    "severity": issue.severity or "",
                },
            )
            indexed += 1
            if indexed % 100 == 0:
                activity.heartbeat(f"Indexed {indexed} Jira issues")

        # Index all PRs
        result = await db.execute(select(PullRequest))
        prs = result.scalars().all()
        for pr in prs:
            await rag_service.index_pr(
                pr_number=pr.pr_number,
                repo=pr.repo,
                title=pr.title,
                description=pr.description,
                metadata={
                    "status": pr.status.value if hasattr(pr.status, "value") else pr.status,
                    "author": pr.author_login or "",
                },
            )
            indexed += 1
            if indexed % 100 == 0:
                activity.heartbeat(f"Indexed {indexed} total documents")

    return {"status": "index_rebuilt", "documents_indexed": indexed}
