"""Step 15: Event Extractor — Extract detailed events from announcements.

Analyzes announcement text to extract:
- Event type (earnings, dividend, M&A, etc.)
- Key financial figures (amounts, percentages)
- Dates and timelines
- Named entities (people, companies, regulatory bodies)
- Impact assessment (who benefits/loses)
- Conditional statements (approvals pending, subject to, etc.)

Input: Announcement text
Output: DetailedEvent (structured event data)
"""

import logging
import re
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from enum import Enum

logger = logging.getLogger(__name__)


class EventImpact(str, Enum):
    """Impact of event."""

    POSITIVE = "Positive"
    NEGATIVE = "Negative"
    NEUTRAL = "Neutral"
    MIXED = "Mixed"
    UNKNOWN = "Unknown"


class ConditionalStatus(str, Enum):
    """Whether event is conditional."""

    UNCONDITIONAL = "Unconditional"
    CONDITIONAL = "Conditional"
    COMPLETED = "Completed"
    PENDING = "Pending"
    WITHDRAWN = "Withdrawn"


@dataclass
class ExtractedFigure:
    """Financial figure from event."""

    figure_type: str  # "Dividend", "Price", "Amount", "Percentage"
    value: float
    unit: str  # "PKR", "%", "Shares"
    context: str  # "per share", "total", etc.


@dataclass
class KeyEntity:
    """Named entity from event."""

    entity_type: str  # "Person", "Company", "Regulator"
    name: str
    role: Optional[str]  # "CEO", "Acquirer", "Regulatory Body"


@dataclass
class DetailedEvent:
    """Complete extracted event data."""

    announcement_date: str
    event_type: str  # From AnnouncementNormalizer categories
    event_title: str
    event_body: str

    # Key information
    impact: EventImpact
    conditional_status: ConditionalStatus
    probability_of_occurrence: float  # 0-100% for conditional events

    # Extracted data
    financial_figures: List[ExtractedFigure]
    key_entities: List[KeyEntity]
    implementation_date: Optional[str]
    timeline: Optional[str]  # "Q4 2024", "6 months", etc.

    # Text analysis
    sentiment_keywords: List[str]
    risk_factors: List[str]
    opportunities: List[str]

    # Event context
    related_announcements: List[str]  # References to prior/related events
    regulatory_approvals_needed: List[str]
    conditions_to_meet: List[str]

    # Data quality
    extraction_confidence: float  # 0-100%
    requires_followup: bool  # True if more info needed

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "announcement_date": self.announcement_date,
            "event_type": self.event_type,
            "event_title": self.event_title,
            "impact": self.impact.value,
            "conditional_status": self.conditional_status.value,
            "probability_of_occurrence": self.probability_of_occurrence,
            "financial_figures_count": len(self.financial_figures),
            "key_entities_count": len(self.key_entities),
            "implementation_date": self.implementation_date,
            "timeline": self.timeline,
            "risk_factors": self.risk_factors,
            "opportunities": self.opportunities,
            "regulatory_approvals_needed": self.regulatory_approvals_needed,
            "extraction_confidence": round(self.extraction_confidence, 1),
            "requires_followup": self.requires_followup,
        }


class EventExtractor:
    """Extracts detailed information from announcements."""

    def __init__(self):
        """Initialize event extractor."""
        self.logger = logging.getLogger(__name__)

    def extract_event(self, announcement_text: str, announcement_date: str) -> Optional[DetailedEvent]:
        """Extract detailed event from announcement.

        Args:
            announcement_text: Full announcement text
            announcement_date: Date of announcement

        Returns:
            DetailedEvent or None on error
        """
        try:
            # Extract basic info
            event_type = self._extract_event_type(announcement_text)
            event_title = self._extract_event_title(announcement_text)
            impact = self._assess_impact(announcement_text)

            # Extract financial figures
            figures = self._extract_financial_figures(announcement_text)

            # Extract entities
            entities = self._extract_key_entities(announcement_text)

            # Extract dates and timelines
            impl_date = self._extract_implementation_date(announcement_text)
            timeline = self._extract_timeline(announcement_text)

            # Extract conditional information
            conditional = self._extract_conditional_status(announcement_text)
            probability = self._extract_probability(announcement_text, conditional)

            # Extract text analysis
            sentiment_kws = self._extract_sentiment_keywords(announcement_text)
            risks = self._extract_risk_factors(announcement_text)
            opportunities = self._extract_opportunities(announcement_text)

            # Extract context
            related = self._extract_related_announcements(announcement_text)
            regulators = self._extract_regulatory_approvals(announcement_text)
            conditions = self._extract_conditions(announcement_text)

            # Calculate confidence
            confidence = self._calculate_extraction_confidence(
                announcement_text, figures, entities
            )
            followup = conditional == ConditionalStatus.CONDITIONAL or confidence < 70

            event = DetailedEvent(
                announcement_date=announcement_date,
                event_type=event_type,
                event_title=event_title,
                event_body=announcement_text[:500],  # First 500 chars
                impact=impact,
                conditional_status=conditional,
                probability_of_occurrence=probability,
                financial_figures=figures,
                key_entities=entities,
                implementation_date=impl_date,
                timeline=timeline,
                sentiment_keywords=sentiment_kws,
                risk_factors=risks,
                opportunities=opportunities,
                related_announcements=related,
                regulatory_approvals_needed=regulators,
                conditions_to_meet=conditions,
                extraction_confidence=confidence,
                requires_followup=followup,
            )

            self.logger.info(
                f"Extracted event: {event_type} ({impact.value}), "
                f"confidence {confidence:.0f}%"
            )
            return event

        except Exception as e:
            self.logger.error(f"Error extracting event: {e}")
            return None

    @staticmethod
    def _extract_event_type(text: str) -> str:
        """Extract event type."""
        text_lower = text.lower()
        if "earnings" in text_lower or "results" in text_lower:
            return "Earnings"
        elif "dividend" in text_lower:
            return "Dividend"
        elif "acquisition" in text_lower or "acquired" in text_lower:
            return "Acquisition"
        elif "merger" in text_lower:
            return "Merger"
        elif "ipo" in text_lower or "listing" in text_lower:
            return "IPO"
        elif "split" in text_lower or "subdivision" in text_lower:
            return "Stock Split"
        elif "approval" in text_lower or "approved" in text_lower:
            return "Regulatory Approval"
        else:
            return "Other"

    @staticmethod
    def _extract_event_title(text: str) -> str:
        """Extract event title (usually first line)."""
        lines = text.strip().split("\n")
        return lines[0][:100] if lines else "Event"

    @staticmethod
    def _assess_impact(text: str) -> EventImpact:
        """Assess impact of event."""
        text_lower = text.lower()

        positive_indicators = ["growth", "increase", "exceed", "strong", "record", "upside"]
        negative_indicators = ["decline", "decrease", "loss", "weak", "challenge", "downside"]

        pos_count = sum(1 for word in positive_indicators if word in text_lower)
        neg_count = sum(1 for word in negative_indicators if word in text_lower)

        if pos_count > neg_count:
            return EventImpact.POSITIVE
        elif neg_count > pos_count:
            return EventImpact.NEGATIVE
        elif pos_count > 0 or neg_count > 0:
            return EventImpact.MIXED
        else:
            return EventImpact.NEUTRAL

    @staticmethod
    def _extract_financial_figures(text: str) -> List[ExtractedFigure]:
        """Extract financial figures from text."""
        figures = []

        # Dividend per share
        div_pattern = r"dividend.*?(\d+\.?\d*)\s*(?:per share|rupee|paise|pkg)"
        matches = re.findall(div_pattern, text, re.IGNORECASE)
        for match in matches:
            figures.append(
                ExtractedFigure(
                    figure_type="Dividend",
                    value=float(match),
                    unit="PKR",
                    context="per share",
                )
            )

        # Percentage changes
        pct_pattern = r"(\d+\.?\d*)\s*%"
        matches = re.findall(pct_pattern, text)
        for match in matches[:3]:  # Top 3 percentages
            figures.append(
                ExtractedFigure(
                    figure_type="Percentage",
                    value=float(match),
                    unit="%",
                    context="change",
                )
            )

        # Large amounts (millions/billions)
        amount_pattern = r"(\d+(?:,\d+)*)\s*(?:million|billion|crore)"
        matches = re.findall(amount_pattern, text, re.IGNORECASE)
        for match in matches[:2]:  # Top 2 amounts
            amount = float(match.replace(",", ""))
            figures.append(
                ExtractedFigure(
                    figure_type="Amount",
                    value=amount,
                    unit="PKR",
                    context="total",
                )
            )

        return figures

    @staticmethod
    def _extract_key_entities(text: str) -> List[KeyEntity]:
        """Extract key entities (people, companies)."""
        entities = []

        # CEO/Managing Director patterns
        ceo_pattern = r"(?:CEO|Chief Executive Officer|MD|Managing Director)[:\s]+([A-Z][a-z]+ [A-Z][a-z]+)"
        matches = re.findall(ceo_pattern, text)
        for match in matches:
            entities.append(KeyEntity(entity_type="Person", name=match, role="CEO"))

        # Company names (capitalized phrases)
        company_pattern = r"\b([A-Z][a-z]+ (?:Corporation|Limited|Ltd|Inc|Company))\b"
        matches = re.findall(company_pattern, text)
        for match in matches[:2]:
            entities.append(KeyEntity(entity_type="Company", name=match, role=None))

        return entities

    @staticmethod
    def _extract_implementation_date(text: str) -> Optional[str]:
        """Extract implementation/effective date."""
        date_pattern = r"(?:effective|implementation|payable).*?(\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4})"
        match = re.search(date_pattern, text, re.IGNORECASE)
        return match.group(1) if match else None

    @staticmethod
    def _extract_timeline(text: str) -> Optional[str]:
        """Extract timeline (duration or period)."""
        timeline_pattern = r"(?:within|during|by|in)\s+(?:the next\s+)?(\d+\s+(?:days|weeks|months|years)|next\s+quarter|end of year)"
        match = re.search(timeline_pattern, text, re.IGNORECASE)
        return match.group(1) if match else None

    @staticmethod
    def _extract_conditional_status(text: str) -> ConditionalStatus:
        """Extract conditional status."""
        text_lower = text.lower()
        if "completed" in text_lower or "effective" in text_lower:
            return ConditionalStatus.COMPLETED
        elif "subject to" in text_lower or "pending" in text_lower or "approval" in text_lower:
            return ConditionalStatus.CONDITIONAL
        elif "withdrawn" in text_lower or "cancelled" in text_lower:
            return ConditionalStatus.WITHDRAWN
        else:
            return ConditionalStatus.UNCONDITIONAL

    @staticmethod
    def _extract_probability(text: str, conditional: ConditionalStatus) -> float:
        """Extract probability of occurrence."""
        if conditional == ConditionalStatus.COMPLETED:
            return 100.0
        elif conditional == ConditionalStatus.WITHDRAWN:
            return 0.0
        else:
            # Default: 75% for conditional, 90% for unconditional
            return 75.0 if conditional == ConditionalStatus.CONDITIONAL else 90.0

    @staticmethod
    def _extract_sentiment_keywords(text: str) -> List[str]:
        """Extract sentiment keywords."""
        positive = ["growth", "increase", "strong", "record", "exceed", "expand"]
        negative = ["decline", "loss", "weak", "challenge", "miss", "risk"]

        found = []
        for word in positive + negative:
            if word in text.lower():
                found.append(word)
        return found[:5]

    @staticmethod
    def _extract_risk_factors(text: str) -> List[str]:
        """Extract risk factors mentioned."""
        risks = []
        if "volatile" in text.lower():
            risks.append("Market volatility")
        if "regulatory" in text.lower():
            risks.append("Regulatory changes")
        if "economic" in text.lower():
            risks.append("Economic uncertainty")
        if "competition" in text.lower():
            risks.append("Competitive pressure")
        return risks[:3]

    @staticmethod
    def _extract_opportunities(text: str) -> List[str]:
        """Extract opportunities mentioned."""
        opportunities = []
        if "expansion" in text.lower():
            opportunities.append("Market expansion")
        if "growth" in text.lower():
            opportunities.append("Growth potential")
        if "acquisition" in text.lower():
            opportunities.append("M&A opportunity")
        if "market" in text.lower():
            opportunities.append("Market opportunity")
        return opportunities[:3]

    @staticmethod
    def _extract_related_announcements(text: str) -> List[str]:
        """Extract references to related announcements."""
        # Look for date references to prior events
        date_pattern = r"(\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4})"
        matches = re.findall(date_pattern, text)
        return matches[1:4] if len(matches) > 1 else []  # Exclude current date

    @staticmethod
    def _extract_regulatory_approvals(text: str) -> List[str]:
        """Extract regulatory approvals needed."""
        approvals = []
        if "secp" in text.lower():
            approvals.append("SECP Approval")
        if "sbp" in text.lower():
            approvals.append("SBP Approval")
        if "board" in text.lower():
            approvals.append("Board Approval")
        if "shareholders" in text.lower():
            approvals.append("Shareholder Approval")
        return approvals[:3]

    @staticmethod
    def _extract_conditions(text: str) -> List[str]:
        """Extract conditions to meet."""
        conditions = []
        condition_pattern = r"(?:subject to|conditional on|provided that)\s+([^.;]+)"
        matches = re.findall(condition_pattern, text, re.IGNORECASE)
        conditions.extend(matches[:3])
        return [c.strip()[:80] for c in conditions]

    @staticmethod
    def _calculate_extraction_confidence(
        text: str, figures: List[ExtractedFigure], entities: List[KeyEntity]
    ) -> float:
        """Calculate confidence in extraction."""
        confidence = 70.0

        # More data = higher confidence
        confidence += len(figures) * 5
        confidence += len(entities) * 5

        # Structured format (numbers, dates) = higher confidence
        if re.search(r"\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}", text):
            confidence += 10

        # Length (more content = more detail)
        if len(text) > 500:
            confidence += 5

        return min(100, confidence)
