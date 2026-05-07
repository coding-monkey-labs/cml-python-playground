"""Temporal workflow dispatch — connects to Temporal server and starts workflows."""

import json

from temporalio.client import Client

from engineering_intelligence.config import get_settings

# Workflow type -> Temporal workflow class name mapping
_WORKFLOW_MAP = {
    "jira_ingestion": "JiraIngestionWorkflow",
    "jira_incremental": "IncrementalJiraUpdateWorkflow",
    "pr_ingestion": "PRIngestionWorkflow",
    "feature_graph_build": "FeatureGraphBuildWorkflow",
    "hotspot_computation": "HotspotComputationWorkflow",
    "rag_rebuild": "RAGRebuildWorkflow",
}


async def get_temporal_client() -> Client:
    """Create a connection to the Temporal server."""
    settings = get_settings()
    return await Client.connect(
        settings.temporal_host,
        namespace=settings.temporal_namespace,
    )


async def dispatch_workflow(
    workflow_type: str,
    workflow_id: str,
    params: dict | None = None,
) -> str:
    """Dispatch a workflow to Temporal and return the run ID.

    Args:
        workflow_type: One of the keys in _WORKFLOW_MAP.
        workflow_id: Unique workflow ID for idempotency.
        params: Parameters to pass to the workflow.

    Returns:
        The Temporal workflow run ID.
    """
    settings = get_settings()
    client = await get_temporal_client()

    # Build workflow args from params
    args = _build_workflow_args(workflow_type, params or {})

    handle = await client.start_workflow(
        _WORKFLOW_MAP[workflow_type],
        arg=args,
        id=workflow_id,
        task_queue=settings.temporal_task_queue,
    )

    return handle.result_run_id


async def get_workflow_result(workflow_id: str) -> dict:
    """Get the result of a completed workflow."""
    client = await get_temporal_client()
    handle = client.get_workflow_handle(workflow_id)
    return await handle.result()


async def cancel_workflow(workflow_id: str) -> None:
    """Cancel a running workflow."""
    client = await get_temporal_client()
    handle = client.get_workflow_handle(workflow_id)
    await handle.cancel()


def get_supported_workflows() -> list[str]:
    """Return the list of supported workflow types."""
    return list(_WORKFLOW_MAP.keys())


def _build_workflow_args(workflow_type: str, params: dict) -> object:
    """Convert raw params dict to the appropriate workflow input."""
    if workflow_type == "jira_ingestion":
        return params.get("epic_keys", [])
    elif workflow_type == "jira_incremental":
        return params.get("epic_keys", [])
    elif workflow_type == "pr_ingestion":
        return params.get("repo", "")
    elif workflow_type == "feature_graph_build":
        return params.get("codebase_path", ".")
    elif workflow_type == "hotspot_computation":
        return params.get("feature_names")
    elif workflow_type == "rag_rebuild":
        return params.get("collection_name")
    else:
        raise ValueError(f"Unknown workflow type: {workflow_type}")
