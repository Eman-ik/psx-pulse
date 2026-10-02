# Backend container -- Stage 3 deployment prep (see backend/docs/model_governance.md's
# sibling deployment notes / the project's staged Windows-dev -> Linux-server progression).
# Does not run psx_prices.py/ml_signal_engine.py on its own -- those stay separate
# scheduled jobs (see scripts/run_price_backfill.ps1's eventual cron/systemd-timer
# equivalent), this image only serves the FastAPI app.
FROM python:3.12-slim AS base

# psycopg2-binary avoids needing libpq-dev at build time; lxml/pdfplumber need these
# system libs even with prebuilt wheels for some transitive dependencies.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libxml2 libxslt1.1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Runs as a non-root user -- no reason this process needs root inside the container.
RUN useradd --create-home appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Alembic migrations are a separate step (docker-compose's backend service runs them
# before this, or a deploy script does) -- not baked into the container's own startup,
# so a container restart never silently re-runs migrations against a live DB.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
