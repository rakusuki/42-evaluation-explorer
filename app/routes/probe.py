from __future__ import annotations

from typing import Any, Awaitable, Callable

from fastapi import APIRouter, HTTPException, Query

from app.forty_two import FortyTwoAPIError, forty_two_client
from app.services.evaluation import evaluation_service


router = APIRouter(prefix="/api/test", tags=["capability-probe"])


async def run_probe(call: Callable[[], Awaitable[Any]]) -> dict[str, Any]:
    try:
        data = await call()
        return {"ok": True, "data": data}
    except FortyTwoAPIError as exc:
        return {
            "ok": False,
            "status_code": exc.status_code,
            "message": exc.message,
            "detail": exc.body,
        }


@router.get("/token")
async def probe_token() -> dict[str, Any]:
    result = await run_probe(forty_two_client.token_info)
    if result.get("ok") and isinstance(result.get("data"), dict):
        # token/info does not normally include the bearer token itself, but this
        # keeps the endpoint safe even if the upstream response changes.
        result["data"].pop("access_token", None)
    return result


@router.get("/users/{login}")
async def probe_user(login: str) -> dict[str, Any]:
    return await run_probe(lambda: evaluation_service.user(login))


@router.get("/users/{login}/projects")
async def probe_user_projects(login: str) -> dict[str, Any]:
    return await run_probe(lambda: evaluation_service.user_projects(login))


@router.get("/users/{login}/teams")
async def probe_user_teams(login: str) -> dict[str, Any]:
    return await run_probe(lambda: evaluation_service.teams_for_user(login))


@router.get("/users/{login}/scale-teams/as-corrected")
async def probe_as_corrected(login: str) -> dict[str, Any]:
    return await run_probe(lambda: evaluation_service.scale_teams_as_corrected(login))


@router.get("/users/{login}/scale-teams/as-corrector")
async def probe_as_corrector(login: str) -> dict[str, Any]:
    return await run_probe(lambda: evaluation_service.scale_teams_as_corrector(login))


@router.get("/projects/{project_id_or_slug}")
async def probe_project(project_id_or_slug: str) -> dict[str, Any]:
    return await run_probe(lambda: evaluation_service.project(project_id_or_slug))


@router.get("/projects/{project_id_or_slug}/scales")
async def probe_project_scales(project_id_or_slug: str) -> dict[str, Any]:
    return await run_probe(lambda: evaluation_service.project_scales(project_id_or_slug))


@router.get("/scale-teams/{scale_team_id}")
async def probe_scale_team(scale_team_id: int) -> dict[str, Any]:
    return await run_probe(lambda: evaluation_service.scale_team(scale_team_id))


@router.get("/scale-teams/{scale_team_id}/feedbacks")
async def probe_feedbacks(scale_team_id: int) -> dict[str, Any]:
    return await run_probe(lambda: evaluation_service.scale_team_feedbacks(scale_team_id))


@router.get("/teams/{team_id}/uploads")
async def probe_team_uploads(team_id: int) -> dict[str, Any]:
    return await run_probe(lambda: evaluation_service.team_uploads(team_id))


@router.get("/raw")
async def probe_raw(
    resource: str = Query(..., description="Whitelisted probe name"),
    value: str = Query(..., description="Login, ID, or slug for the probe"),
) -> dict[str, Any]:
    # Keep arbitrary upstream URLs out of the API. This is intentionally a
    # whitelist so the endpoint cannot become an SSRF/open-proxy primitive.
    probes: dict[str, Callable[[], Awaitable[Any]]] = {
        "user": lambda: evaluation_service.user(value),
        "user_projects": lambda: evaluation_service.user_projects(value),
        "user_teams": lambda: evaluation_service.teams_for_user(value),
        "as_corrected": lambda: evaluation_service.scale_teams_as_corrected(value),
        "as_corrector": lambda: evaluation_service.scale_teams_as_corrector(value),
        "project": lambda: evaluation_service.project(value),
        "project_scales": lambda: evaluation_service.project_scales(value),
    }
    call = probes.get(resource)
    if call is None:
        raise HTTPException(status_code=400, detail=f"Unsupported probe: {resource}")
    return await run_probe(call)
