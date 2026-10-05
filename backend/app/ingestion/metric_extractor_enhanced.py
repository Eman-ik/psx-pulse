"""Enhanced MetricExtractor with statement-aware fallbacks.

Adds detection + fallback strategies for:
1. Statement type (table vs narrative vs scanned)
2. Narrative metric extraction (prose-embedded values)
3. Derived metrics (DPS = interim + final, etc)
4. Extraction quality flags

Maintains backward compatibility: falls back to original line-by-line
extraction when statement-aware methods don't find values.
"""

import re
import logging
from typing import Optional
from decimal import Decimal

logger = logging.getLogger(__name__)


class StatementDetector:
    """Detect statement type and format from extracted PDF text."""

    @staticmethod
    def detect_statement_type(page_text: str) -> str:
        """Return statement type: 'income_statement', 'balance_sheet', 'cash_flow', 'narrative', 'unknown'."""
        text_upper = page_text.upper()

        # Income statement keywords
        if any(x in text_upper for x in [
            "STATEMENT OF PROFIT AND LOSS",
            "INCOME STATEMENT",
            "PROFIT & LOSS",
            "P&L",
            "CONSOLIDATED PROFIT AND LOSS",
            "STATEMENT OF PROFIT",
        ]):
            return "income_statement"

        # Balance sheet keywords
        if any(x in text_upper for x in [
            "BALANCE SHEET",
            "STATEMENT OF FINANCIAL POSITION",
            "STATEMENT OF POSITION",
            "ASSETS AND LIABILITIES",
        ]):
            return "balance_sheet"

        # Cash flow keywords
        if any(x in text_upper for x in [
            "CASH FLOW",
            "STATEMENT OF CASH FLOWS",
        ]):
            return "cash_flow"

        # Narrative detection: has narrative structure (prose-like text with narrative keywords)
        page_lower = page_text.lower()
        narrative_keywords = [
            " reached ", " improved ", " increased ", " declined ",
            " profit of ", " revenue of ", " costs of ",
            " driven by ", " due to ", " resulted in ",
            "company achieved", "company's total", "compared to",
        ]
        has_narrative_words = sum(1 for kw in narrative_keywords if kw in page_lower)

        # If has enough narrative keywords, likely narrative
        if has_narrative_words >= 3:
            return "narrative"

        lowercase_ratio = sum(1 for c in page_text if c.islower()) / max(len(page_text), 1)
        if lowercase_ratio > 0.65 and has_narrative_words >= 1:
            return "narrative"

        return "unknown"

    @staticmethod
    def detect_scanned_pdf(pages_text: list[tuple[int, str]]) -> bool:
        """Return True if PDF appears to be scanned (image-based, little/no extractable text)."""

        # Check first 3 pages
        for page_num, text in pages_text[:3]:
            # Scanned PDFs extract very little meaningful text
            if len(text.strip()) < 100:
                continue

            # Check if text looks like OCR junk (lots of single chars, no words)
            words = text.split()
            if len(words) < 20:  # Too few words for a real page
                continue

            return False

        # All checked pages had < 100 chars or < 20 words
        return True


class NarrativeMetricExtractor:
    """Extract metrics from prose/narrative text in reports."""

    @staticmethod
    def extract_metric_from_narrative(text: str, metric_name: str) -> Optional[float]:
        """Extract metric from narrative prose.

        Examples:
        - "Operating profit reached PKR 450 million"
        - "Other income of PKR 12.5 million"
        - "Tax expense was 38,900 thousand rupees"

        Returns value in thousands (matching table-based extraction unit).
        """

        if metric_name == "operating_profit":
            return NarrativeMetricExtractor._extract_operating_profit(text)
        elif metric_name == "other_income":
            return NarrativeMetricExtractor._extract_other_income(text)
        elif metric_name == "tax_expense":
            return NarrativeMetricExtractor._extract_tax_expense(text)
        elif metric_name == "dividend_per_share":
            return NarrativeMetricExtractor._extract_dps(text)
        elif metric_name == "revenue":
            return NarrativeMetricExtractor._extract_revenue(text)

        return None

    @staticmethod
    def _extract_operating_profit(text: str) -> Optional[float]:
        """Extract operating profit from narrative."""
        # Patterns handle various narrative styles:
        # - "Operating profit improved to PKR 450 million"
        # - "EBIT reached 450 million"
        # - "Operating Profit 450"
        patterns = [
            r"operating profit\s+(?:improved\s+to|reached|was|of|to)?\s+(?:pkr\s+)?(\d+(?:,\d{3})*(?:\.\d+)?)\s+(million|thousand|lakh|billion)",
            r"\bebit\s+(?:improved\s+to|reached|was|of|to)?\s+(?:pkr\s+)?(\d+(?:,\d{3})*(?:\.\d+)?)\s+(million|thousand|lakh)",
            r"earnings\s+before\s+interest\s+(?:and\s+)?tax.*?(\d+(?:,\d{3})*(?:\.\d+)?)\s+(million|thousand)",
        ]

        return NarrativeMetricExtractor._apply_patterns(text, patterns)

    @staticmethod
    def _extract_other_income(text: str) -> Optional[float]:
        """Extract other income from narrative."""
        patterns = [
            r"(?:other income|other operating income|miscellaneous income)\s+(?:of|was|reached|to)?\s+(?:pkr\s+)?(\d+(?:,\d{3})*(?:\.\d+)?)\s+(million|thousand|lakh)",
            r"other operating income\s+(?:pkr\s+)?(\d+(?:,\d{3})*(?:\.\d+)?)",
        ]

        return NarrativeMetricExtractor._apply_patterns(text, patterns)

    @staticmethod
    def _extract_tax_expense(text: str) -> Optional[float]:
        """Extract tax expense from narrative."""
        patterns = [
            r"(?:tax expense|taxation|income tax|tax expenses)\s+(?:of|was|reached|to)?\s+(?:pkr\s+)?(\d+(?:,\d{3})*(?:\.\d+)?)\s+(million|thousand|lakh)",
            r"tax(?:ation)?\s+(?:charge|expense|expenses)\s+of\s+(?:pkr\s+)?(\d+(?:,\d{3})*(?:\.\d+)?)",
        ]

        return NarrativeMetricExtractor._apply_patterns(text, patterns)

    @staticmethod
    def _extract_revenue(text: str) -> Optional[float]:
        """Extract revenue from narrative."""
        patterns = [
            r"(?:revenue|sales)\s+(?:reached|was|of)?\s+(?:pkr\s+)?(\d+(?:,\d{3})*(?:\.\d+)?)\s+(million|thousand|lakh|billion)",
            r"total revenue\s+(?:pkr\s+)?(\d+(?:,\d{3})*(?:\.\d+)?)",
        ]

        return NarrativeMetricExtractor._apply_patterns(text, patterns)

    @staticmethod
    def _extract_dps(text: str) -> Optional[float]:
        """Extract dividend per share from narrative.

        Handles: "1.50 per share" or "1.50 + 1.00 = 2.50" (interim + final).
        """
        # Try explicit final DPS
        patterns = [
            r"dividend per share.*?(\d+\.\d+)",
            r"dps.*?(\d+\.\d+)",
            r"final dividend.*?(?:pkr\s+)?(\d+\.\d+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                return float(match.group(1))

        # Try interim + final pattern: "1.50 + 1.00 = 2.50" or "interim 1.50, final 1.00"
        derived = NarrativeMetricExtractor._extract_derived_dps(text)
        if derived:
            return derived

        return None

    @staticmethod
    def _extract_derived_dps(text: str) -> Optional[float]:
        """Extract DPS from interim + final pattern."""
        # Pattern 1: "interim 1.50, final 1.00" or "interim 1.50 and final 1.00"
        interim_match = re.search(r"interim\s+(?:dividend\s+)?(?:pkr\s+)?(\d+\.\d+)", text, re.IGNORECASE)
        final_match = re.search(r"final\s+(?:dividend\s+)?(?:pkr\s+)?(\d+\.\d+)", text, re.IGNORECASE)

        if interim_match and final_match:
            interim = float(interim_match.group(1))
            final = float(final_match.group(1))
            return interim + final

        # Pattern 2: "1.50 + 1.00 = 2.50"
        match = re.search(r"(\d+\.\d+)\s*\+\s*(\d+\.\d+)(?:\s*=\s*(\d+\.\d+))?", text)
        if match:
            interim = float(match.group(1))
            final = float(match.group(2))
            stated = float(match.group(3)) if match.lastindex >= 3 else None

            # Prefer stated if available
            return stated or (interim + final)

        return None

    @staticmethod
    def _apply_patterns(text: str, patterns: list[str]) -> Optional[float]:
        """Apply regex patterns to extract and scale a numeric value."""

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                num_str = match.group(1).replace(",", "")
                num = float(num_str)

                # Scale to thousands (standard unit)
                unit = match.group(2) if match.lastindex >= 2 else None
                if unit:
                    multiplier = {
                        "thousand": 1,
                        "lakh": 100,
                        "million": 1000,
                        "billion": 1000000,
                    }.get(unit.lower(), 1)
                    num *= multiplier

                logger.info(f"  Narrative extraction: {pattern[:50]}... → {num:,.0f}")
                return num

        return None


class DerivedMetricCalculator:
    """Calculate metrics that require combining multiple line items."""

    @staticmethod
    def calculate_ebitda(operating_profit: Optional[float], depreciation: Optional[float],
                        amortization: Optional[float]) -> Optional[float]:
        """Calculate EBITDA = Operating Profit + Depreciation + Amortization."""

        if operating_profit is None:
            return None

        # If depreciation/amortization not found, can't calculate
        if depreciation is None or amortization is None:
            return None

        return operating_profit + depreciation + amortization

    @staticmethod
    def extract_derived_metric_from_line(line: str, metric_name: str) -> Optional[float]:
        """Detect derived metrics in a single line.

        Examples:
        - "Total Dividend = 1.50 + 1.00 = 2.50"
        - "EBITDA (OP + D&A) 450,000"
        """

        if metric_name == "dividend_per_share":
            # Pattern: "1.50 + 1.00 = 2.50"
            match = re.search(r"(\d+\.\d+)\s*\+\s*(\d+\.\d+)(?:\s*=\s*(\d+\.\d+))?", line)
            if match:
                if match.lastindex >= 3:
                    return float(match.group(3))
                else:
                    a = float(match.group(1))
                    b = float(match.group(2))
                    return a + b

        return None


class EnhancedMetricExtractor:
    """Wrapper around original extractor with statement-aware fallbacks."""

    def __init__(self, original_extraction_func):
        """Store reference to original extractor's _extract_number_from_line method."""
        self.original_extract = original_extraction_func

    def extract_with_fallbacks(self, pages_text: list[tuple[int, str]],
                               metric_key: str, aliases: list[str]) -> Optional[dict]:
        """Extract metric with fallback chain:

        1. Try original line-by-line extraction (fast, works for tables)
        2. Detect statement type
        3. If narrative, use narrative extractor
        4. If scanned, flag for manual review
        5. Return metadata about extraction method
        """

        # Step 1: Original extraction
        for page_num, text in pages_text:
            for alias in aliases:
                for line in text.split("\n"):
                    if alias.lower() in line.lower():
                        value = self.original_extract(line)
                        if value is not None:
                            return {
                                "value": value,
                                "page": page_num,
                                "raw_line": line.strip(),
                                "alias_found": alias,
                                "extraction_method": "table",
                                "confidence": "high",
                            }

        # Step 2: Detect statement type
        detector = StatementDetector()
        statement_types = [detector.detect_statement_type(text) for _, text in pages_text]

        logger.info(f"  Statement types detected: {set(statement_types)}")

        # Step 3: Try narrative extraction if narrative detected
        if "narrative" in statement_types:
            logger.info(f"  Attempting narrative extraction for {metric_key}...")
            for page_num, text in pages_text:
                if detector.detect_statement_type(text) == "narrative":
                    value = NarrativeMetricExtractor.extract_metric_from_narrative(text, metric_key)
                    if value is not None:
                        return {
                            "value": value,
                            "page": page_num,
                            "extraction_method": "narrative",
                            "confidence": "medium",
                        }

        # Step 4: Check if scanned
        if detector.detect_scanned_pdf(pages_text):
            logger.warning(f"  PDF appears to be scanned (image-based); cannot extract {metric_key}")
            return {
                "value": None,
                "extraction_method": "scanned_pdf",
                "confidence": "none",
                "flag": "requires_ocr",
            }

        # Step 5: Not found
        return None


# Backward-compatible wrapper for original MetricExtractor
def enhance_metric_extractor(original_extractor_class):
    """Monkey-patch original MetricExtractor with fallback-aware extraction.

    Usage:
        from app.ingestion.annual_report_extraction import MetricExtractor
        MetricExtractor = enhance_metric_extractor(MetricExtractor)
    """

    original_extract_metrics = original_extractor_class.extract_metrics_from_pdf

    def new_extract_metrics_from_pdf(self, url: str, fiscal_year: int) -> dict:
        """Enhanced extraction with fallbacks."""

        import io
        import hashlib
        import httpx
        import pdfplumber

        HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) psx-fertilizer-research-pilot/0.1"}

        logger.info(f"Downloading {url}")

        try:
            response = httpx.get(url, headers=HEADERS, timeout=180)
            response.raise_for_status()
        except Exception as e:
            logger.error(f"Failed to download {url}: {e}")
            return {}

        pdf_content = response.content
        pdf_hash = hashlib.sha256(pdf_content).hexdigest()

        extracted = {}

        try:
            with pdfplumber.open(io.BytesIO(pdf_content)) as pdf:
                # Extract text from all pages
                pages_text = [
                    (i, page.extract_text() or "")
                    for i, page in enumerate(pdf.pages, start=1)
                ]

                # Check for scanned PDF early
                detector = StatementDetector()
                if detector.detect_scanned_pdf(pages_text):
                    logger.warning("PDF appears to be scanned; flagging for manual review")
                    return {"_metadata": {"scanned_pdf": True, "requires_ocr": True}}

                # Search for income statement
                income_statement_pages = [
                    (i, text)
                    for i, text in pages_text
                    if detector.detect_statement_type(text) in ["income_statement", "narrative"]
                ]

                if not income_statement_pages:
                    logger.warning(f"No income statement found in {url}")
                    return {}

                # Enhanced metric extraction with fallbacks
                enhancer = EnhancedMetricExtractor(self._extract_number_from_line)

                for metric_key, aliases in [
                    ("operating_profit", self.__class__.CANONICAL_METRICS["operating_profit"]["aliases"]),
                    ("other_income", self.__class__.CANONICAL_METRICS["other_income"]["aliases"]),
                    ("tax_expense", self.__class__.CANONICAL_METRICS["tax_expense"]["aliases"]),
                ]:
                    result = enhancer.extract_with_fallbacks(income_statement_pages, metric_key, aliases)
                    if result:
                        extracted[metric_key] = result

                # DPS extraction (searches all pages, may use narrative)
                for page_num, text in pages_text:
                    for alias in self.__class__.CANONICAL_METRICS["dividend_per_share"]["aliases"]:
                        if alias.lower() in text.lower():
                            # Try derived calculation first
                            derived = DerivedMetricCalculator.extract_derived_metric_from_line(text, "dividend_per_share")
                            if derived and "dividend_per_share" not in extracted:
                                extracted["dividend_per_share"] = {
                                    "value": derived,
                                    "page": page_num,
                                    "extraction_method": "derived",
                                    "confidence": "high",
                                }
                                logger.info(f"  dividend_per_share (derived) = {derived}")
                                break

                            # Fallback to narrative
                            value = NarrativeMetricExtractor.extract_metric_from_narrative(text, "dividend_per_share")
                            if value and "dividend_per_share" not in extracted:
                                extracted["dividend_per_share"] = {
                                    "value": value,
                                    "page": page_num,
                                    "extraction_method": "narrative",
                                    "confidence": "medium",
                                }
                                logger.info(f"  dividend_per_share (narrative) = {value}")

        except Exception as e:
            logger.error(f"Failed to parse PDF {url}: {e}")

        return extracted

    original_extractor_class.extract_metrics_from_pdf = new_extract_metrics_from_pdf
    return original_extractor_class
