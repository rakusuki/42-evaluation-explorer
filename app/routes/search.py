from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Query

from app.forty_two import FortyTwoAPIError
from app.services.evaluation import evaluation_service


router = APIRouter(prefix="/api", tags=["search"])


def error_payload(
    exc: FortyTwoAPIError,
) -> dict[str, Any]:
    return {
        "ok": False,
        "status_code": exc.status_code,
        "message": exc.message,
        "detail": exc.body,
    }


@router.get("/projects/search")
async def search_projects(
    q: str = Query(..., min_length=1),
    limit: int = Query(30, ge=1, le=100),
) -> dict[str, Any]:
    try:
        projects = await evaluation_service.search_projects(
            q,
            limit=limit,
        )
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
    status: str | None = Query(
        None,
        pattern=(
            "^(finished|in_progress|"
            "waiting_for_correction|searching_a_group|"
            "creating_group|parent|any)$"
        ),
    ),
) -> dict[str, Any]:
    try:
        rows = await evaluation_service.user_projects(login)
    except FortyTwoAPIError as exc:
        return error_payload(exc)

    compact = [
        evaluation_service.compact_project_user(item)
        for item in rows
    ]

    if project:
        needle = project.casefold()
        compact = [
            item
            for item in compact
            if str(item.get("project_id")) == project
            or needle
            in str(
                item.get("project_name") or ""
            ).casefold()
        ]

    if status and status != "any":
        compact = [
            item
            for item in compact
            if item.get("status") == status
        ]

    return {
        "ok": True,
        "login": login,
        "items": compact,
    }


@router.get("/reviews/{login}")
async def review_candidates(
    login: str,
    project: str | None = None,
    project_id: int | None = None,
    max_reviews: int = Query(
        50,
        ge=1,
        le=100,
    ),
) -> dict[str, Any]:
    """Aggregate visible Scale Team and Feedback comments.

    project accepts a 42 project slug or numeric project ID as text.
    project_id is retained for backward compatibility.
    """
    resolved_project: dict[str, Any] | None = None
    effective_project_id = project_id

    if project:
        try:
            resolved_project = (
                await evaluation_service.project(project)
            )
        except FortyTwoAPIError as exc:
            return error_payload(exc)

        resolved_id = resolved_project.get("id")
        if not isinstance(resolved_id, int):
            return {
                "ok": False,
                "status_code": 502,
                "message": (
                    "42 API project response did not contain "
                    "a numeric project ID."
                ),
                "detail": resolved_project,
            }

        if (
            project_id is not None
            and project_id != resolved_id
        ):
            return {
                "ok": False,
                "status_code": 400,
                "message": (
                    "project and project_id refer to "
                    "different projects."
                ),
                "detail": {
                    "project": project,
                    "resolved_project_id": resolved_id,
                    "project_id": project_id,
                },
            }

        effective_project_id = resolved_id

    try:
        items = await evaluation_service.aggregate_reviews(
            login,
            effective_project_id,
            max_pages=5,
            max_reviews=max_reviews,
        )
    except FortyTwoAPIError as exc:
        return error_payload(exc)

    project_meta: dict[str, Any] | None = None
    if resolved_project is not None:
        project_meta = {
            "id": resolved_project.get("id"),
            "name": resolved_project.get("name"),
            "slug": resolved_project.get("slug"),
        }
    elif effective_project_id is not None:
        project_meta = {
            "id": effective_project_id,
            "name": None,
            "slug": None,
        }

    return {
        "ok": True,
        "login": login,
        "project": project_meta,
        "count": len(items),
        "items": items,
    }
