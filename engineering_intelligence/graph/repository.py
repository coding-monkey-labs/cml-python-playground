"""Graph repository for Neo4j CRUD operations on the knowledge graph."""

from engineering_intelligence.graph.client import GraphClient


class GraphRepository:
    """High-level operations on the engineering knowledge graph."""

    def __init__(self, client: GraphClient) -> None:
        self._client = client

    # ── Feature Graph ──────────────────────────────────────────────────────

    async def upsert_feature(self, name: str, description: str | None = None,
                             file_path: str | None = None) -> dict:
        query = """
        MERGE (f:Feature {name: $name})
        SET f.description = $description, f.file_path = $file_path
        RETURN f
        """
        rows = await self._client.execute_write(
            query, name=name, description=description, file_path=file_path
        )
        return rows[0] if rows else {}

    async def add_subfeature(self, parent_name: str, child_name: str) -> dict:
        query = """
        MATCH (p:Feature {name: $parent_name})
        MERGE (c:Feature {name: $child_name})
        MERGE (p)-[:HAS_SUBFEATURE]->(c)
        RETURN p, c
        """
        rows = await self._client.execute_write(
            query, parent_name=parent_name, child_name=child_name
        )
        return rows[0] if rows else {}

    async def get_feature_tree(self, root_name: str | None = None) -> list[dict]:
        if root_name:
            query = """
            MATCH path = (root:Feature {name: $root_name})-[:HAS_SUBFEATURE*0..]->(child)
            RETURN nodes(path) AS nodes, relationships(path) AS rels
            """
            return await self._client.execute_read(query, root_name=root_name)
        query = """
        MATCH (f:Feature)
        OPTIONAL MATCH (f)-[:HAS_SUBFEATURE]->(child:Feature)
        RETURN f.name AS feature, collect(child.name) AS children
        """
        return await self._client.execute_read(query)

    # ── Jira Graph ─────────────────────────────────────────────────────────

    async def upsert_jira_node(self, key: str, issue_type: str, summary: str,
                               status: str, severity: str | None = None) -> dict:
        label = issue_type.capitalize()
        query = f"""
        MERGE (n:{label} {{key: $key}})
        SET n.summary = $summary, n.status = $status, n.severity = $severity
        RETURN n
        """
        rows = await self._client.execute_write(
            query, key=key, summary=summary, status=status, severity=severity
        )
        return rows[0] if rows else {}

    async def link_epic_child(self, epic_key: str, child_key: str,
                              child_type: str) -> dict:
        child_label = child_type.capitalize()
        query = f"""
        MATCH (e:Epic {{key: $epic_key}})
        MATCH (c:{child_label} {{key: $child_key}})
        MERGE (e)-[:CONTAINS]->(c)
        RETURN e, c
        """
        rows = await self._client.execute_write(
            query, epic_key=epic_key, child_key=child_key
        )
        return rows[0] if rows else {}

    async def link_story_child(self, story_key: str, child_key: str,
                               child_type: str) -> dict:
        child_label = child_type.capitalize()
        query = f"""
        MATCH (s:Story {{key: $story_key}})
        MATCH (c:{child_label} {{key: $child_key}})
        MERGE (s)-[:CONTAINS]->(c)
        RETURN s, c
        """
        rows = await self._client.execute_write(
            query, story_key=story_key, child_key=child_key
        )
        return rows[0] if rows else {}

    async def link_defect_to_feature(self, defect_key: str, feature_name: str,
                                     weight: float = 1.0) -> dict:
        query = """
        MATCH (d:Defect {key: $defect_key})
        MATCH (f:Feature {name: $feature_name})
        MERGE (d)-[r:LINKED_TO_FEATURE]->(f)
        SET r.weight = $weight
        RETURN d, f
        """
        rows = await self._client.execute_write(
            query, defect_key=defect_key, feature_name=feature_name, weight=weight
        )
        return rows[0] if rows else {}

    async def link_pr_fixes_jira(self, pr_number: int, jira_key: str) -> dict:
        query = """
        MERGE (p:PullRequest {number: $pr_number})
        WITH p
        MATCH (j {key: $jira_key})
        MERGE (p)-[:FIXES]->(j)
        RETURN p, j
        """
        rows = await self._client.execute_write(
            query, pr_number=pr_number, jira_key=jira_key
        )
        return rows[0] if rows else {}

    async def link_developer(self, email: str, jira_key: str) -> dict:
        query = """
        MERGE (d:Developer {email: $email})
        WITH d
        MATCH (j {key: $jira_key})
        MERGE (d)-[:WORKED_ON]->(j)
        RETURN d, j
        """
        rows = await self._client.execute_write(query, email=email, jira_key=jira_key)
        return rows[0] if rows else {}

    async def mark_defect_reopened(self, defect_key: str, from_key: str) -> dict:
        query = """
        MATCH (d:Defect {key: $defect_key})
        MATCH (prev {key: $from_key})
        MERGE (d)-[:REOPENED_FROM]->(prev)
        RETURN d, prev
        """
        rows = await self._client.execute_write(
            query, defect_key=defect_key, from_key=from_key
        )
        return rows[0] if rows else {}

    async def link_component(self, jira_key: str, component_name: str) -> dict:
        query = """
        MERGE (c:Component {name: $component_name})
        WITH c
        MATCH (j {key: $jira_key})
        MERGE (j)-[:AFFECTS_COMPONENT]->(c)
        RETURN j, c
        """
        rows = await self._client.execute_write(
            query, jira_key=jira_key, component_name=component_name
        )
        return rows[0] if rows else {}

    # ── Analytics Queries ──────────────────────────────────────────────────

    async def get_hotspot_features(self, limit: int = 10) -> list[dict]:
        query = """
        MATCH (d:Defect)-[r:LINKED_TO_FEATURE]->(f:Feature)
        RETURN f.name AS feature, count(d) AS defect_count,
               sum(r.weight) AS total_weight
        ORDER BY total_weight DESC
        LIMIT $limit
        """
        return await self._client.execute_read(query, limit=limit)

    async def get_reopen_patterns(self, limit: int = 10) -> list[dict]:
        query = """
        MATCH (d:Defect)-[:REOPENED_FROM]->(prev)
        RETURN d.key AS defect, prev.key AS reopened_from,
               d.summary AS summary
        LIMIT $limit
        """
        return await self._client.execute_read(query, limit=limit)

    async def get_jira_subtree(self, root_key: str) -> list[dict]:
        query = """
        MATCH path = ({key: $root_key})-[:CONTAINS*0..]->(child)
        RETURN nodes(path) AS nodes
        """
        return await self._client.execute_read(query, root_key=root_key)

    async def get_developer_metrics(self, email: str) -> list[dict]:
        query = """
        MATCH (dev:Developer {email: $email})-[:WORKED_ON]->(j)
        RETURN labels(j)[0] AS type, count(j) AS count,
               collect(j.key) AS keys
        """
        return await self._client.execute_read(query, email=email)

    async def get_feature_risk_score(self, feature_name: str) -> list[dict]:
        query = """
        MATCH (f:Feature {name: $feature_name})
        OPTIONAL MATCH (d:Defect)-[r:LINKED_TO_FEATURE]->(f)
        OPTIONAL MATCH (d)-[:REOPENED_FROM]->(prev)
        RETURN f.name AS feature,
               count(DISTINCT d) AS defect_count,
               count(DISTINCT prev) AS reopen_count,
               sum(r.weight) AS risk_weight
        """
        return await self._client.execute_read(query, feature_name=feature_name)
