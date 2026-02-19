"""GitHub service — fetch PR metadata, files changed, and map to Jira issues."""

import httpx

from engineering_intelligence.config import get_settings
from engineering_intelligence.schemas.pull_requests import PRCreate
from engineering_intelligence.services.jira_service import JiraService


class GitHubService:
    """Fetches PR data from the GitHub REST API."""

    def __init__(self) -> None:
        self._settings = get_settings()
        self._base_url = "https://api.github.com"

    def _headers(self) -> dict[str, str]:
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self._settings.github_token:
            headers["Authorization"] = f"Bearer {self._settings.github_token}"
        return headers

    async def fetch_pr(self, owner: str, repo: str, pr_number: int) -> PRCreate | None:
        """Fetch a single PR from GitHub API and return as PRCreate."""
        url = f"{self._base_url}/repos/{owner}/{repo}/pulls/{pr_number}"
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, headers=self._headers(), timeout=30.0)
            if resp.status_code != 200:
                return None
            data = resp.json()
            return self._parse_pr(data, f"{owner}/{repo}")

    async def fetch_prs(
        self,
        owner: str,
        repo: str,
        state: str = "all",
        per_page: int = 100,
        page: int = 1,
    ) -> list[PRCreate]:
        """Fetch a page of PRs from GitHub API."""
        url = f"{self._base_url}/repos/{owner}/{repo}/pulls"
        params = {"state": state, "per_page": per_page, "page": page, "sort": "updated", "direction": "desc"}
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                url, headers=self._headers(), params=params, timeout=30.0
            )
            if resp.status_code != 200:
                return []
            items = resp.json()
            return [self._parse_pr(item, f"{owner}/{repo}") for item in items]

    async def fetch_pr_files(self, owner: str, repo: str, pr_number: int) -> list[dict]:
        """Fetch the list of files changed in a PR."""
        url = f"{self._base_url}/repos/{owner}/{repo}/pulls/{pr_number}/files"
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, headers=self._headers(), timeout=30.0)
            if resp.status_code != 200:
                return []
            return [
                {
                    "filename": f["filename"],
                    "status": f["status"],
                    "additions": f["additions"],
                    "deletions": f["deletions"],
                    "patch": f.get("patch", ""),
                }
                for f in resp.json()
            ]

    async def fetch_pr_with_details(
        self, owner: str, repo: str, pr_number: int
    ) -> PRCreate | None:
        """Fetch PR metadata with accurate file change counts."""
        pr = await self.fetch_pr(owner, repo, pr_number)
        if not pr:
            return None
        files = await self.fetch_pr_files(owner, repo, pr_number)
        pr.files_changed = len(files)
        pr.additions = sum(f["additions"] for f in files)
        pr.deletions = sum(f["deletions"] for f in files)
        return pr

    def extract_jira_keys_from_pr(self, pr: PRCreate) -> list[str]:
        """Extract Jira keys from PR title and description."""
        text = f"{pr.title} {pr.description or ''}"
        return JiraService.extract_jira_keys(text)

    @staticmethod
    def _parse_pr(data: dict, repo_full_name: str) -> PRCreate:
        user = data.get("user", {})
        return PRCreate(
            pr_number=data["number"],
            repo=repo_full_name,
            title=data.get("title", ""),
            description=data.get("body"),
            status=_map_pr_state(data.get("state", "open"), data.get("merged_at")),
            author_email=user.get("email"),
            author_login=user.get("login"),
            files_changed=data.get("changed_files", 0),
            additions=data.get("additions", 0),
            deletions=data.get("deletions", 0),
        )


def _map_pr_state(state: str, merged_at: str | None) -> str:
    if merged_at:
        return "merged"
    return "open" if state == "open" else "closed"
