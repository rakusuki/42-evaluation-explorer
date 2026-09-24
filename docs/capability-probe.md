# Capability Probe

This phase verifies which evaluation-related resources the current
42 API application token can actually read before the product is
expanded.

The generated report is intentionally sanitized. It records counts,
field names, selected IDs, and whether comment/final_mark fields are
present. It does not store raw review comments or full user payloads.

## Run

Create .env from .env.example and set your own 42 API credentials.
Never commit .env.

From the repository root:

    python -m scripts.probe_report --login YOUR_42_LOGIN

To also test project-specific access:

    python -m scripts.probe_report \
      --login YOUR_42_LOGIN \
      --project a-maze-ing

Default output:

    reports/capability-report.json

The reports directory is ignored by Git.

## FastAPI endpoint

Start the app:

    uvicorn app.main:app --reload

Then request:

    GET /api/test/report/{login}

Optionally:

    GET /api/test/report/{login}?project=a-maze-ing

## Findings

accessible_comment_paths lists comment-bearing resources where at
least one non-empty comment was observed in the sampled data.

project_scales_access is one of:
allowed, forbidden, error, or not_tested.

If no comment path is observed, test a user/project combination known
to have completed peer evaluations before concluding that comments are
inaccessible.

Review the generated JSON before sharing it, especially the login and
numeric IDs.
