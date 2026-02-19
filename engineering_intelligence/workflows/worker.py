"""Temporal worker — registers workflows and activities, connects to Temporal server."""

import asyncio

from temporalio.client import Client
from temporalio.worker import Worker

from engineering_intelligence.config import get_settings
from engineering_intelligence.workflows.activities import (
    build_feature_hierarchy,
    compute_hotspots,
    detect_reopen_patterns,
    extract_pr_jira_mappings,
    fetch_jira_issues,
    fetch_pr_metadata,
    generate_jira_embeddings,
    infer_pr_jira_mappings,
    parse_react_codebase,
    rebuild_vector_index,
    update_graph_weights,
    update_jira_graph,
)
from engineering_intelligence.workflows.definitions import (
    FeatureGraphBuildWorkflow,
    HotspotComputationWorkflow,
    IncrementalJiraUpdateWorkflow,
    JiraIngestionWorkflow,
    PRIngestionWorkflow,
    RAGRebuildWorkflow,
)


async def run_worker() -> None:
    settings = get_settings()

    client = await Client.connect(
        settings.temporal_host,
        namespace=settings.temporal_namespace,
    )

    worker = Worker(
        client,
        task_queue=settings.temporal_task_queue,
        workflows=[
            JiraIngestionWorkflow,
            IncrementalJiraUpdateWorkflow,
            PRIngestionWorkflow,
            FeatureGraphBuildWorkflow,
            HotspotComputationWorkflow,
            RAGRebuildWorkflow,
        ],
        activities=[
            fetch_jira_issues,
            update_jira_graph,
            generate_jira_embeddings,
            fetch_pr_metadata,
            extract_pr_jira_mappings,
            infer_pr_jira_mappings,
            parse_react_codebase,
            build_feature_hierarchy,
            compute_hotspots,
            detect_reopen_patterns,
            update_graph_weights,
            rebuild_vector_index,
        ],
    )

    print(f"Starting Temporal worker on queue: {settings.temporal_task_queue}")
    await worker.run()


if __name__ == "__main__":
    asyncio.run(run_worker())
