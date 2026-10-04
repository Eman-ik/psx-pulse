"""PSX report discovery using browser automation.

Discovers annual report PDFs from PSX company pages by:
1. Loading page with Playwright (handles JavaScript)
2. Extracting document links from rendered DOM
3. Deriving direct PSX document URLs
4. Validating each PDF

PSX document URL pattern: https://dps.psx.com.pk/download/document/{id}.pdf
"""

import logging
import re
from typing import Optional
import httpx

logger = logging.getLogger(__name__)

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) psx-research/1.0"}


def discover_psx_reports_with_browser(ticker: str, years: list[int]) -> dict[int, dict]:
    """Discover PSX annual reports using browser automation.

    Requires Playwright. Install with: pip install playwright
    Then: playwright install chromium

    Returns: {
        2024: {
            "url": "https://dps.psx.com.pk/download/document/...",
            "document_id": "...",
            "title": "Annual Report FY2024",
            "validated": True,
        },
        ...
    }
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        logger.error(
            "Playwright not installed. Install with: pip install playwright\n"
            "Then run: playwright install chromium"
        )
        return {}

    logger.info(f"Discovering PSX reports for {ticker} using browser automation")

    company_url = f"https://dps.psx.com.pk/company/{ticker}"
    found_reports = {}

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            logger.info(f"Loading {company_url}")
            page.goto(company_url, wait_until="domcontentloaded")

            # Wait for announcements section to load
            try:
                page.wait_for_selector("#announcements table", timeout=5000)
                logger.info("Announcements section loaded")
            except:
                logger.warning("Announcements section not found or timed out")
                browser.close()
                return {}

            # Get the HTML content after JavaScript rendering
            content = page.content()

            # Extract all document links from the announcements table
            # Look for patterns in table rows
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(content, "lxml")

            announcements = soup.find("div", id="announcements")
            if not announcements:
                logger.warning("No announcements section found")
                browser.close()
                return {}

            # Look for annual reports in the table
            tables = announcements.find_all("table")
            logger.info(f"Found {len(tables)} tables in announcements")

            for table in tables:
                rows = table.find_all("tr")

                for row in rows:
                    cells = row.find_all(["td", "th"])
                    if len(cells) < 3:
                        continue

                    # Extract date, title, document link
                    title_cell = cells[1] if len(cells) > 1 else None
                    link_cell = cells[-1] if cells else None

                    if not title_cell or not link_cell:
                        continue

                    title_text = title_cell.get_text(strip=True).lower()

                    # Look for annual report indicators
                    if not any(x in title_text for x in ["annual", "report", "ar"]):
                        continue

                    # Extract year
                    year_match = re.search(r"(20\d{2})", title_text)
                    if not year_match:
                        continue

                    year = int(year_match.group(1))
                    if year not in years:
                        continue

                    # Look for document link
                    # First check for href with document ID
                    for link in link_cell.find_all("a", href=True):
                        href = link.get("href", "")

                        # Look for document ID patterns
                        # PSX: /download/document/{id}.pdf or onclick handlers
                        doc_id_match = re.search(r"document[/=](\d+)", href)

                        if doc_id_match:
                            doc_id = doc_id_match.group(1)
                            url = f"https://dps.psx.com.pk/download/document/{doc_id}.pdf"

                            logger.info(f"  FY{year}: Found document {doc_id}")

                            # Validate the PDF
                            if is_valid_pdf(url):
                                found_reports[year] = {
                                    "url": url,
                                    "document_id": doc_id,
                                    "title": link.get_text(strip=True),
                                    "validated": True,
                                }
                                logger.info(f"    ✓ Validated: {url[:60]}")
                            else:
                                logger.warning(f"    ✗ Invalid PDF: {url[:60]}")
                                found_reports[year] = {
                                    "url": url,
                                    "document_id": doc_id,
                                    "title": link.get_text(strip=True),
                                    "validated": False,
                                }

            browser.close()

    except Exception as e:
        logger.error(f"Browser discovery failed: {e}", exc_info=True)
        return {}

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
        response = httpx.head(url, headers=HEADERS, timeout=timeout, follow_redirects=True)

        if response.status_code != 200:
            logger.debug(f"PDF validation failed for {url}: HTTP {response.status_code}")
            return False

        content_type = response.headers.get("content-type", "").lower()
        if "pdf" not in content_type:
            logger.debug(f"PDF validation failed for {url}: wrong content-type {content_type}")
            return False

        content_length = response.headers.get("content-length")
        if content_length:
            size = int(content_length)
            if size < 100_000:
                logger.debug(f"PDF validation failed for {url}: too small ({size} bytes)")
                return False

        # Check PDF magic bytes
        response = httpx.get(url, headers=HEADERS, timeout=timeout, follow_redirects=True)
        if response.status_code != 200:
            return False

        if not response.content.startswith(b"%PDF"):
            logger.debug(f"PDF validation failed for {url}: no PDF magic bytes")
            return False

        return True

    except Exception as e:
        logger.debug(f"PDF validation exception for {url}: {e}")
        return False


def discover_all_psx_reports() -> dict[str, dict[int, dict]]:
    """Discover all annual reports for FFC and EFERT from PSX.

    Returns: {
        "FFC": {
            2020: {"url": "...", "validated": True},
            ...
        },
        "EFERT": {...}
    }
    """
    logger.info("=" * 70)
    logger.info("PSX BROWSER-BASED REPORT DISCOVERY")
    logger.info("=" * 70)

    results = {
        "FFC": discover_psx_reports_with_browser("FFC", [2020, 2021, 2022, 2023, 2024, 2025]),
        "EFERT": discover_psx_reports_with_browser("EFERT", [2023, 2024, 2025]),
    }

    # Summary
    logger.info("\n" + "=" * 70)
    logger.info("DISCOVERY SUMMARY")
    logger.info("=" * 70)

    for ticker, reports in results.items():
        validated = sum(1 for r in reports.values() if r.get("validated"))
        total = len(reports)
        logger.info(f"\n{ticker}: {validated}/{total} validated reports")

        for year in sorted(reports.keys()):
            report = reports[year]
            status = "OK" if report.get("validated") else "INVALID"
            logger.info(f"  FY{year}: [{status}] {report['url'][:60]}")

    return results


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Check if Playwright is available
    try:
        import playwright
        logger.info("Playwright found")
    except ImportError:
        logger.error("\nPlaywright not installed!")
        logger.error("Install with: pip install playwright")
        logger.error("Then run: playwright install chromium")
        import sys
        sys.exit(1)

    results = discover_all_psx_reports()

    print("\n" + "=" * 70)
    print("DISCOVERY RESULTS")
    print("=" * 70)

    import json
    for ticker, reports in results.items():
        print(f"\n{ticker}:")
        for year in sorted(reports.keys()):
            report = reports[year]
            print(f"  {year}: {json.dumps(report)}")
