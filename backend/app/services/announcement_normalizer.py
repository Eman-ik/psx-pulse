"""Announcement Normalizer — Parse and normalize PSX announcements.

Processes announcements from PSX to extract:
- Event type (earnings, dividend, M&A, regulatory, etc.)
- Sentiment (positive, negative, neutral)
- Materiality (major, moderate, minor)
- Key facts and figures

Input: Raw announcement data from MarketDataService or database
Output: Normalized RecentEvent objects for StockSnapshot
"""

import logging
import re
from datetime import datetime, date
from typing import Optional, List, Tuple

from app.schemas.stock_snapshot import RecentEvent

logger = logging.getLogger(__name__)


class AnnouncementNormalizer:
    """Normalize PSX announcements into structured events."""

    # Announcement category keywords
    CATEGORY_KEYWORDS = {
        "earnings": [
            "earnings", "profit", "pat", "revenue", "fy", "quarterly", "q1", "q2", "q3", "q4",
            "annual results", "financial results", "performance"
        ],
        "dividend": [
            "dividend", "distribution", "payout", "dps", "yield", "cash dividend", "bonus"
        ],
        "acquisition": [
            "acquisition", "acquire", "purchase", "buy", "stake", "investment", "merge", "merger"
        ],
        "corporate_action": [
            "stock split", "bonus", "rights", "warrant", "conversion", "corporate action", "ipo"
        ],
        "regulatory": [
            "regulatory", "secp", "compliance", "license", "approval", "regulatory approval",
            "investigation", "fine", "penalty", "audit"
        ],
        "material_contract": [
            "contract", "agreement", "tender", "order", "supply", "export", "deal", "partnership"
        ],
        "asset_disposal": [
            "sale", "disposal", "divest", "close", "shutdown", "write-off", "impairment"
        ],
        "leadership": [
            "ceo", "cfo", "director", "chairman", "appointment", "resignation", "retirement",
            "management change", "board"
        ],
        "litigation": [
            "lawsuit", "litigation", "dispute", "legal", "court", "judgment", "settlement"
        ],
    }

    # Sentiment indicators
    POSITIVE_KEYWORDS = [
        "strong", "improved", "growth", "increase", "exceed", "beat", "positive",
        "successful", "approval", "record", "expansion", "new", "expansion", "recover"
    ]

    NEGATIVE_KEYWORDS = [
        "decline", "decrease", "loss", "weak", "miss", "negative", "delay",
        "challenge", "risk", "uncertain", "investigation", "fine", "penalty", "restructuring"
    ]

    def __init__(self):
        """Initialize announcement normalizer."""
        self.logger = logging.getLogger(__name__)

    def normalize_batch(self, ticker: str, announcements: List[dict]) -> List[RecentEvent]:
        """Normalize a batch of announcements.

        Args:
            ticker: Stock ticker for context
            announcements: List of raw announcement dicts from MarketDataService

        Returns:
            List of normalized RecentEvent objects
        """
        if not announcements:
            return []

        events = []
        for ann in announcements:
            try:
                event = self.normalize_single(ticker, ann)
                if event:
                    events.append(event)
            except Exception as e:
                self.logger.warning(f"Error normalizing announcement for {ticker}: {e}")
                continue

        return events

    def normalize_single(self, ticker: str, announcement: dict) -> Optional[RecentEvent]:
        """Normalize a single announcement.

        Args:
            ticker: Stock ticker
            announcement: Raw announcement dict with keys: date, title, body, source

        Returns:
            Normalized RecentEvent or None if invalid
        """
        try:
            # Extract fields
            ann_date = announcement.get("date")
            title = announcement.get("title", "").strip()
            body = announcement.get("body", "").strip()
            source = announcement.get("source", "PSX")

            if not title:
                return None

            # Parse date
            if isinstance(ann_date, str):
                try:
                    ann_date = datetime.fromisoformat(ann_date).date()
                except (ValueError, TypeError):
                    ann_date = date.today()
            elif not isinstance(ann_date, date):
                ann_date = date.today()

            # Combine text for analysis
            full_text = f"{title} {body}".lower()

            # Categorize
            category = self._categorize(full_text)

            # Assess sentiment
            sentiment = self._assess_sentiment(full_text)

            # Assess materiality
            materiality = self._assess_materiality(full_text, category)

            # Build event body with metadata
            event_body = self._build_event_body(title, body, category, sentiment, materiality)

            event = RecentEvent(
                date=ann_date,
                title=title,
                body=event_body,
                source=source,
            )

            self.logger.debug(
                f"{ticker}: {title[:50]}... "
                f"[{category}, {sentiment}, {materiality}]"
            )
            return event

        except Exception as e:
            self.logger.error(f"Error normalizing announcement: {e}")
            return None

    def _categorize(self, text: str) -> str:
        """Categorize announcement by type.

        Args:
            text: Announcement text (lowercased)

        Returns:
            Category string
        """
        for category, keywords in self.CATEGORY_KEYWORDS.items():
            if any(kw in text for kw in keywords):
                return category

        return "other"

    def _assess_sentiment(self, text: str) -> str:
        """Assess sentiment of announcement.

        Args:
            text: Announcement text (lowercased)

        Returns:
            "positive", "negative", or "neutral"
        """
        positive_count = sum(1 for kw in self.POSITIVE_KEYWORDS if kw in text)
        negative_count = sum(1 for kw in self.NEGATIVE_KEYWORDS if kw in text)

        if positive_count > negative_count:
            return "positive"
        elif negative_count > positive_count:
            return "negative"
        else:
            return "neutral"

    def _assess_materiality(self, text: str, category: str) -> str:
        """Assess materiality of announcement.

        Args:
            text: Announcement text
            category: Announcement category

        Returns:
            "major", "moderate", or "minor"
        """
        # Major categories are inherently material
        major_categories = ["acquisition", "regulatory", "earnings", "dividend"]
        if category in major_categories:
            # Check for magnitude indicators
            if any(word in text for word in ["record", "exceed", "beat", "strong"]):
                return "major"
            return "moderate"

        # Check for percentage/amount indicators
        if re.search(r"(\d{1,3})%", text):  # Contains percentage
            match = re.search(r"(\d{1,3})%", text)
            if match:
                pct = int(match.group(1))
                if pct > 20:
                    return "major"
                elif pct > 5:
                    return "moderate"

        # Check for large numbers
        if re.search(r"\d{2,}\.?\d*\s*(billion|billion|thousand|crore|lakh)", text):
            return "major"

        if re.search(r"\d{1,}\s*(million|million)", text):
            return "moderate"

        return "minor"

    @staticmethod
    def _build_event_body(
        title: str,
        body: Optional[str],
        category: str,
        sentiment: str,
        materiality: str
    ) -> str:
        """Build normalized event body with metadata.

        Args:
            title: Announcement title
            body: Announcement body
            category: Event category
            sentiment: Event sentiment
            materiality: Event materiality

        Returns:
            Formatted event body
        """
        parts = [
            f"[{category.upper()} | {sentiment.upper()} | {materiality.upper()}]",
            "",
            title,
        ]

        if body:
            parts.extend(["", body[:500]])  # Truncate to 500 chars

        return "\n".join(parts)

    @staticmethod
    def extract_numbers(text: str) -> List[float]:
        """Extract all numerical values from text.

        Args:
            text: Text to extract from

        Returns:
            List of numbers found
        """
        pattern = r"[\d,]+\.?\d*"
        matches = re.findall(pattern, text)
        numbers = []
        for match in matches:
            try:
                num = float(match.replace(",", ""))
                numbers.append(num)
            except ValueError:
                continue
        return numbers

    @staticmethod
    def extract_date_mentions(text: str) -> List[str]:
        """Extract date mentions from text.

        Args:
            text: Text to extract from

        Returns:
            List of date strings found
        """
        patterns = [
            r"\d{1,2}[/-]\d{1,2}[/-]\d{2,4}",  # DD/MM/YYYY or similar
            r"(january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2}",
            r"(q1|q2|q3|q4)\s+\d{4}",
            r"fy\d{2,4}",
        ]

        dates = []
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            dates.extend(matches)

        return dates

    def is_material_event(self, announcement: dict, materiality_threshold: str = "moderate") -> bool:
        """Check if announcement meets materiality threshold.

        Args:
            announcement: Raw announcement dict
            materiality_threshold: Minimum materiality ("major", "moderate", "minor")

        Returns:
            True if announcement meets threshold
        """
        title = announcement.get("title", "").lower()
        body = announcement.get("body", "").lower()
        full_text = f"{title} {body}".lower()

        category = self._categorize(full_text)
        materiality = self._assess_materiality(full_text, category)

        # Map materiality to numeric scale
        scales = {"major": 3, "moderate": 2, "minor": 1}
        threshold_scale = scales.get(materiality_threshold, 2)
        actual_scale = scales.get(materiality, 1)

        return actual_scale >= threshold_scale
