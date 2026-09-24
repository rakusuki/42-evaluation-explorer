from __future__ import annotations

from typing import Any

from app.forty_two import FortyTwoClient, forty_two_client


class EvaluationService:
    def __init__(self, client: FortyTwoClient = forty_two_client) -> None:
        self.client = client

    async def user(self, login: str) -> dict[str, Any]:
        data = await self.client.get(f"/users/{login}")
        if not isinstance(data, dict):
            return {"raw": data}
        return data

    async def user_projects(self, login: str) -> list[dict[str, Any]]:
        data = await self.client.paginate(
            f"/users/{login}/projects_users",
            max_pages=5,
            page_size=100,
        )
        return [item for item in data if isinstance(item, dict)]

    async def search_projects(self, query: str, limit: int = 30) -> list[dict[str, Any]]:
        # 42 API supports search on many index resources. If the API rejects the
        # search parameter for projects, the caller receives the real 4xx result.
        data = await self.client.get(
            "/projects",
            params={"search[name]": query, "page[size]": min(limit, 100)},
        )
        if not isinstance(data, list):
            return []
        return [item for item in data if isinstance(item, dict)]

    async def project(self, project_id_or_slug: str) -> dict[str, Any]:
        data = await self.client.get(f"/projects/{project_id_or_slug}")
        if not isinstance(data, dict):
            return {"raw": data}
        return data

    async def teams_for_user(self, login: str, max_pages: int = 3) -> list[dict[str, Any]]:
        data = await self.client.paginate(
            f"/users/{login}/teams",
            max_pages=max_pages,
            page_size=100,
        )
        return [item for item in data if isinstance(item, dict)]

    async def scale_teams_as_corrected(self, login: str, max_pages: int = 3) -> list[dict[str, Any]]:
        data = await self.client.paginate(
            f"/users/{login}/scale_teams/as_corrected",
            max_pages=max_pages,
            page_size=100,
        )
        return [item for item in data if isinstance(item, dict)]

    async def scale_teams_as_corrector(self, login: str, max_pages: int = 3) -> list[dict[str, Any]]:
        data = await self.client.paginate(
            f"/users/{login}/scale_teams/as_corrector",
            max_pages=max_pages,
            page_size=100,
        )
        return [item for item in data if isinstance(item, dict)]

    async def scale_team(self, scale_team_id: int) -> dict[str, Any]:
        data = await self.client.get(f"/scale_teams/{scale_team_id}")
        if not isinstance(data, dict):
            return {"raw": data}
        return data

    async def scale_team_feedbacks(self, scale_team_id: int) -> list[dict[str, Any]]:
        data = await self.client.paginate(
            f"/scale_teams/{scale_team_id}/feedbacks",
            max_pages=3,
            page_size=100,
        )
        return [item for item in data if isinstance(item, dict)]

    async def team_uploads(self, team_id: int) -> list[dict[str, Any]]:
        data = await self.client.paginate(
            f"/teams/{team_id}/teams_uploads",
            max_pages=3,
            page_size=100,
        )
        return [item for item in data if isinstance(item, dict)]

    async def project_scales(self, project_id_or_slug: str) -> list[dict[str, Any]]:
        data = await self.client.paginate(
            f"/projects/{project_id_or_slug}/scales",
            max_pages=3,
            page_size=100,
        )
        return [item for item in data if isinstance(item, dict)]

    @staticmethod
    def compact_project_user(item: dict[str, Any]) -> dict[str, Any]:
        project = item.get("project") or {}
        return {
            "id": item.get("id"),
            "project_id": project.get("id"),
            "project_name": project.get("name"),
            "status": item.get("status"),
            "final_mark": item.get("final_mark"),
            "validated": item.get("validated?", item.get("validated")),
            "marked_at": item.get("marked_at"),
            "updated_at": item.get("updated_at"),
        }


evaluation_service = EvaluationService()
