from app.services.capability import CapabilityReportService


def test_summarize_list_redacts_comment_body() -> None:
    payload = [
        {
            "id": 1,
            "comment": "sensitive review",
            "final_mark": 100,
            "team": {"id": 7, "project_id": 42},
        },
        {
            "id": 2,
            "comment": "",
            "final_mark": None,
            "team": {"id": 8, "project_id": 42},
        },
    ]

    summary = CapabilityReportService.summarize_payload(payload)

    assert summary["count"] == 2
    assert summary["comment_fields"] == {
        "present": 2,
        "non_empty": 1,
    }
    assert summary["final_mark_fields"] == {
        "present": 2,
        "non_empty": 1,
    }
    assert summary["ids"] == [1, 2]
    assert summary["team_ids"] == [7, 8]
    assert "sensitive review" not in str(summary)
