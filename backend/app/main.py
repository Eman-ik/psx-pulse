import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from app.api import (
    admin,
    companies,
    comparison,
    data_status,
    fundamentals,
    market,
    research_intelligence,
    research_trade,
    research_workspace,
    screeners,
    screening_api,
    sectors,
    signals,
    sources,
    sprint4_endpoints,
)
from app.api.v1 import companies as v1_companies
from app.core.config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()

app = FastAPI(title=settings.app_name)

# CORS only limits which browser origins can read responses; it is not access control.
# No endpoint uses cookies or auth headers yet, so credentials stay off.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

# Static /companies/* routes must register before sprint4's /companies/{ticker} catch-all.
app.include_router(comparison.router)
app.include_router(companies.router)
app.include_router(sprint4_endpoints.router)
app.include_router(sectors.router)
app.include_router(research_workspace.router)
app.include_router(admin.router)
app.include_router(signals.router)
app.include_router(v1_companies.router)
app.include_router(market.router)
app.include_router(data_status.router)
app.include_router(fundamentals.router)
app.include_router(screeners.router)
app.include_router(screening_api.router)
app.include_router(research_intelligence.router)
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
