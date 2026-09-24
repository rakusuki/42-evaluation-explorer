from __future__ import annotations

import asyncio
from typing import Any

from app.forty_two import (
    FortyTwoAPIError,
    FortyTwoClient,
    forty_two_client,
)


class EvaluationService:
    def __init__(
        self,
        client: FortyTwoClient = forty_two_client,
    ) -> None:
        self.client = client

    async def user(self, login: str) -> dict[str, Any]:
        data = await self.client.get(f"/users/{login}")
        if not isinstance(data, dict):
            return {"raw": data}
        return data

    async def user_projects(
        self,
        login: str,
    ) -> list[dict[str, Any]]:
        data = await self.client.paginate(
            f"/users/{login}/projects_users",
            max_pages=5,
            page_size=100,
        )
        return [
            item for item in data
            if isinstance(item, dict)
        ]

    async def search_projects(
        self,
        query: str,
        limit: int = 30,
    ) -> list[dict[str, Any]]:
        data = await self.client.get(
            "/projects",
            params={
                "search[name]": query,
                "page[size]": min(limit, 100),
            },
        )
        if not isinstance(data, list):
            return []
        return [
            item for item in data
            if isinstance(item, dict)
        ]

    async def project(
        self,
        project_id_or_slug: str,
    ) -> dict[str, Any]:
        data = await self.client.get(
            f"/projects/{project_id_or_slug}"
        )
        if not isinstance(data, dict):
            return {"raw": data}
        return data

    async def teams_for_user(
        self,
        login: str,
        max_pages: int = 3,
    ) -> list[dict[str, Any]]:
        data = await self.client.paginate(
            f"/users/{login}/teams",
            max_pages=max_pages,
            page_size=100,
        )
        return [
            item for item in data
            if isinstance(item, dict)
        ]

    async def scale_teams_as_corrected(
        self,
        login: str,
        max_pages: int = 3,
    ) -> list[dict[str, Any]]:
        data = await self.client.paginate(
            f"/users/{login}/scale_teams/as_corrected",
            max_pages=max_pages,
            page_size=100,
        )
        return [
            item for item in data
            if isinstance(item, dict)
        ]

    async def scale_teams_as_corrector(
        self,
        login: str,
        max_pages: int = 3,
    ) -> list[dict[str, Any]]:
        data = await self.client.paginate(
            f"/users/{login}/scale_teams/as_corrector",
            max_pages=max_pages,
            page_size=100,
        )
        return [
            item for item in data
            if isinstance(item, dict)
        ]

    async def scale_team(
        self,
        scale_team_id: int,
    ) -> dict[str, Any]:
        data = await self.client.get(
            f"/scale_teams/{scale_team_id}"
        )
        if not isinstance(data, dict):
            return {"raw": data}
        return data

    async def scale_team_feedbacks(
        self,
        scale_team_id: int,
    ) -> list[dict[str, Any]]:
        data = await self.client.paginate(
            f"/scale_teams/{scale_team_id}/feedbacks",
            max_pages=3,
            page_size=100,
        )
        return [
            item for item in data
            if isinstance(item, dict)
        ]

    async def team_uploads(
        self,
        team_id: int,
    ) -> list[dict[str, Any]]:
        data = await self.client.paginate(
            f"/teams/{team_id}/teams_uploads",
            max_pages=3,
            page_size=100,
        )
        return [
            item for item in data
            if isinstance(item, dict)
        ]

    async def project_scales(
        self,
        project_id_or_slug: str,
    ) -> list[dict[str, Any]]:
        data = await self.client.paginate(
            f"/projects/{project_id_or_slug}/scales",
            max_pages=3,
            page_size=100,
        )
        return [
            item for item in data
            if isinstance(item, dict)
        ]

    async def aggregate_reviews(
        self,
        login: str,
        project_id: int | None = None,
        *,
        max_pages: int = 5,
        max_reviews: int = 50,
        feedback_concurrency: int = 4,
    ) -> list[dict[str, Any]]:
        rows = await self.scale_teams_as_corrected(
            login,
            max_pages=max_pages,
        )

        if project_id is not None:
            rows = [
                row
                for row in rows
                if self._project_id_from_scale_team(row)
                == project_id
            ]

        rows = rows[:max_reviews]
        semaphore = asyncio.Semaphore(
            max(1, feedback_concurrency)
        )

        async def enrich(
            row: dict[str, Any],
        ) -> dict[str, Any]:
            scale_team_id = row.get("id")
            feedbacks: list[dict[str, Any]] = []
            feedback_error: dict[str, Any] | None = None

            if isinstance(scale_team_id, int):
                try:
                    async with semaphore:
                        feedbacks = (
                            await self.scale_team_feedbacks(
                                scale_team_id
                            )
                        )
                except FortyTwoAPIError as exc:
                    feedback_error = {
                        "status_code": exc.status_code,
                        "message": exc.message,
                    }

            return self.compact_review(
                row,
                feedbacks,
                feedback_error=feedback_error,
            )

        if not rows:
            return []

        return list(
            await asyncio.gather(
                *(enrich(row) for row in rows)
            )
        )

    @staticmethod
    def compact_project_user(
        item: dict[str, Any],
    ) -> dict[str, Any]:
        project = item.get("project") or {}
        return {
            "id": item.get("id"),
            "project_id": project.get("id"),
            "project_name": project.get("name"),
            "status": item.get("status"),
            "final_mark": item.get("final_mark"),
            "validated": item.get(
                "validated?",
                item.get("validated"),
            ),
            "marked_at": item.get("marked_at"),
            "updated_at": item.get("updated_at"),
        }

    @staticmethod
    def compact_feedback(
        item: dict[str, Any],
    ) -> dict[str, Any]:
        user = (
            item.get("user")
            or item.get("feedbacker")
            or item.get("author")
            or {}
        )
        if not isinstance(user, dict):
            user = {}

        return {
            "id": item.get("id"),
            "comment": item.get("comment"),
            "rating": item.get("rating"),
            "user_login": user.get("login"),
            "created_at": item.get("created_at"),
            "updated_at": item.get("updated_at"),
        }

    @classmethod
    def compact_review(
        cls,
        row: dict[str, Any],
        feedbacks: list[dict[str, Any]],
        *,
        feedback_error: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        corrector = row.get("corrector") or {}
        if not isinstance(corrector, dict):
            corrector = {}

        team = row.get("team") or {}
        if not isinstance(team, dict):
            team = {}

        compact_feedbacks = [
            cls.compact_feedback(item)
            for item in feedbacks
        ]

        comments: list[dict[str, Any]] = []
        seen_comments: set[str] = set()

        scale_comment = row.get("comment")
        if isinstance(scale_comment, str):
            text = scale_comment.strip()
            if text:
                comments.append(
                    {
                        "source": "scale_team",
                        "comment": text,
                        "user_login": (
                            corrector.get("login")
                        ),
                    }
                )
                seen_comments.add(text)

        for feedback in compact_feedbacks:
            comment = feedback.get("comment")
            if not isinstance(comment, str):
                continue
            text = comment.strip()
            if not text or text in seen_comments:
                continue
            comments.append(
                {
                    "source": "feedback",
                    "comment": text,
                    "user_login": (
                        feedback.get("user_login")
                    ),
                    "rating": feedback.get("rating"),
                }
            )
            seen_comments.add(text)

        return {
            "id": row.get("id"),
            "team_id": row.get(
                "team_id",
                team.get("id"),
            ),
            "project_id": team.get("project_id"),
            "begin_at": row.get("begin_at"),
            "filled_at": row.get("filled_at"),
            "final_mark": row.get("final_mark"),
            "corrector": corrector.get("login"),
            "flag": row.get("flag"),
            "scale_comment": row.get("comment"),
            "feedbacks": compact_feedbacks,
            "comments": comments,
            "feedback_error": feedback_error,
        }

    @staticmethod
    def _project_id_from_scale_team(
        row: dict[str, Any],
    ) -> Any:
        team = row.get("team") or {}
        if not isinstance(team, dict):
            return None
        return team.get("project_id")


evaluation_service = EvaluationService()
