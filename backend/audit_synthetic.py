#!/usr/bin/env python
"""Audit database for synthetic row contamination."""

import psycopg2

try:
    conn = psycopg2.connect(
        host="localhost",
        port=5432,
        database="psx_fertilizer",
        user="psx",
        password="psx"
    )
    cur = conn.cursor()

    print("=== PRICE_OHLCV AUDIT ===\n")

    cur.execute("""
        SELECT is_synthetic, quality_status, COUNT(*) as count
        FROM price_ohlcv
        GROUP BY is_synthetic, quality_status
        ORDER BY is_synthetic, quality_status;
    """)

    for is_syn, qual_stat, count in cur.fetchall():
        print(f"is_synthetic={is_syn}, quality_status={qual_stat}: {count:,} rows")

    print("\n=== PROBLEM ROWS: is_synthetic=False + quality_status='unknown' ===")
    cur.execute("""
        SELECT COUNT(*) FROM price_ohlcv
        WHERE is_synthetic = FALSE AND quality_status = 'unknown';
    """)
    problem_count = cur.fetchone()[0]
    print(f"Count: {problem_count:,} rows (potential legacy synthetic data)")

    print("\n=== Total rows in price_ohlcv ===")
    cur.execute("SELECT COUNT(*) FROM price_ohlcv;")
    total = cur.fetchone()[0]
    print(f"Total: {total:,} rows")

    print("\n=== INDEX_OHLCV AUDIT ===\n")

    cur.execute("""
        SELECT is_synthetic, quality_status, COUNT(*) as count
        FROM index_ohlcv
        GROUP BY is_synthetic, quality_status
        ORDER BY is_synthetic, quality_status;
    """)

    for is_syn, qual_stat, count in cur.fetchall():
        print(f"is_synthetic={is_syn}, quality_status={qual_stat}: {count:,} rows")

    print("\n=== PROBLEM ROWS: is_synthetic=False + quality_status='unknown' ===")
    cur.execute("""
        SELECT COUNT(*) FROM index_ohlcv
        WHERE is_synthetic = FALSE AND quality_status = 'unknown';
    """)
    problem_count = cur.fetchone()[0]
    print(f"Count: {problem_count:,} rows (potential legacy synthetic data)")

    print("\n=== Sample problem rows from price_ohlcv ===")
    cur.execute("""
        SELECT security_id, trade_date, open, high, low, close, is_synthetic, quality_status
        FROM price_ohlcv
        WHERE is_synthetic = FALSE AND quality_status = 'unknown'
        LIMIT 5;
    """)

    print("security_id | date | open | high | low | close | is_synthetic | quality_status")
    for row in cur.fetchall():
        print(f"{row[0]} | {row[1]} | {row[2]} | {row[3]} | {row[4]} | {row[5]} | {row[6]} | {row[7]}")

    cur.close()
    conn.close()

except Exception as e:
    print(f"Error: {e}")
    print("Is PostgreSQL running on localhost:55432?")
