from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.config import settings
from app.routes.probe import router as probe_router
from app.routes.search import router as search_router


BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(
    title="42 Evaluation Explorer",
    description=(
        "MVP for probing and exploring evaluation data "
        "exposed by the 42 API."
    ),
    version="0.2.0",
)

app.include_router(probe_router)
app.include_router(search_router)
app.mount(
    "/static",
    StaticFiles(directory=BASE_DIR / "static"),
    name="static",
)
templates = Jinja2Templates(
    directory=BASE_DIR / "templates"
)


@app.get("/health")
async def health() -> dict[str, object]:
    return {
        "ok": True,
        "service": "42-evaluation-explorer",
        "version": "0.2.0",
        "credentials_configured": (
            settings.credentials_configured
        ),
    }


@app.get(
    "/",
    response_class=HTMLResponse,
)
async def index(
    request: Request,
) -> HTMLResponse:
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "credentials_configured": (
                settings.credentials_configured
            )
        },
    )
