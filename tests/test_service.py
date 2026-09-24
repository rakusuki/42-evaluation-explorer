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
        "project": {
            "id": 42,
            "name": "a-maze-ing",
        },
    }

    compact = EvaluationService.compact_project_user(
        item
    )

    assert compact["project_id"] == 42
    assert compact["project_name"] == "a-maze-ing"
    assert compact["status"] == "finished"
    assert compact["final_mark"] == 100
    assert compact["validated"] is True


def test_compact_feedback() -> None:
    item = {
        "id": 9,
        "comment": "Helpful feedback",
        "rating": 4,
        "user": {
            "login": "peer42",
        },
        "created_at": "2026-09-20T10:00:00Z",
    }

    compact = EvaluationService.compact_feedback(item)

    assert compact == {
        "id": 9,
        "comment": "Helpful feedback",
        "rating": 4,
        "user_login": "peer42",
        "created_at": "2026-09-20T10:00:00Z",
        "updated_at": None,
    }


def test_compact_review_merges_comment_sources() -> None:
    row = {
        "id": 123,
        "comment": "Scale comment",
        "final_mark": 100,
        "corrector": {
            "login": "corrector42",
        },
        "team": {
            "id": 77,
            "project_id": 42,
        },
    }
    feedbacks = [
        {
            "id": 1,
            "comment": "Feedback comment",
            "rating": 5,
            "user": {
                "login": "student42",
            },
        },
        {
            "id": 2,
            "comment": "Scale comment",
            "rating": 3,
        },
    ]

    compact = EvaluationService.compact_review(
        row,
        feedbacks,
    )

    assert compact["team_id"] == 77
    assert compact["project_id"] == 42
    assert compact["final_mark"] == 100
    assert compact["corrector"] == "corrector42"
    assert compact["comments"] == [
        {
            "source": "scale_team",
            "comment": "Scale comment",
            "user_login": "corrector42",
        },
        {
            "source": "feedback",
            "comment": "Feedback comment",
            "user_login": "student42",
            "rating": 5,
        },
    ]
