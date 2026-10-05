#!/usr/bin/env python3
"""Test MetricExtractor on real annual reports from FFC and EFERT.

Downloads PDFs from official IR sites and logs extraction results.
"""

import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx
from app.ingestion.annual_report_extraction import MetricExtractor

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

REPORTS = {
    "FFC": [
        {"year": 2025, "url": "https://ffc.com.pk/wp-content/uploads/2026/03/FFC-AR-2025-2.pdf"},
        {"year": 2024, "url": "https://ffc.com.pk/wp-content/uploads/2025/03/FFC-AR-2024.pdf"},
        {"year": 2023, "url": "https://ffc.com.pk/wp-content/uploads/2024/11/FFC-Annual-Integrated-Report-2023_a.pdf"},
    ],
    "EFERT": [
        {"year": 2025, "url": "https://www.engrofertilizers.com/themes/engro/documents/Engro-Fertilizers-Annual-Report-2025.pdf"},
        {"year": 2024, "url": "https://www.engrofertilizers.com/themes/engro/documents/efert-annual-report-2024.pdf"},
        {"year": 2023, "url": "https://www.engrofertilizers.com/themes/engro/documents/EFERT_Annual_Report_2023_Final.pdf"},
    ]
}

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) psx-fertilizer/0.1"}
DOWNLOAD_DIR = Path(__file__).parent.parent / "test_fixtures" / "real_pdfs"

def download_pdf(ticker: str, year: int, url: str) -> Path:
    """Download PDF and save locally."""
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

    filename = f"{ticker}_AR_{year}.pdf"
    filepath = DOWNLOAD_DIR / filename

    if filepath.exists():
        logger.info(f"  {filename} already downloaded ({filepath.stat().st_size / 1024 / 1024:.1f}MB)")
        return filepath

    try:
        logger.info(f"  Downloading {filename}...")
        response = httpx.get(url, headers=HEADERS, timeout=30, follow_redirects=True)
        response.raise_for_status()

        filepath.write_bytes(response.content)
        size_mb = filepath.stat().st_size / 1024 / 1024
        logger.info(f"  ✓ Downloaded {filename} ({size_mb:.1f}MB)")
        return filepath
    except Exception as e:
        logger.error(f"  ✗ Failed to download {filename}: {e}")
        return None

def test_extractor_on_pdf(ticker: str, year: int, pdf_path: Path) -> dict:
    """Run MetricExtractor on PDF and return results."""
    logger.info(f"Testing {ticker} FY{year} ({pdf_path.name})...")

    try:
        extractor = MetricExtractor(pdf_path)
        metrics = extractor.extract()

        # Count successful extractions
        extracted_count = sum(1 for m in metrics.values() if m.get('value') is not None)
        total_metrics = len(metrics)

        result = {
            "ticker": ticker,
            "year": year,
            "pdf_path": str(pdf_path),
            "file_size_mb": pdf_path.stat().st_size / 1024 / 1024,
            "extraction_success": True,
            "metrics_extracted": extracted_count,
            "total_metrics": total_metrics,
            "extraction_pct": round(100 * extracted_count / total_metrics, 1) if total_metrics > 0 else 0,
            "metrics": metrics,
            "timestamp": datetime.now().isoformat(),
        }

        logger.info(f"  ✓ Extracted {extracted_count}/{total_metrics} metrics ({result['extraction_pct']}%)")
        return result
    except Exception as e:
        logger.error(f"  ✗ Extraction failed: {e}", exc_info=True)
        return {
            "ticker": ticker,
            "year": year,
            "pdf_path": str(pdf_path),
            "extraction_success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
        }

def main():
    logger.info("=" * 70)
    logger.info("REAL PDF EXTRACTION TEST")
    logger.info("=" * 70)

    all_results = {"ffc": {}, "efert": {}}

    for ticker, reports in REPORTS.items():
        logger.info(f"\n{ticker}:")
        ticker_lower = ticker.lower()

        for report in reports:
            year = report["year"]
            url = report["url"]

            # Download
            pdf_path = download_pdf(ticker, year, url)
            if not pdf_path:
                continue

            # Extract
            result = test_extractor_on_pdf(ticker, year, pdf_path)
            all_results[ticker_lower][year] = result

    # Save results
    results_file = DOWNLOAD_DIR / "extraction_results.json"
    with open(results_file, "w") as f:
        json.dump(all_results, f, indent=2, default=str)

    logger.info(f"\n✓ Results saved to {results_file}")

    # Summary
    logger.info("\n" + "=" * 70)
    logger.info("SUMMARY")
    logger.info("=" * 70)

    for ticker_lower, years_data in all_results.items():
        logger.info(f"\n{ticker_lower.upper()}:")
        for year, result in sorted(years_data.items()):
            if result.get("extraction_success"):
                pct = result.get("extraction_pct", 0)
                logger.info(f"  FY{year}: {result['metrics_extracted']}/{result['total_metrics']} metrics ({pct}%)")
            else:
                logger.info(f"  FY{year}: FAILED - {result.get('error', 'Unknown error')}")

if __name__ == "__main__":
    main()
