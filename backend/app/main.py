from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import admin, companies, financials, macro, market, news, screener, signals
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

app.include_router(companies.router)
app.include_router(financials.router)
app.include_router(market.router)
app.include_router(screener.router)
app.include_router(news.router)
app.include_router(macro.router)
app.include_router(signals.router)
app.include_router(admin.router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "app": settings.app_name, "environment": settings.environment}
