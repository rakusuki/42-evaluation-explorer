from __future__ import annotations

from app.services.evaluation import EvaluationService


def test_compact_project_user() -> None:
    item = {
        "id": 7,
        "status": "finished",
        "final_mark": 100,
        "validated?": True,
        "marked_at": "2026-09-20T10:00:00Z",
        "updated_at": "2026-09-20T10:00:01Z",
        "project": {"id": 42, "name": "a-maze-ing"},
    }

    compact = EvaluationService.compact_project_user(item)

    assert compact["project_id"] == 42
    assert compact["project_name"] == "a-maze-ing"
    assert compact["status"] == "finished"
    assert compact["final_mark"] == 100
    assert compact["validated"] is True
