from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import admin, comparison, companies, financials, live, macro, market, news, screener, sectors, signals
from app.core.config import get_settings

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
app.include_router(companies.router)
app.include_router(sectors.router)
app.include_router(financials.router)
app.include_router(market.router)
app.include_router(live.router)
app.include_router(screener.router)
app.include_router(news.router)
app.include_router(macro.router)
app.include_router(signals.router)
app.include_router(admin.router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "app": settings.app_name, "environment": settings.environment}
