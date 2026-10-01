import asyncio
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from app.api import admin, analyst, comparison, companies, equity_research, financials, live, macro, market, ml_signals, news, quant_forecast, realtime, research_data, research_trade, research_workspace, research_workspace_api, screener, screeners, screening_api, sectors, signals
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

app.include_router(comparison.router)
app.include_router(analyst.router)
app.include_router(companies.router)
app.include_router(sectors.router)
app.include_router(financials.router)
app.include_router(market.router)
app.include_router(live.router)
app.include_router(screener.router)
app.include_router(screeners.router)
app.include_router(screening_api.router)
app.include_router(news.router)
app.include_router(macro.router)
app.include_router(signals.router)
app.include_router(ml_signals.router)
app.include_router(admin.router)
app.include_router(equity_research.router)
app.include_router(quant_forecast.router)
app.include_router(research_data.router)
app.include_router(research_workspace_api.router)
app.include_router(research_trade.router)
app.include_router(research_workspace.router)
app.include_router(realtime.router)


@app.on_event("startup")
async def startup_event():
    """Start background tasks on app startup."""
    asyncio.create_task(realtime.broadcast_market_updates())
    logger.info("Started real-time market data broadcaster")


@app.get("/", include_in_schema=False)
def root() -> RedirectResponse:
    """This is an API-only backend with nothing to render at the bare root -- redirect
    anyone who lands here (a person, not the frontend, which never calls "/") to the
    interactive API docs instead of a bare {"detail": "Not Found"}."""
    return RedirectResponse(url="/docs")


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "app": settings.app_name, "environment": settings.environment}
