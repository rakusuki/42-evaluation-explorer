from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Awaitable, Callable

from app.forty_two import FortyTwoAPIError
from app.services.evaluation import EvaluationService, evaluation_service


ProbeCall = Callable[[], Awaitable[Any]]


class CapabilityReportService:
    def __init__(self, service: EvaluationService = evaluation_service) -> None:
        self.service = service

    async def build(self, login: str, project: str | None = None) -> dict[str, Any]:
        probes: dict[str, dict[str, Any]] = {}

        probes["user"] = await self._probe(lambda: self.service.user(login))
        probes["user_projects"] = await self._probe(
            lambda: self.service.user_projects(login)
        )
        probes["user_teams"] = await self._probe(
            lambda: self.service.teams_for_user(login)
        )
        probes["scale_teams_as_corrected"] = await self._probe(
            lambda: self.service.scale_teams_as_corrected(login)
        )
        probes["scale_teams_as_corrector"] = await self._probe(
            lambda: self.service.scale_teams_as_corrector(login)
        )

        if project:
            probes["project"] = await self._probe(
                lambda: self.service.project(project)
            )
            probes["project_scales"] = await self._probe(
                lambda: self.service.project_scales(project)
            )

        candidate_probe = probes.get("scale_teams_as_corrected", {})
        if (
            not candidate_probe.get("ok")
            or not candidate_probe.get("summary", {}).get("count")
        ):
            candidate_probe = probes.get("scale_teams_as_corrector", {})

        scale_team_id = self._first_id(candidate_probe, "id")
        team_id = self._first_team_id(candidate_probe)

        if scale_team_id is not None:
            probes["scale_team_detail"] = await self._probe(
                lambda: self.service.scale_team(scale_team_id)
            )
            probes["scale_team_feedbacks"] = await self._probe(
                lambda: self.service.scale_team_feedbacks(scale_team_id)
            )

        if team_id is not None:
            probes["team_uploads"] = await self._probe(
                lambda: self.service.team_uploads(team_id)
            )

        return {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "login": login,
            "project": project,
            "probes": probes,
            "findings": self._findings(probes),
        }

    async def _probe(self, call: ProbeCall) -> dict[str, Any]:
        try:
            data = await call()
            return {
                "ok": True,
                "summary": self.summarize_payload(data),
            }
        except FortyTwoAPIError as exc:
            return {
                "ok": False,
                "status_code": exc.status_code,
                "message": exc.message,
            }

    @staticmethod
    def summarize_payload(data: Any) -> dict[str, Any]:
        if isinstance(data, list):
            dict_items = [item for item in data if isinstance(item, dict)]
            keys = sorted(
                {key for item in dict_items[:20] for key in item.keys()}
            )
            return {
                "kind": "list",
                "count": len(data),
                "item_keys": keys,
                "comment_fields": CapabilityReportService._field_stats(
                    dict_items, "comment"
                ),
                "final_mark_fields": CapabilityReportService._field_stats(
                    dict_items, "final_mark"
                ),
                "ids": [
                    item.get("id")
                    for item in dict_items[:5]
                    if item.get("id") is not None
                ],
                "team_ids": CapabilityReportService._collect_team_ids(
                    dict_items[:5]
                ),
                "project_ids": CapabilityReportService._collect_project_ids(
                    dict_items[:5]
                ),
            }

        if isinstance(data, dict):
            return {
                "kind": "object",
                "keys": sorted(data.keys()),
                "has_comment": bool(data.get("comment")),
                "has_final_mark": data.get("final_mark") is not None,
                "id": data.get("id"),
                "team_id": (data.get("team") or {}).get("id")
                if isinstance(data.get("team"), dict)
                else data.get("team_id"),
            }

        return {"kind": type(data).__name__}

    @staticmethod
    def _field_stats(
        items: list[dict[str, Any]], field: str
    ) -> dict[str, Any]:
        present = sum(1 for item in items if field in item)
        non_empty = sum(
            1 for item in items if item.get(field) not in (None, "", [])
        )
        return {"present": present, "non_empty": non_empty}

    @staticmethod
    def _collect_team_ids(items: list[dict[str, Any]]) -> list[Any]:
        values: list[Any] = []
        for item in items:
            direct = item.get("team_id")
            nested = item.get("team")
            value = direct
            if value is None and isinstance(nested, dict):
                value = nested.get("id")
            if value is not None and value not in values:
                values.append(value)
        return values

    @staticmethod
    def _collect_project_ids(items: list[dict[str, Any]]) -> list[Any]:
        values: list[Any] = []
        for item in items:
            direct = item.get("project_id")
            nested = item.get("team")
            value = direct
            if value is None and isinstance(nested, dict):
                value = nested.get("project_id")
            if value is not None and value not in values:
                values.append(value)
        return values

    @staticmethod
    def _first_id(probe: dict[str, Any], field: str) -> int | None:
        if not probe.get("ok"):
            return None
        ids = probe.get("summary", {}).get("ids", [])
        if field == "id" and ids:
            value = ids[0]
            return value if isinstance(value, int) else None
        return None

    @staticmethod
    def _first_team_id(probe: dict[str, Any]) -> int | None:
        if not probe.get("ok"):
            return None
        ids = probe.get("summary", {}).get("team_ids", [])
        if not ids:
            return None
        value = ids[0]
        return value if isinstance(value, int) else None

    @staticmethod
    def _findings(
        probes: dict[str, dict[str, Any]]
    ) -> dict[str, Any]:
        def field_non_empty(name: str, field: str) -> int:
            return int(
                probes.get(name, {})
                .get("summary", {})
                .get(field, {})
                .get("non_empty", 0)
            )

        corrected_comments = field_non_empty(
            "scale_teams_as_corrected", "comment_fields"
        )
        upload_comments = field_non_empty(
            "team_uploads", "comment_fields"
        )
        feedback_comments = field_non_empty(
            "scale_team_feedbacks", "comment_fields"
        )

        accessible_paths: list[str] = []
        if corrected_comments:
            accessible_paths.append("scale_team.comment")
        if upload_comments:
            accessible_paths.append("teams_uploads.comment")
        if feedback_comments:
            accessible_paths.append("feedback.comment")

        project_scales = probes.get("project_scales")
        project_scales_access = "not_tested"
        if project_scales:
            if project_scales.get("ok"):
                project_scales_access = "allowed"
            elif project_scales.get("status_code") == 403:
                project_scales_access = "forbidden"
            else:
                project_scales_access = "error"

        if accessible_paths:
            next_step = (
                "Use the accessible comment path(s) to implement "
                "project-filtered review aggregation."
            )
        else:
            next_step = (
                "No non-empty review-comment path was observed in the "
                "sampled data. Inspect another user/project with known "
                "evaluations before changing the product scope."
            )

        return {
            "accessible_comment_paths": accessible_paths,
            "project_scales_access": project_scales_access,
            "next_step": next_step,
        }


capability_report_service = CapabilityReportService()
