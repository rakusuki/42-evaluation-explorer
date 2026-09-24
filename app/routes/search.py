from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Query

from app.forty_two import FortyTwoAPIError
from app.services.evaluation import evaluation_service


router = APIRouter(prefix="/api", tags=["search"])


def error_payload(exc: FortyTwoAPIError) -> dict[str, Any]:
    return {
        "ok": False,
        "status_code": exc.status_code,
        "message": exc.message,
        "detail": exc.body,
    }


@router.get("/projects/search")
async def search_projects(q: str = Query(..., min_length=1), limit: int = Query(30, ge=1, le=100)) -> dict[str, Any]:
    try:
        projects = await evaluation_service.search_projects(q, limit=limit)
        return {
            "ok": True,
            "items": [
                {
                    "id": project.get("id"),
                    "name": project.get("name"),
                    "slug": project.get("slug"),
                }
                for project in projects
            ],
        }
    except FortyTwoAPIError as exc:
        return error_payload(exc)


@router.get("/users/{login}/project-progress")
async def user_project_progress(
    login: str,
    project: str | None = None,
    status: str | None = Query(None, pattern="^(finished|in_progress|waiting_for_correction|searching_a_group|creating_group|parent|any)$"),
) -> dict[str, Any]:
    try:
        rows = await evaluation_service.user_projects(login)
    except FortyTwoAPIError as exc:
        return error_payload(exc)

    compact = [evaluation_service.compact_project_user(item) for item in rows]

    if project:
        needle = project.casefold()
        compact = [
            item
            for item in compact
            if str(item.get("project_id")) == project
            or needle in str(item.get("project_name") or "").casefold()
        ]

    if status and status != "any":
        compact = [item for item in compact if item.get("status") == status]

    return {"ok": True, "login": login, "items": compact}


@router.get("/reviews/{login}")
async def review_candidates(login: str, project_id: int | None = None) -> dict[str, Any]:
    """Return review-like records visible to the application's token.

    This endpoint deliberately uses the user's scale-team history instead of
    assuming that every 42 application can enumerate all evaluations globally.
    The capability-probe endpoints expose 403/404 results separately.
    """
    try:
        rows = await evaluation_service.scale_teams_as_corrected(login, max_pages=5)
    except FortyTwoAPIError as exc:
        return error_payload(exc)

    if project_id is not None:
        filtered: list[dict[str, Any]] = []
        for item in rows:
            team = item.get("team") or {}
            if team.get("project_id") == project_id:
                filtered.append(item)
        rows = filtered

    items: list[dict[str, Any]] = []
    for row in rows:
        corrector = row.get("corrector") or {}
        team = row.get("team") or {}
        items.append(
            {
                "id": row.get("id"),
                "team_id": row.get("team_id", team.get("id")),
                "project_id": team.get("project_id"),
                "begin_at": row.get("begin_at"),
                "filled_at": row.get("filled_at"),
                "final_mark": row.get("final_mark"),
                "comment": row.get("comment"),
                "corrector": corrector.get("login"),
                "flag": row.get("flag"),
                "raw": row,
            }
        )

    return {"ok": True, "login": login, "items": items}
