"""Hybrid report discovery: automated + graceful fallback.

PHASE 1: Automated discovery from official sources
- PSX company filings
- Company official websites
- Standard IR paths

PHASE 2: Fallback when automated fails
- Return what was found
- Provide structured guidance for manual discovery
- Accept URLs provided through any means (manual browsing, scripts, etc)

The key principle: AUTOMATION FIRST, manual fallback only when needed.
No synthetic data or fabricated numbers ever.
"""

import logging
import os
import sys
from datetime import datetime
from typing import Optional

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import httpx
from app.ingestion.official_report_discovery import discover_all_reports, COMPANIES

logger = logging.getLogger(__name__)


class DiscoveryResult:
    """Structured discovery result for a company/year."""

    def __init__(self, ticker: str, year: int):
        self.ticker = ticker
        self.year = year
        self.url: Optional[str] = None
        self.source: Optional[str] = None  # "psx", "company_website", "manual"
        self.validated: bool = False
        self.discovered_at: Optional[datetime] = None
        self.error: Optional[str] = None


def load_manual_overrides() -> dict[str, dict[int, str]]:
    """Load manually provided report URLs from environment or config file.

    Users can provide URLs through:
    1. Environment variables: FFC_REPORTS_2023="https://...", etc
    2. Config file: report_overrides.json in backend directory
    3. Git-ignored config: report_urls_manual.py (not tracked)
    """
    overrides = {}

    # Check environment variables
    for ticker in ["FFC", "EFERT"]:
        overrides[ticker] = {}
        company = COMPANIES.get(ticker)
        if not company:
            continue

        for year in company["required_years"]:
            env_var = f"{ticker}_AR_{year}"
            if env_var in os.environ:
                url = os.environ[env_var]
                logger.info(f"Loaded {ticker} FY{year} from environment: {url[:60]}")
                overrides[ticker][year] = url

    # Check for manual config file (git-ignored)
    manual_config_path = "app/ingestion/report_urls_manual.py"
    if os.path.exists(manual_config_path):
        logger.info(f"Loading manual overrides from {manual_config_path}")
        try:
            spec = __import__("importlib.util").util.spec_from_file_location("manual", manual_config_path)
            module = __import__("importlib.util").util.module_from_spec(spec)
            spec.loader.exec_module(module)

            if hasattr(module, "MANUAL_REPORT_URLS"):
                for ticker, years in module.MANUAL_REPORT_URLS.items():
                    overrides.setdefault(ticker, {}).update(years)
                    logger.info(f"Loaded {len(years)} reports for {ticker} from manual config")
        except Exception as e:
            logger.warning(f"Failed to load manual config: {e}")

    return overrides


def discover_reports_with_fallback() -> dict[str, dict[int, DiscoveryResult]]:
    """Discover reports with automated first attempt, then manual fallback.

    Returns: {
        "FFC": {
            2020: DiscoveryResult(url="...", source="psx", validated=True),
            2021: DiscoveryResult(url=None, error="Not found in automated discovery"),
            ...
        },
        ...
    }
    """
    logger.info("=" * 70)
    logger.info("REPORT DISCOVERY (Automated + Manual Fallback)")
    logger.info("=" * 70)

    # PHASE 1: Automated discovery
    logger.info("\nPHASE 1: Automated Discovery")
    logger.info("-" * 70)

    automated = discover_all_reports()
    results = {}

    for ticker in ["FFC", "EFERT"]:
        results[ticker] = {}
        company = COMPANIES.get(ticker)
        if not company:
            continue

        for year in company["required_years"]:
            result = DiscoveryResult(ticker, year)

            if year in automated.get(ticker, {}):
                report_data = automated[ticker][year]
                result.url = report_data.get("url")
                result.source = report_data.get("source")
                result.validated = report_data.get("validated", False)
                result.discovered_at = datetime.utcnow()

            results[ticker][year] = result

    # PHASE 2: Manual fallback
    logger.info("\nPHASE 2: Manual Fallback")
    logger.info("-" * 70)

    manual_overrides = load_manual_overrides()

    for ticker, years_dict in manual_overrides.items():
        if ticker not in results:
            results[ticker] = {}

        for year, url in years_dict.items():
            if year not in results[ticker]:
                results[ticker][year] = DiscoveryResult(ticker, year)

            result = results[ticker][year]
            result.url = url
            result.source = "manual"
            result.validated = True  # Trust manually provided URLs
            result.discovered_at = datetime.utcnow()
            logger.info(f"{ticker} FY{year}: Loaded from manual override")

    # Report status
    logger.info("\n" + "=" * 70)
    logger.info("DISCOVERY STATUS")
    logger.info("=" * 70)

    for ticker in ["FFC", "EFERT"]:
        company = COMPANIES.get(ticker)
        if not company:
            continue

        found = sum(1 for r in results[ticker].values() if r.validated)
        total = len(company["required_years"])

        logger.info(f"\n{ticker}: {found}/{total} reports found")
        for year in sorted(company["required_years"]):
            result = results[ticker].get(year)
            if result and result.validated:
                logger.info(f"  FY{year}: ✓ ({result.source})")
            else:
                logger.info(f"  FY{year}: ✗ (not found)")

    return results


def print_discovery_guidance(results: dict) -> None:
    """Print guidance for providing missing report URLs."""
    missing = []

    for ticker, years_dict in results.items():
        for year, result in years_dict.items():
            if not result.validated:
                missing.append((ticker, year))

    if not missing:
        logger.info("\n" + "=" * 70)
        logger.info("ALL REPORTS DISCOVERED")
        logger.info("=" * 70)
        logger.info("\nReady to proceed with extraction and ingestion.")
        return

    logger.info("\n" + "=" * 70)
    logger.info("MANUAL DISCOVERY NEEDED")
    logger.info("=" * 70)
    logger.info(f"\nMissing {len(missing)} reports. To provide URLs:")
    logger.info("\nOption 1: Create app/ingestion/report_urls_manual.py (git-ignored):")
    logger.info("""
MANUAL_REPORT_URLS = {
    "FFC": {
        2020: "https://www.fauji.com.pk/.../FFC_AR_2020.pdf",
        2021: "https://www.fauji.com.pk/.../FFC_AR_2021.pdf",
        ...
    },
    "EFERT": {
        2023: "https://www.engrofertilizers.com/.../EFERT_AR_2023.pdf",
        ...
    }
}
""")

    logger.info("\nOption 2: Set environment variables:")
    for ticker, year in missing:
        env_var = f"{ticker}_AR_{year}"
        logger.info(f"  export {env_var}='https://...'")

    logger.info("\nThen re-run discovery or extraction.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    results = discover_reports_with_fallback()
    print_discovery_guidance(results)

    # Output structured results
    print("\n" + "=" * 70)
    print("RESULTS (JSON)")
    print("=" * 70)

    import json
    output = {}
    for ticker, years_dict in results.items():
        output[ticker] = {}
        for year, result in years_dict.items():
            output[ticker][year] = {
                "url": result.url,
                "source": result.source,
                "validated": result.validated,
            }

    print(json.dumps(output, indent=2))
