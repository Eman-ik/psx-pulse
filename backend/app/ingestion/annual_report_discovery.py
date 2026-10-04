"""Phase 1: Discover official annual report URLs for FFC and EFERT.

IMPORTANT: PSX DPS portal uses JavaScript to load PDFs dynamically.
We prioritize company investor-relations websites which have directly
accessible PDF links.

Official sources (in priority order):
1. Company's official investor-relations website (direct PDF links)
2. Pakistan Stock Exchange (if direct PDF URLs available)
3. Company downloads/reports pages

This module discovers the official URLs without downloading or parsing yet.
"""

import logging
from datetime import datetime
from typing import Optional
import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# Base URLs
PSX_DPS_BASE = "https://dps.psx.com.pk"
PSX_COMPANY_ANNOUNCEMENTS = f"{PSX_DPS_BASE}/company"

# Known IR sites
EFERT_IR_SITE = "https://www.engrofert.com"  # investor relations
FFC_IR_SITE = "https://www.fauji.com.pk"  # investor relations

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) psx-fertilizer-research-pilot/0.1"}


def discover_psx_annual_reports(symbol: str, years: list[int]) -> dict[int, str]:
    """Discover FY annual reports from PSX announcements page.

    Returns: {fiscal_year: url}
    """
    url = f"{PSX_COMPANY_ANNOUNCEMENTS}/{symbol}"
    logger.info(f"Discovering PSX reports for {symbol} at {url}")

    try:
        response = httpx.get(url, headers=HEADERS, timeout=20)
        response.raise_for_status()
    except Exception as e:
        logger.error(f"Failed to fetch PSX page for {symbol}: {e}")
        return {}

    soup = BeautifulSoup(response.text, "lxml")
    section = soup.find("div", id="announcements")
    if not section:
        logger.warning(f"No announcements section found for {symbol}")
        return {}

    # Look for Financial Results tab entries
    results = {}
    for link in section.find_all("a"):
        text = link.get_text(strip=True).lower()
        href = link.get("href", "")

        # Match "Financial Results" announcements with year in title
        if "result" in text or "financial" in text.lower():
            for year in years:
                if str(year) in text or str(year) in href:
                    full_url = href if href.startswith("http") else f"{PSX_DPS_BASE}{href}"
                    results[year] = full_url
                    logger.info(f"  FY{year}: {full_url}")

    return results


def discover_efert_ir_reports(years: list[int]) -> dict[int, str]:
    """Discover EFERT annual reports from IR website.

    EFERT's IR site is at: https://www.engrofert.com
    Reports typically at: /investor-relations/ or /about-us/reports/

    Returns: {fiscal_year: url}
    """
    logger.info(f"Discovering EFERT reports from {EFERT_IR_SITE}")

    # Common paths for annual reports on IR sites
    candidates = [
        "/investor-relations/",
        "/investor-relations/annual-reports/",
        "/investor-relations/reports/",
        "/about-us/reports/",
        "/downloads/",
    ]

    reports = {}

    for path in candidates:
        url = f"{EFERT_IR_SITE}{path}"
        try:
            response = httpx.get(url, headers=HEADERS, timeout=20)
            if response.status_code != 200:
                continue

            soup = BeautifulSoup(response.text, "lxml")

            # Look for links containing year
            for link in soup.find_all("a"):
                text = link.get_text(strip=True).lower()
                href = link.get("href", "")

                for year in years:
                    year_str = str(year)
                    # Match: "annual report 2024", "2024.pdf", "ar2024", etc
                    if year_str in text or year_str in href:
                        if "annual" in text or "report" in text or ".pdf" in href:
                            full_url = href if href.startswith("http") else f"{EFERT_IR_SITE}{href}"
                            reports[year] = full_url
                            logger.info(f"  FY{year}: {full_url}")
                            break
        except Exception as e:
            logger.debug(f"Failed to fetch {url}: {e}")

    return reports


def discover_ffc_ir_reports(years: list[int]) -> dict[int, str]:
    """Discover FFC annual reports from IR website.

    FFC's IR site is at: https://www.fauji.com.pk

    Returns: {fiscal_year: url}
    """
    logger.info(f"Discovering FFC reports from {FFC_IR_SITE}")

    candidates = [
        "/investor-relations/",
        "/investor-relations/financial-reports/",
        "/investor-relations/annual-reports/",
        "/about-us/reports/",
        "/downloads/",
    ]

    reports = {}

    for path in candidates:
        url = f"{FFC_IR_SITE}{path}"
        try:
            response = httpx.get(url, headers=HEADERS, timeout=20)
            if response.status_code != 200:
                continue

            soup = BeautifulSoup(response.text, "lxml")

            for link in soup.find_all("a"):
                text = link.get_text(strip=True).lower()
                href = link.get("href", "")

                for year in years:
                    year_str = str(year)
                    if year_str in text or year_str in href:
                        if "annual" in text or "report" in text or ".pdf" in href:
                            full_url = href if href.startswith("http") else f"{FFC_IR_SITE}{href}"
                            reports[year] = full_url
                            logger.info(f"  FY{year}: {full_url}")
                            break
        except Exception as e:
            logger.debug(f"Failed to fetch {url}: {e}")

    return reports


def discover_all_reports() -> dict[str, dict[int, str]]:
    """Discover all annual reports for FFC and EFERT.

    Returns: {
        "FFC": {2020: url, 2021: url, 2022: url, 2023: url},
        "EFERT": {2023: url, 2024: url, 2025: url}
    }
    """
    logger.info("=" * 70)
    logger.info("PHASE 1: ANNUAL REPORT DISCOVERY")
    logger.info("=" * 70)

    # FFC: Try PSX first, then IR site
    ffc_psx = discover_psx_annual_reports("FFC", [2020, 2021, 2022, 2023, 2024])
    ffc_ir = discover_ffc_ir_reports([2020, 2021, 2022, 2023, 2024])

    ffc_reports = {}
    for year in [2020, 2021, 2022, 2023, 2024]:
        # Prefer PSX, fall back to IR
        ffc_reports[year] = ffc_psx.get(year) or ffc_ir.get(year)

    # EFERT: Try IR site first, then PSX
    efert_ir = discover_efert_ir_reports([2023, 2024, 2025])
    efert_psx = discover_psx_annual_reports("EFERT", [2023, 2024, 2025])

    efert_reports = {}
    for year in [2023, 2024, 2025]:
        # Prefer IR, fall back to PSX
        efert_reports[year] = efert_ir.get(year) or efert_psx.get(year)

    # Filter to only found reports
    ffc_reports = {y: u for y, u in ffc_reports.items() if u}
    efert_reports = {y: u for y, u in efert_reports.items() if u}

    logger.info("\n" + "=" * 70)
    logger.info("DISCOVERY SUMMARY")
    logger.info("=" * 70)
    logger.info(f"\nFFC (found {len(ffc_reports)} reports):")
    for year in sorted(ffc_reports.keys()):
        logger.info(f"  FY{year}: {ffc_reports[year]}")

    logger.info(f"\nEFERT (found {len(efert_reports)} reports):")
    for year in sorted(efert_reports.keys()):
        logger.info(f"  FY{year}: {efert_reports[year]}")

    return {
        "FFC": ffc_reports,
        "EFERT": efert_reports,
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    reports = discover_all_reports()
    print("\n" + "=" * 70)
    print("RESULT")
    print("=" * 70)
    import json
    print(json.dumps(reports, indent=2))
