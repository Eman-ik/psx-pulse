from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings

settings = get_settings()

# pool_size/max_overflow raised from SQLAlchemy's defaults (5/10 -- a 15-connection
# ceiling a single dev-mode page load can approach on its own, given React Strict
# Mode's double-invoked effects plus several parallel fetches per page). Real
# incident (2026-08-19): every connection ended up stuck in Postgres's real
# 'idle in transaction' state -- not a connection LEAK in the sense of code that
# forgets to close, but request cancellation (a browser tab closed/navigated away
# mid-request) leaving get_db()'s generator cleanup in a state where close() alone
# didn't reliably end the open transaction first. idle_in_transaction_session_timeout
# is Postgres's own backstop: even if application code has another gap like this one,
# the database itself reclaims a connection that's sat idle-in-transaction too long,
# rather than silently starving the pool for the rest of the process's life.
#
# statement_timeout added separately (2026-08-27): idle_in_transaction_session_timeout
# only catches a connection sitting IDLE mid-transaction -- it does nothing for a query
# that's actively running and just hangs (real observed symptom: API requests, e.g.
# GET /ml-signals/research/{id}, hanging 15s+ with no response at all on this
# memory-constrained dev machine, well past pool_pre_ping's narrow guarantee that only
# covers a connection that died while idle in the pool before checkout). 60s, not
# something tighter: app/etl/ml_signal_engine.py's __main__ standalone run shares this
# same engine, and load_price_panel's single un-chunked read across ~250 symbols' full
# price history is a legitimately heavier query that a short timeout would wrongly kill.
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    pool_timeout=10,
    connect_args={
        "options": "-c idle_in_transaction_session_timeout=30000 -c statement_timeout=60000"
    },
)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        # Explicit rollback before close, not just close() alone -- close() is
        # documented to roll back any open transaction, but the real incident above
        # showed that guarantee doesn't reliably hold under request cancellation
        # (a client disconnecting mid-request). Rollback is a no-op if there's
        # nothing pending, so this is safe on every normal request too.
        db.rollback()
        db.close()
