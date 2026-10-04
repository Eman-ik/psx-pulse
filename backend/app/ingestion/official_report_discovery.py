"""Official source discovery: ticker → validated annual report PDFs.

Automated discovery from official sources (no manual URL entry).

Priority:
1. PSX company page (dps.psx.com.pk/company/{ticker})
2. Company official website (ffc.com.pk, engrofertilizers.com)
3. Fail if both exhausted

Validates each candidate:
- HTTP 200
- Content-Type: application/pdf
- File size > 100KB (non-trivial)
- PDF magic bytes (checked on download)
"""

import logging
import httpx
import re
from datetime import datetime
from typing import Optional
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) psx-fertilizer/0.1"}

# Company metadata
COMPANIES = {
    "FFC": {
        "name": "Fauji Fertilizer Company Limited",
        "psx_ticker": "FFC",
        "psx_url": "https://dps.psx.com.pk/company/FFC",
        "official_sites": [
            "https://www.ffc.com.pk",
            "https://www.fauji.com.pk",
        ],
        "required_years": [2020, 2021, 2022, 2023, 2024, 2025],
    },
    "EFERT": {
        "name": "Engro Fertilizers Limited",
        "psx_ticker": "EFERT",
        "psx_url": "https://dps.psx.com.pk/company/EFERT",
        "official_sites": [
            "https://www.engrofertilizers.com",
            "https://www.engrofert.com",
        ],
        "required_years": [2023, 2024, 2025],
    },
}


def discover_psx_filings(ticker: str) -> dict[int, str]:
    """Discover annual reports from PSX company page.

    PSX stores recent announcements/filings. We look for:
    - "Annual Report" in title
    - "Financial Statement" in title
    - Year in announcement title

    Returns: {year: url} for found reports
    """
    if ticker not in COMPANIES:
        logger.warning(f"Unknown ticker: {ticker}")
        return {}

    company = COMPANIES[ticker]
    psx_url = company["psx_url"]
    logger.info(f"Discovering PSX filings for {ticker} at {psx_url}")

    try:
        response = httpx.get(psx_url, headers=HEADERS, timeout=20)
        response.raise_for_status()
    except Exception as e:
        logger.warning(f"Failed to fetch PSX page: {e}")
        return {}

    soup = BeautifulSoup(response.text, "lxml")
    found_reports = {}

    # Look for announcements section with financial reports/statements
    section = soup.find("div", id="announcements")
    if not section:
        logger.info("  No announcements section found on PSX page")
        return {}

    # Parse announcements table
    tables = section.find_all("table")
    for table in tables:
        rows = table.find_all("tr")

        for row in rows:
            cells = row.find_all(["td", "th"])
            if len(cells) < 3:
                continue

            # Typical: [Date, Title/Description, Document Link]
            title_cell = cells[1]  # Usually column 1 is title
            link_cell = cells[-1]  # Last column is usually document link

            title_text = title_cell.get_text(strip=True).lower()

            # Look for annual report indicators
            if not any(x in title_text for x in ["annual", "financial", "report", "statement"]):
                continue

            # Try to extract year from title
            year_match = re.search(r"(20\d{2})", title_text)
            if not year_match:
                continue

            year = int(year_match.group(1))
            if year not in company["required_years"]:
                continue

            # Find PDF link in link cell
            link = link_cell.find("a")
            if not link:
                # Try onclick or data attributes
                if link_cell.find("a", href=re.compile(r"\.pdf", re.I)):
                    link = link_cell.find("a", href=re.compile(r"\.pdf", re.I))

            if link and link.get("href"):
                href = link.get("href", "")

                # Handle relative URLs
                if href.startswith("http"):
                    url = href
                elif href.startswith("/"):
                    # PSX relative URL
                    url = f"https://dps.psx.com.pk{href}"
                else:
                    continue

                logger.info(f"  FY{year}: Found {url[:60]}")
                found_reports[year] = url

    return found_reports


def discover_company_website_reports(ticker: str) -> dict[int, str]:
    """Discover annual reports from company official website.

    Searches common paths:
    - /investor-relations/
    - /investments/
    - /reports/
    - /annual-reports/

    Matches report PDFs by year in filename or page text.
    """
    if ticker not in COMPANIES:
        return {}

    company = COMPANIES[ticker]
    logger.info(f"Discovering company website reports for {ticker}")

    found_reports = {}

    for base_url in company["official_sites"]:
        logger.info(f"  Checking {base_url}")

        # Common report paths
        report_paths = [
            "/investor-relations/",
            "/investments/",
            "/reports/",
            "/annual-reports/",
            "/investor-relations/annual-reports/",
            "/ir/reports/",
        ]

        for path in report_paths:
            url = f"{base_url}{path}"

            try:
                response = httpx.get(url, headers=HEADERS, timeout=15, follow_redirects=True)
                if response.status_code != 200:
                    continue

                soup = BeautifulSoup(response.text, "lxml")

                # Look for PDF links containing year
                for link in soup.find_all("a", href=True):
                    href = link.get("href", "")
                    link_text = link.get_text(strip=True).lower()

                    # Check if this looks like a report
                    if not any(x in link_text or x in href.lower() for x in ["annual", "report", "ar", ".pdf"]):
                        continue

                    # Extract year
                    year_match = re.search(r"(20\d{2})", href + " " + link_text)
                    if not year_match:
                        continue

                    year = int(year_match.group(1))
                    if year not in company["required_years"]:
                        continue

                    # Build full URL
                    if href.startswith("http"):
                        full_url = href
                    elif href.startswith("/"):
                        full_url = f"{base_url}{href}"
                    else:
                        full_url = f"{url.rstrip('/')}/{href}"

                    # Validate before adding
                    if is_valid_pdf(full_url):
                        logger.info(f"    FY{year}: {full_url[:60]}")
                        found_reports[year] = full_url

            except Exception as e:
                logger.debug(f"    Failed to fetch {url}: {e}")

    return found_reports


def is_valid_pdf(url: str, timeout: int = 15) -> bool:
    """Validate that URL points to an actual PDF.

    Checks:
    - HTTP 200
    - Content-Type: application/pdf
    - File size > 100KB
    - PDF magic bytes
    """
    try:
        # Head request first
        response = httpx.head(url, headers=HEADERS, timeout=timeout, follow_redirects=True)

        if response.status_code != 200:
            return False

        # Check content type
        content_type = response.headers.get("content-type", "").lower()
        if "pdf" not in content_type:
            return False

        # Check file size
        content_length = response.headers.get("content-length")
        if content_length:
            size = int(content_length)
            if size < 100_000:  # Less than 100KB is suspicious
                return False

        # Download a bit and check PDF magic bytes
        response = httpx.get(url, headers=HEADERS, timeout=timeout, follow_redirects=True)
        if response.status_code != 200:
            return False

        # Check PDF magic bytes (%PDF)
        if not response.content.startswith(b"%PDF"):
            return False

        return True

    except Exception as e:
        logger.debug(f"Failed to validate {url}: {e}")
        return False


def discover_all_reports() -> dict[str, dict]:
    """Discover all annual reports for FFC and EFERT.

    Returns: {
        "FFC": {
            2020: {"url": "...", "source": "psx", "validated": True},
            2021: {"url": "...", "source": "company_website", "validated": True},
            ...
        },
        "EFERT": {...},
    }
    """
    logger.info("=" * 70)
    logger.info("AUTOMATED ANNUAL REPORT DISCOVERY")
    logger.info("=" * 70)

    all_reports = {}

    for ticker in ["FFC", "EFERT"]:
        logger.info(f"\n{ticker}:")
        reports = {}

        # Try PSX first
        psx_reports = discover_psx_filings(ticker)
        for year, url in psx_reports.items():
            if is_valid_pdf(url):
                reports[year] = {"url": url, "source": "psx", "validated": True}
                logger.info(f"  ✓ FY{year}: PSX (validated)")
            else:
                logger.info(f"  ✗ FY{year}: PSX URL invalid, trying company website...")

        # Fall back to company website for missing years
        company = COMPANIES[ticker]
        for year in company["required_years"]:
            if year not in reports:
                company_reports = discover_company_website_reports(ticker)
                if year in company_reports:
                    url = company_reports[year]
                    if is_valid_pdf(url):
                        reports[year] = {"url": url, "source": "company_website", "validated": True}
                        logger.info(f"  ✓ FY{year}: Company website (validated)")
                    else:
                        reports[year] = {"url": url, "source": "company_website", "validated": False}
                        logger.info(f"  ✗ FY{year}: Company website URL invalid")
                else:
                    logger.info(f"  ✗ FY{year}: Not found")

        all_reports[ticker] = reports

    # Summary
    logger.info("\n" + "=" * 70)
    logger.info("DISCOVERY SUMMARY")
    logger.info("=" * 70)

    for ticker, reports in all_reports.items():
        company = COMPANIES[ticker]
        found = sum(1 for r in reports.values() if r.get("validated"))
        total = len(company["required_years"])
        logger.info(f"\n{ticker}: {found}/{total} validated reports found")

        for year in sorted(company["required_years"]):
            if year in reports:
                report = reports[year]
                status = "OK" if report.get("validated") else "INVALID"
                source = report.get("source", "unknown")
                logger.info(f"  FY{year}: [{status}] {source} - {report['url'][:50]}")
            else:
                logger.info(f"  FY{year}: [MISSING]")

    return all_reports


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    reports = discover_all_reports()

    # Pretty print results
    import json
    print("\n" + "=" * 70)
    print("DISCOVERY OUTPUT")
    print("=" * 70)
    for ticker, reports in reports.items():
        print(f"\n{ticker}:")
        for year in sorted(reports.keys()):
            report = reports[year]
            print(f"  {year}: {report}")
