"""
Module 6, Sprint R7: Events Context Integration

Catalyst and event-driven trade planning.

Event types:
- Company: Earnings, dividends, splits, mergers, analyst days
- Market: Economic calendar (Fed, jobs, inflation, GDP), major indices events
- Sector: Industry catalysts, regulatory changes

Impact assessment:
- Days to event (entry timing)
- Implied volatility (straddle risk)
- Historical reaction magnitude
- Safety recommendations
"""

from dataclasses import dataclass, field
from enum import Enum
from datetime import date, timedelta
from typing import Optional, List, Dict, Tuple


# ════════════════════════════════════════════════════════════════════════════════
# ENUMS
# ════════════════════════════════════════════════════════════════════════════════

class EventType(Enum):
    """Types of events affecting trade decisions."""
    # Company events
    EARNINGS = "EARNINGS"
    DIVIDEND = "DIVIDEND"
    STOCK_SPLIT = "STOCK_SPLIT"
    MERGER_ACQUISITION = "MERGER_ACQUISITION"
    ANALYST_DAY = "ANALYST_DAY"
    PRODUCT_LAUNCH = "PRODUCT_LAUNCH"

    # Market events
    FOMC_MEETING = "FOMC_MEETING"
    JOBS_REPORT = "JOBS_REPORT"
    INFLATION_REPORT = "INFLATION_REPORT"
    GDP_REPORT = "GDP_REPORT"
    EARNINGS_SEASON = "EARNINGS_SEASON"
    MARKET_HOLIDAY = "MARKET_HOLIDAY"

    # Sector events
    REGULATORY_DECISION = "REGULATORY_DECISION"
    INDUSTRY_CATALYST = "INDUSTRY_CATALYST"


class EventRisk(Enum):
    """Risk level of upcoming events."""
    LOW = "LOW"              # <2 days out or well-known
    MODERATE = "MODERATE"    # 2-5 days out, typical reaction
    HIGH = "HIGH"            # 1-2 days out, significant potential
    CRITICAL = "CRITICAL"    # Same day, high volatility


class EventTiming(Enum):
    """Timing relative to event."""
    LONG_BEFORE = "LONG_BEFORE"    # >30 days
    BEFORE = "BEFORE"              # 8-30 days
    NEAR = "NEAR"                  # 3-7 days
    IMMEDIATE = "IMMEDIATE"        # 1-2 days
    DAY_OF = "DAY_OF"              # Same trading day
    AFTER = "AFTER"                # Passed


class EntryRecommendation(Enum):
    """Entry recommendation based on events."""
    FAVORABLE = "FAVORABLE"      # Enter before event (catalyst positive)
    AVOID = "AVOID"              # Avoid entry (high risk)
    WAIT = "WAIT"                # Wait for clarity (post-event)
    NEUTRAL = "NEUTRAL"          # No impact on entry


# ════════════════════════════════════════════════════════════════════════════════
# DATA CLASSES
# ════════════════════════════════════════════════════════════════════════════════

@dataclass
class Event:
    """Single upcoming event."""
    event_type: EventType
    event_date: date
    description: str
    location: Optional[str] = None
    expected_volatility_impact: float = 0.0  # Expected IV increase (%)
    historical_avg_move: Optional[float] = None  # Typical price move %
    importance: int = 5  # 1-10 importance scale

    def days_away(self, from_date: date = None) -> int:
        """Days until event."""
        ref_date = from_date or date.today()
        return (self.event_date - ref_date).days

    def get_timing(self, from_date: date = None) -> EventTiming:
        """Classify timing relative to event."""
        days = self.days_away(from_date)

        if days < 0:
            return EventTiming.AFTER
        elif days == 0:
            return EventTiming.DAY_OF
        elif days <= 2:
            return EventTiming.IMMEDIATE
        elif days <= 7:
            return EventTiming.NEAR
        elif days <= 30:
            return EventTiming.BEFORE
        else:
            return EventTiming.LONG_BEFORE

    def get_risk_level(self, from_date: date = None) -> EventRisk:
        """Assess event risk level."""
        timing = self.get_timing(from_date)

        if timing == EventTiming.AFTER:
            return EventRisk.LOW
        elif timing == EventTiming.LONG_BEFORE:
            return EventRisk.LOW
        elif timing == EventTiming.BEFORE:
            return EventRisk.MODERATE
        elif timing == EventTiming.NEAR:
            return EventRisk.HIGH
        elif timing in [EventTiming.IMMEDIATE, EventTiming.DAY_OF]:
            return EventRisk.CRITICAL
        else:
            return EventRisk.MODERATE

    def to_dict(self) -> Dict:
        """Serialize to dict."""
        return {
            "event_type": self.event_type.value,
            "event_date": self.event_date.isoformat(),
            "description": self.description,
            "location": self.location,
            "expected_volatility_impact": self.expected_volatility_impact,
            "historical_avg_move": self.historical_avg_move,
            "importance": self.importance,
        }


@dataclass
class EventCalendar:
    """Complete event calendar for trade planning."""
    ticker: str
    upcoming_events: List[Event] = field(default_factory=list)
    nearest_event: Optional[Event] = None
    days_to_nearest: int = 0
    event_risk_score: float = 0.0  # 0-100, higher = more risky
    entry_recommendation: EntryRecommendation = EntryRecommendation.NEUTRAL
    description: str = ""

    def to_dict(self) -> Dict:
        """Serialize to dict for API."""
        return {
            "ticker": self.ticker,
            "upcoming_events": [e.to_dict() for e in self.upcoming_events],
            "nearest_event": self.nearest_event.to_dict() if self.nearest_event else None,
            "days_to_nearest": self.days_to_nearest,
            "event_risk_score": self.event_risk_score,
            "entry_recommendation": self.entry_recommendation.value,
            "description": self.description,
        }


# ════════════════════════════════════════════════════════════════════════════════
# EVENTS EXTRACTOR
# ════════════════════════════════════════════════════════════════════════════════

class EventContextExtractor:
    """Extract and assess event risk."""

    @staticmethod
    def calculate_event_risk_score(
        days_to_event: int,
        event_importance: int,
        expected_volatility: float
    ) -> float:
        """
        Calculate event risk score (0-100).

        Components:
        - Proximity (50 pts): Closer = riskier
        - Importance (30 pts): More important = riskier
        - Volatility (20 pts): Higher IV impact = riskier
        """
        score = 0.0

        # Proximity (50 pts): Closer events are riskier
        if days_to_event <= 0:
            score += 50  # Day of event
        elif days_to_event <= 2:
            score += 45
        elif days_to_event <= 5:
            score += 35
        elif days_to_event <= 10:
            score += 25
        elif days_to_event <= 30:
            score += 15
        else:
            score += 5

        # Importance (30 pts): 1-10 scale
        score += min(30, (event_importance / 10) * 30)

        # Volatility impact (20 pts)
        score += min(20, expected_volatility / 5)  # 5% IV = 20 pts

        return min(max(score, 0), 100)

    @staticmethod
    def get_entry_recommendation(
        event_risk: EventRisk,
        timing: EventTiming,
        event_type: EventType,
        historical_move: Optional[float] = None
    ) -> EntryRecommendation:
        """
        Recommend entry timing based on event.

        Earnings/econ data = AVOID (high volatility)
        3-7 days before known catalyst = FAVORABLE
        Day of event = AVOID
        After event = WAIT (for clarity)
        """

        # Critical risk events = avoid
        if event_risk == EventRisk.CRITICAL:
            return EntryRecommendation.AVOID

        # Day of event = avoid
        if timing == EventTiming.DAY_OF:
            return EntryRecommendation.AVOID

        # Immediate window (1-2 days before) = risky, avoid unless favorable
        if timing == EventTiming.IMMEDIATE:
            if event_type == EventType.EARNINGS and historical_move and historical_move < 2:
                return EntryRecommendation.FAVORABLE  # Small typical move
            return EntryRecommendation.AVOID

        # Near window (3-7 days) = potentially favorable before positive catalyst
        if timing == EventTiming.NEAR:
            if event_type in [EventType.ANALYST_DAY, EventType.PRODUCT_LAUNCH]:
                return EntryRecommendation.FAVORABLE
            elif event_type == EventType.EARNINGS:
                return EntryRecommendation.AVOID  # Still risky
            return EntryRecommendation.NEUTRAL

        # After event = wait for clarity
        if timing == EventTiming.AFTER:
            return EntryRecommendation.WAIT

        # Before window (8-30 days) = typically safe
        if timing == EventTiming.BEFORE:
            return EntryRecommendation.FAVORABLE

        # Long before = neutral
        return EntryRecommendation.NEUTRAL

    @staticmethod
    def extract_event_context(
        ticker: str,
        upcoming_events: List[Event]
    ) -> EventCalendar:
        """Extract complete event calendar context."""

        if not upcoming_events:
            return EventCalendar(
                ticker=ticker,
                upcoming_events=[],
                description=f"{ticker}: No upcoming events identified."
            )

        # Sort by date
        sorted_events = sorted(upcoming_events, key=lambda e: e.event_date)

        # Find nearest event
        today = date.today()
        nearest = None
        days_to_nearest = float('inf')

        for event in sorted_events:
            days = event.days_away(today)
            if 0 <= days < days_to_nearest:
                nearest = event
                days_to_nearest = days

        if nearest is None and sorted_events:
            # All events are in future, take closest
            nearest = sorted_events[0]
            days_to_nearest = nearest.days_away(today)

        # Calculate risk score for nearest event
        event_risk_score = 0.0
        if nearest:
            event_risk_score = EventContextExtractor.calculate_event_risk_score(
                days_to_event=max(0, days_to_nearest),
                event_importance=nearest.importance,
                expected_volatility=nearest.expected_volatility_impact
            )

        # Get entry recommendation
        entry_rec = EntryRecommendation.NEUTRAL
        if nearest:
            timing = nearest.get_timing(today)
            risk = nearest.get_risk_level(today)
            entry_rec = EventContextExtractor.get_entry_recommendation(
                event_risk=risk,
                timing=timing,
                event_type=nearest.event_type,
                historical_move=nearest.historical_avg_move
            )

        # Build description
        description = f"{ticker}: "
        if nearest:
            description += f"Nearest event: {nearest.event_type.value} on {nearest.event_date} "
            description += f"({days_to_nearest} days away). "
            description += f"Risk score: {event_risk_score:.0f}/100. "
            description += f"Recommendation: {entry_rec.value}. "
        else:
            description += "No upcoming events."

        return EventCalendar(
            ticker=ticker,
            upcoming_events=sorted_events,
            nearest_event=nearest,
            days_to_nearest=max(0, days_to_nearest) if days_to_nearest != float('inf') else 0,
            event_risk_score=event_risk_score,
            entry_recommendation=entry_rec,
            description=description,
        )


# ════════════════════════════════════════════════════════════════════════════════
# EVENT VALIDATOR
# ════════════════════════════════════════════════════════════════════════════════

class EventValidator:
    """Validate entry decisions against event calendar."""

    @staticmethod
    def validate_entry_around_events(
        event_calendar: EventCalendar,
        entry_price: float
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate if entry timing is sound vs events.

        Returns: (is_valid, warning_message)
        """
        warnings = []

        # High risk = warning
        if event_calendar.event_risk_score > 70:
            warnings.append(
                f"High event risk score ({event_calendar.event_risk_score:.0f}/100). "
                f"Consider waiting or sizing down."
            )

        # Critical recommendations = caution
        if event_calendar.entry_recommendation == EntryRecommendation.AVOID:
            warnings.append(
                f"Entry recommendation: AVOID due to upcoming {event_calendar.nearest_event.event_type.value} "
                f"in {event_calendar.days_to_nearest} days."
            )

        # Wait recommendations = caution
        if event_calendar.entry_recommendation == EntryRecommendation.WAIT:
            warnings.append(
                f"Wait for clarity after {event_calendar.nearest_event.event_type.value}. "
                f"Current event risk warrants post-event confirmation."
            )

        combined_warning = " | ".join(warnings) if warnings else None
        return True, combined_warning

    @staticmethod
    def validate_earnings_entry(
        days_to_earnings: int,
        historical_earnings_move: Optional[float] = None
    ) -> Tuple[bool, Optional[str]]:
        """Validate entry decision around earnings."""

        # Day of or day before earnings = caution
        if days_to_earnings <= 1:
            return True, f"Earnings in {days_to_earnings} day(s). High IV risk."

        # 2-5 days = moderate caution
        if days_to_earnings <= 5:
            move_pct = historical_earnings_move or 3.0
            return True, f"Earnings in {days_to_earnings} days. Typical move: {move_pct:.1f}%"

        # >30 days = typically safe
        if days_to_earnings > 30:
            return True, None

        # 6-30 days = caution if large expected move
        if historical_earnings_move and historical_earnings_move > 5:
            return True, f"Earnings in {days_to_earnings} days. Large expected move {historical_earnings_move:.1f}%."

        return True, None


# ════════════════════════════════════════════════════════════════════════════════
# INTEGRATION FUNCTIONS
# ════════════════════════════════════════════════════════════════════════════════

def enhance_trade_plan_with_events(
    trade_plan: Dict,
    event_calendar: EventCalendar,
) -> Dict:
    """Add events context to trade plan."""
    enhanced = trade_plan.copy()

    # Add event calendar
    enhanced["event_calendar"] = event_calendar.to_dict()

    # Add validation
    is_valid, warning = EventValidator.validate_entry_around_events(
        event_calendar,
        trade_plan.get("entry_price", 0)
    )
    enhanced["event_validation"] = {
        "is_valid": is_valid,
        "warning": warning,
    }

    # Add event warnings
    warnings = []
    if warning:
        warnings.append(warning)

    # Earnings-specific validation
    if event_calendar.nearest_event and event_calendar.nearest_event.event_type == EventType.EARNINGS:
        _, earnings_warning = EventValidator.validate_earnings_entry(
            event_calendar.days_to_nearest,
            event_calendar.nearest_event.historical_avg_move
        )
        if earnings_warning:
            warnings.append(earnings_warning)

    enhanced["event_warnings"] = warnings

    return enhanced


# ════════════════════════════════════════════════════════════════════════════════
# API HANDLERS
# ════════════════════════════════════════════════════════════════════════════════

def api_get_event_context(
    ticker: str,
    upcoming_events: List[Dict]
) -> Dict:
    """API: Get event context."""
    try:
        # Convert dict events to Event objects
        events = []
        for evt in upcoming_events:
            event = Event(
                event_type=EventType[evt.get("event_type", "EARNINGS")],
                event_date=date.fromisoformat(evt.get("event_date", date.today().isoformat())),
                description=evt.get("description", ""),
                location=evt.get("location"),
                expected_volatility_impact=evt.get("expected_volatility_impact", 0.0),
                historical_avg_move=evt.get("historical_avg_move"),
                importance=evt.get("importance", 5),
            )
            events.append(event)

        context = EventContextExtractor.extract_event_context(
            ticker=ticker,
            upcoming_events=events
        )

        return {
            "success": True,
            "event_calendar": context.to_dict(),
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }
