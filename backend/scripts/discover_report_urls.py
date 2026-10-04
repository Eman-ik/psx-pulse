#!/usr/bin/env python3
"""Discover valid annual report URLs by testing common patterns.

This script:
1. Tests known and pattern-based URLs
2. Validates they are actually PDFs
3. Reports working URLs for ingestion

Usage:
    python discover_report_urls.py
"""

import sys
import os
import logging
import httpx
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.ingestion.report_urls_seed import get_report_urls_to_try

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) psx-fertilizer-research-pilot/0.1"}


def test_url(url: str, timeout: int = 10) -> bool:
    """Test if URL is accessible and returns PDF content."""
    try:
        response = httpx.head(url, headers=HEADERS, timeout=timeout, follow_redirects=True)

        # Check status
        if response.status_code != 200:
            return False

        # Check content type
        content_type = response.headers.get("content-type", "").lower()
        if "pdf" not in content_type:
            return False

        return True
    except Exception:
        return False


def discover_reports():
    """Test URLs and find valid report links."""
    logger.info("=" * 70)
    logger.info("DISCOVERING VALID ANNUAL REPORT URLS")
    logger.info("=" * 70)

    companies = {
        "FFC": [2020, 2021, 2022, 2023],
        "EFERT": [2023, 2024, 2025],
    }

    working_urls = {}

    for company, years in companies.items():
        logger.info(f"\n{company}:")
        working_urls[company] = {}

        urls_to_try = get_report_urls_to_try(company, years)

        for year in sorted(years):
            if year not in urls_to_try:
                logger.info(f"  FY{year}: No patterns defined")
                continue

            candidates = urls_to_try[year]
            found = None

            for url in candidates:
                status = "[OK]" if test_url(url) else "[failed]"
                logger.info(f"    {url[:70]:70} {status}")

                if status == "[OK]":
                    found = url
                    break

            if found:
                working_urls[company][year] = found
                logger.info(f"  FY{year}: {found}")
            else:
                logger.info(f"  FY{year}: NOT FOUND")

    # Report summary
    logger.info("\n" + "=" * 70)
    logger.info("DISCOVERY SUMMARY")
    logger.info("=" * 70)

    for company in companies:
        found_count = len(working_urls.get(company, {}))
        total_count = len(companies[company])
        logger.info(f"\n{company}: {found_count}/{total_count} reports found")

        for year in sorted(companies[company]):
            url = working_urls.get(company, {}).get(year)
            if url:
                logger.info(f"  FY{year}: [OK] {url}")
            else:
                logger.info(f"  FY{year}: [MISSING] Need manual discovery")

    logger.info("\n" + "=" * 70)
    logger.info("NEXT STEPS")
    logger.info("=" * 70)
    logger.info("\nIf reports are missing:")
    logger.info("1. Check company IR websites manually")
    logger.info("2. Add discovered URLs to app/ingestion/report_urls_seed.py")
    logger.info("3. Re-run this script to verify")
    logger.info("\nThen run: python scripts/ingest_annual_reports.py")

    return working_urls


if __name__ == "__main__":
    urls = discover_reports()
