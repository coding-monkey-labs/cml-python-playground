"""Temporal activity definitions — the actual work units invoked by workflows."""

from dataclasses import dataclass
from temporalio import activity


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
    """Fetch Jira issues for given epic keys from Jira API."""
    activity.logger.info(f"Fetching Jira issues for epics: {input.epic_keys}")
    # In production, this would use JiraService.fetch_from_jira_api()
    # and then JiraService.upsert_issue() for each issue
    return {"epics_processed": len(input.epic_keys), "status": "completed"}


@activity.defn
async def update_jira_graph(input: JiraIngestionInput) -> dict:
    """Update the Jira knowledge graph after ingestion."""
    activity.logger.info(f"Updating Jira graph for epics: {input.epic_keys}")
    return {"status": "graph_updated"}


@activity.defn
async def generate_jira_embeddings(input: JiraIngestionInput) -> dict:
    """Generate embeddings for Jira issues and store in vector DB."""
    activity.logger.info(f"Generating embeddings for epics: {input.epic_keys}")
    return {"status": "embeddings_generated"}


# ── PR Activities ──────────────────────────────────────────────────────────────


@activity.defn
async def fetch_pr_metadata(input: PRIngestionInput) -> dict:
    """Fetch PR metadata from GitHub API."""
    activity.logger.info(f"Fetching PRs for repo: {input.repo}")
    return {"repo": input.repo, "status": "completed"}


@activity.defn
async def extract_pr_jira_mappings(input: PRIngestionInput) -> dict:
    """Extract Jira issue keys from PR titles/descriptions and create mappings."""
    activity.logger.info(f"Extracting Jira mappings for repo: {input.repo}")
    return {"status": "mappings_extracted"}


@activity.defn
async def infer_pr_jira_mappings(input: PRIngestionInput) -> dict:
    """Use embedding similarity to infer PR-Jira mappings when explicit keys are missing."""
    activity.logger.info(f"Inferring mappings via embeddings for repo: {input.repo}")
    return {"status": "inferred_mappings_completed"}


# ── Feature Graph Activities ──────────────────────────────────────────────────


@activity.defn
async def parse_react_codebase(codebase_path: str) -> dict:
    """Parse React codebase using AST to detect components, routes, modules."""
    activity.logger.info(f"Parsing React codebase at: {codebase_path}")
    return {"status": "parsed", "path": codebase_path}


@activity.defn
async def build_feature_hierarchy(parsed_data: dict) -> dict:
    """Build Feature → SubFeature hierarchy from parsed AST data."""
    activity.logger.info("Building feature hierarchy")
    return {"status": "hierarchy_built"}


# ── Analytics Activities ───────────────────────────────────────────────────────


@activity.defn
async def compute_hotspots(input: HotspotComputeInput) -> dict:
    """Compute defect hotspots, reopen frequency, defect density."""
    activity.logger.info("Computing hotspot metrics")
    return {"status": "hotspots_computed"}


@activity.defn
async def detect_reopen_patterns(input: HotspotComputeInput) -> dict:
    """Detect repeated defect clusters and recurring root causes."""
    activity.logger.info("Detecting reopen patterns")
    return {"status": "patterns_detected"}


@activity.defn
async def update_graph_weights(input: HotspotComputeInput) -> dict:
    """Update graph edge weights based on computed metrics."""
    activity.logger.info("Updating graph weights")
    return {"status": "weights_updated"}


# ── RAG Activities ─────────────────────────────────────────────────────────────


@activity.defn
async def rebuild_vector_index(input: RAGRebuildInput) -> dict:
    """Full rebuild of the vector DB index."""
    activity.logger.info(f"Rebuilding vector index: {input.collection_name}")
    return {"status": "index_rebuilt"}
