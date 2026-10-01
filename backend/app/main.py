import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from app.api import market, research_data, research_trade, research_workspace_api, screeners, screening_api, sources, sprint4_endpoints
from app.core.config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(sprint4_endpoints.router)
app.include_router(market.router)
app.include_router(screeners.router)
app.include_router(screening_api.router)
app.include_router(research_data.router)
app.include_router(research_workspace_api.router)
app.include_router(research_trade.router)
app.include_router(sources.router)


@app.get("/", include_in_schema=False)
def root() -> RedirectResponse:
    """This is an API-only backend with nothing to render at the bare root -- redirect
    anyone who lands here (a person, not the frontend, which never calls "/") to the
    interactive API docs instead of a bare {"detail": "Not Found"}."""
    return RedirectResponse(url="/docs")


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "app": settings.app_name, "environment": settings.environment}
