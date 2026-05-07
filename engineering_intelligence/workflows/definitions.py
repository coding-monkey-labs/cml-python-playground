"""Temporal workflow definitions — orchestrate multi-step async processing."""

from datetime import timedelta

from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    from engineering_intelligence.workflows.activities import (
        JiraIngestionInput,
        PRIngestionInput,
        HotspotComputeInput,
        RAGRebuildInput,
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
    )


@workflow.defn
class JiraIngestionWorkflow:
    """Fetch Jira issues for given epics, update graph, generate embeddings."""

    @workflow.run
    async def run(self, epic_keys: list[str]) -> dict:
        input_data = JiraIngestionInput(epic_keys=epic_keys)

        # Step 1: Fetch from Jira API
        fetch_result = await workflow.execute_activity(
            fetch_jira_issues,
            input_data,
            start_to_close_timeout=timedelta(minutes=10),
            retry_policy=workflow.RetryPolicy(
                maximum_attempts=3,
                initial_interval=timedelta(seconds=5),
                backoff_coefficient=2.0,
            ),
        )

        # Step 2: Update graph
        await workflow.execute_activity(
            update_jira_graph,
            input_data,
            start_to_close_timeout=timedelta(minutes=5),
        )

        # Step 3: Generate embeddings
        await workflow.execute_activity(
            generate_jira_embeddings,
            input_data,
            start_to_close_timeout=timedelta(minutes=10),
        )

        return {"status": "completed", "fetch": fetch_result}


@workflow.defn
class IncrementalJiraUpdateWorkflow:
    """Triggered daily/webhook — fetch newly created/updated issues."""

    @workflow.run
    async def run(self, epic_keys: list[str]) -> dict:
        input_data = JiraIngestionInput(epic_keys=epic_keys)

        await workflow.execute_activity(
            fetch_jira_issues,
            input_data,
            start_to_close_timeout=timedelta(minutes=10),
        )
        await workflow.execute_activity(
            update_jira_graph,
            input_data,
            start_to_close_timeout=timedelta(minutes=5),
        )
        await workflow.execute_activity(
            generate_jira_embeddings,
            input_data,
            start_to_close_timeout=timedelta(minutes=10),
        )

        return {"status": "incremental_update_completed"}


@workflow.defn
class PRIngestionWorkflow:
    """Fetch PR metadata, extract/infer Jira mappings, update graph."""

    @workflow.run
    async def run(self, repo: str, pr_numbers: list[int] | None = None) -> dict:
        input_data = PRIngestionInput(repo=repo, pr_numbers=pr_numbers)

        await workflow.execute_activity(
            fetch_pr_metadata,
            input_data,
            start_to_close_timeout=timedelta(minutes=10),
        )
        await workflow.execute_activity(
            extract_pr_jira_mappings,
            input_data,
            start_to_close_timeout=timedelta(minutes=5),
        )
        await workflow.execute_activity(
            infer_pr_jira_mappings,
            input_data,
            start_to_close_timeout=timedelta(minutes=10),
        )

        return {"status": "pr_ingestion_completed", "repo": repo}


@workflow.defn
class FeatureGraphBuildWorkflow:
    """Parse React codebase, build feature hierarchy, persist graph."""

    @workflow.run
    async def run(self, codebase_path: str) -> dict:
        parsed = await workflow.execute_activity(
            parse_react_codebase,
            codebase_path,
            start_to_close_timeout=timedelta(minutes=15),
        )

        await workflow.execute_activity(
            build_feature_hierarchy,
            parsed,
            start_to_close_timeout=timedelta(minutes=10),
        )

        return {"status": "feature_graph_built"}


@workflow.defn
class HotspotComputationWorkflow:
    """Compute defect hotspots, reopen patterns, update graph weights."""

    @workflow.run
    async def run(self, feature_names: list[str] | None = None) -> dict:
        input_data = HotspotComputeInput(feature_names=feature_names)

        await workflow.execute_activity(
            compute_hotspots,
            input_data,
            start_to_close_timeout=timedelta(minutes=10),
        )
        await workflow.execute_activity(
            detect_reopen_patterns,
            input_data,
            start_to_close_timeout=timedelta(minutes=10),
        )
        await workflow.execute_activity(
            update_graph_weights,
            input_data,
            start_to_close_timeout=timedelta(minutes=5),
        )

        return {"status": "hotspot_computation_completed"}


@workflow.defn
class RAGRebuildWorkflow:
    """Full rebuild of the RAG vector index."""

    @workflow.run
    async def run(self, collection_name: str | None = None) -> dict:
        input_data = RAGRebuildInput(collection_name=collection_name)

        await workflow.execute_activity(
            rebuild_vector_index,
            input_data,
            start_to_close_timeout=timedelta(minutes=30),
        )

        return {"status": "rag_rebuild_completed"}
