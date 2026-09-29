"""
R6: Announcement Intelligence Engine
Extract and classify FFC corporate announcements

Ingest:
- PSX announcements (results, dividends, board meetings, mergers, etc.)
- Extract key metrics (PAT, EPS, DPS from announcement text)
- Link to financial statements
- Score impact (positive/negative/neutral)

Output:
- announcements table (classified, parsed metrics)
- corporate_events table (groups related announcements)
- Enables: "What changed since last quarter?"
"""

import logging
import re
from datetime import datetime, date
from typing import Optional, List, Tuple, Dict
from enum import Enum
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc

from models import (
    Company, Document, FinancialMetric, MetricDefinition,
    Announcement, CorporateEvent, AnnouncementType
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# FFC Historical Announcements (Manual Configuration)
# In production: Fetch from PSX API
# ============================================================================

FFC_ANNOUNCEMENTS = [
    {
        "date": date(2024, 11, 15),
        "title": "FFC Announces Q3 2024 Results",
        "text": """
        Fauji Fertilizer Company Limited announces Q3 2024 financial results:

        Profit After Tax: Rs. 2,847 million (Q3 2023: Rs. 2,104 million)
        Growth: +35.3% YoY

        Earnings Per Share: Rs. 2.01 (Q3 2023: Rs. 1.49)
        Growth: +34.9% YoY

        Revenue: Rs. 18,432 million (Q3 2023: Rs. 15,821 million)
        Growth: +16.5% YoY

        Gross Margin: 42.1% (Q3 2023: 39.8%)

        The company's improved results reflect strong fertilizer demand and
        better pricing environment.
        """,
        "type": "result"
    },
    {
        "date": date(2024, 11, 20),
        "title": "FFC Board Approves Interim Dividend",
        "text": """
        The Board of Directors of FFC has approved an interim dividend of
        Rs. 1.50 per share for the nine-month period ended September 30, 2024.

        Record Date: December 2, 2024
        Payment Date: December 10, 2024

        Dividend Per Share: Rs. 1.50
        Total Dividend: Rs. 2,130 million

        This is in addition to any final dividend that may be approved
        for the full year.
        """,
        "type": "dividend"
    },
    {
        "date": date(2024, 8, 30),
        "title": "FFC H1 2024 Results",
        "text": """
        FFC announces H1 2024 financial results:

        Profit After Tax: Rs. 5,621 million (H1 2023: Rs. 4,012 million)
        Growth: +40.1% YoY

        Earnings Per Share: Rs. 3.97 (H1 2023: Rs. 2.83)
        Growth: +40.3% YoY

        Revenue: Rs. 34,821 million (H1 2023: Rs. 30,142 million)
        Growth: +15.5% YoY

        EBITDA: Rs. 9,240 million (H1 2023: Rs. 7,321 million)
        EBITDA Margin: 26.5% (H1 2023: 24.3%)

        Strong operational performance driven by higher urea prices and
        improved demand.
        """,
        "type": "result"
    },
    {
        "date": date(2024, 5, 15),
        "title": "FFC Announces Q1 2024 Results",
        "text": """
        FFC announces Q1 2024 financial results:

        Profit After Tax: Rs. 2,774 million (Q1 2023: Rs. 1,908 million)
        Growth: +45.4% YoY

        Earnings Per Share: Rs. 1.96 (Q1 2023: Rs. 1.35)
        Growth: +45.2% YoY

        Revenue: Rs. 16,389 million (Q1 2023: Rs. 14,321 million)
        Growth: +14.4% YoY

        The significant profit growth reflects strong urea prices and
        increased offtake during the spring season.
        """,
        "type": "result"
    },
    {
        "date": date(2024, 3, 25),
        "title": "FFC Board Meeting Scheduled",
        "text": """
        Notice of Board Meeting:

        The Board of Directors of Fauji Fertilizer Company Limited will
        hold its meeting on March 29, 2024 at the registered office.

        Agenda:
        - Review of financial results for year ended December 31, 2023
        - Approval of final dividend (if any)
        - Other business matters

        Closure of Share Transfer Books: March 29-31, 2024
        """,
        "type": "board_meeting"
    },
    {
        "date": date(2024, 2, 15),
        "title": "FFC FY2023 Annual Results",
        "text": """
        FFC announces FY2023 financial results:

        Profit After Tax: Rs. 11,742 million (FY2022: Rs. 8,923 million)
        Growth: +31.6% YoY

        Earnings Per Share: Rs. 8.28 (FY2022: Rs. 6.30)
        Growth: +31.4% YoY

        Revenue: Rs. 74,232 million (FY2022: Rs. 63,421 million)
        Growth: +17.1% YoY

        Gross Profit: Rs. 22,911 million
        Gross Margin: 30.9% (FY2022: 29.3%)

        The company achieved record earnings driven by strong urea prices
        and improved operational efficiency.
        """,
        "type": "result"
    },
]

class AnnouncementClassifier:
    """Classify and extract data from announcements"""

    # Pattern templates for metric extraction
    METRIC_PATTERNS = {
        "PAT": [
            r"Profit After Tax.*?Rs\.\s+([\d,]+)\s*(?:million|crore)",
            r"PAT.*?Rs\.\s+([\d,]+)\s*(?:million|crore)",
            r"Net profit.*?Rs\.\s+([\d,]+)\s*(?:million|crore)",
        ],
        "EPS": [
            r"Earnings Per Share.*?Rs\.\s+([\d.]+)",
            r"EPS.*?Rs\.\s+([\d.]+)",
            r"Per share.*?Rs\.\s+([\d.]+)",
        ],
        "DPS": [
            r"Dividend.*?Rs\.\s+([\d.]+)\s*per share",
            r"Dividend of Rs\.\s+([\d.]+)",
            r"DPS.*?Rs\.\s+([\d.]+)",
        ],
        "REV": [
            r"Revenue.*?Rs\.\s+([\d,]+)\s*(?:million|crore)",
            r"Sales.*?Rs\.\s+([\d,]+)\s*(?:million|crore)",
        ],
        "EBITDA": [
            r"EBITDA.*?Rs\.\s+([\d,]+)\s*(?:million|crore)",
            r"Earnings before.*?Rs\.\s+([\d,]+)\s*(?:million|crore)",
        ],
    }

    @staticmethod
    def classify_announcement(title: str, text: str) -> str:
        """Classify announcement type based on content"""

        content = (title + " " + text).lower()

        # Classification rules (in priority order)
        if any(word in content for word in ["result", "earnings", "profit", "revenue"]):
            return "result"
        elif any(word in content for word in ["dividend", "payout"]):
            return "dividend"
        elif any(word in content for word in ["board meeting", "agm", "eogm"]):
            return "board_meeting"
        elif any(word in content for word in ["merger", "acquisition", "amalgamation"]):
            return "merger"
        elif any(word in content for word in ["buyback", "repurchase"]):
            return "buyback"
        elif any(word in content for word in ["right", "bonus", "split"]):
            return "right_issue"
        elif any(word in content for word in ["material", "information", "change"]):
            return "material_info"
        elif any(word in content for word in ["ceo", "director", "management"]):
            return "management_change"
        elif any(word in content for word in ["project", "facility", "capacity"]):
            return "project_update"
        else:
            return "material_info"

    @staticmethod
    def extract_metrics(text: str) -> Dict[str, Optional[float]]:
        """Extract key metrics from announcement text"""

        extracted = {}

        for metric_code, patterns in AnnouncementClassifier.METRIC_PATTERNS.items():
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    try:
                        value_str = match.group(1).replace(",", "")
                        value = float(value_str)

                        # Convert millions to base units if needed
                        if "million" in match.group(0).lower():
                            # For EPS/DPS, keep as is; for PAT/REV, convert to units
                            if metric_code in ["PAT", "REV", "EBITDA"]:
                                value = value * 1_000_000
                        elif "crore" in match.group(0).lower():
                            if metric_code in ["PAT", "REV", "EBITDA"]:
                                value = value * 10_000_000

                        extracted[metric_code] = value
                        break
                    except (ValueError, AttributeError):
                        pass

        return extracted

    @staticmethod
    def score_impact(announcement_type: str, extracted_metrics: Dict) -> float:
        """Score impact of announcement (-1 to +1, where 1 is most positive)"""

        base_scores = {
            "result": 0.0,  # Depends on metric changes
            "dividend": 0.7,  # Generally positive
            "board_meeting": 0.1,  # Neutral
            "merger": 0.5,  # Could be positive or negative
            "buyback": 0.6,  # Generally positive
            "right_issue": -0.3,  # Dilution concern
            "material_info": 0.0,  # Neutral
            "management_change": 0.0,  # Depends on context
            "project_update": 0.4,  # Generally positive
        }

        score = base_scores.get(announcement_type, 0.0)

        # Adjust based on metrics extracted
        if "PAT" in extracted_metrics and "EPS" in extracted_metrics:
            # Check if growth is positive
            score += 0.3  # Earnings announcement detected

        return min(1.0, max(-1.0, score))  # Clamp to -1 to 1

class AnnouncementIntelligence:
    """Main announcement intelligence orchestrator"""

    def __init__(self, session: Session):
        self.session = session
        self.classifier = AnnouncementClassifier()
        self.stats = {
            "announcements_ingested": 0,
            "metrics_extracted": 0,
            "events_created": 0,
            "errors": 0
        }

    def ingest_announcements(
        self,
        company_id: int,
        announcements: List[dict]
    ) -> int:
        """Ingest announcements into database"""

        count = 0
        for ann_data in announcements:
            # Check if already exists
            existing = self.session.query(Announcement).filter(
                and_(
                    Announcement.company_id == company_id,
                    Announcement.announcement_date == ann_data["date"],
                    Announcement.title == ann_data["title"]
                )
            ).first()

            if existing:
                continue

            # Classify
            ann_type = self.classifier.classify_announcement(
                ann_data["title"],
                ann_data["text"]
            )

            # Extract metrics
            metrics = self.classifier.extract_metrics(ann_data["text"])

            # Score impact
            impact = self.classifier.score_impact(ann_type, metrics)

            # Create announcement record
            announcement = Announcement(
                company_id=company_id,
                announcement_type=AnnouncementType[ann_type.upper()],
                announcement_date=ann_data["date"],
                title=ann_data["title"],
                raw_text=ann_data["text"],
                parsed_data={
                    "extracted_metrics": metrics,
                    "metric_values": {k: float(v) for k, v in metrics.items()}
                },
                classification_confidence=0.95,
                impact_score=impact,
                source="psx",
                processed_at=datetime.utcnow()
            )

            self.session.add(announcement)
            self.session.flush()

            self.stats["announcements_ingested"] += 1
            self.stats["metrics_extracted"] += len(metrics)

            count += 1

        self.session.commit()
        return count

    def group_into_events(self, company_id: int) -> int:
        """Group related announcements into corporate events"""

        # Get all announcements for company
        announcements = self.session.query(Announcement).filter_by(
            company_id=company_id
        ).order_by(desc(Announcement.announcement_date)).all()

        events_created = 0

        # Group by date (announcements on same day are likely related)
        date_groups = {}
        for ann in announcements:
            key = ann.announcement_date
            if key not in date_groups:
                date_groups[key] = []
            date_groups[key].append(ann)

        # Create events
        for event_date, anns in date_groups.items():
            # Check if event already exists
            existing = self.session.query(CorporateEvent).filter(
                and_(
                    CorporateEvent.company_id == company_id,
                    CorporateEvent.event_date == event_date
                )
            ).first()

            if existing:
                continue

            # Determine event type from announcements
            types = set(ann.announcement_type.value for ann in anns)
            primary_type = sorted(types)[0]  # Use alphabetically first

            # Create summary
            summary = f"{len(anns)} announcement(s): " + ", ".join(types)

            # Create event
            event = CorporateEvent(
                company_id=company_id,
                event_type=primary_type,
                event_date=event_date,
                summary=summary,
                document_ids=[ann.announcement_id for ann in anns]
            )

            self.session.add(event)
            events_created += 1

        self.session.commit()
        self.stats["events_created"] = events_created

        return events_created

    def process_ffc_announcements(self) -> dict:
        """Complete R6 pipeline for FFC"""

        logger.info("\n" + "="*60)
        logger.info("R6: Announcement Intelligence Engine")
        logger.info("="*60 + "\n")

        # Get FFC
        ffc = self.session.query(Company).filter_by(ticker="FFC").first()
        if not ffc:
            logger.error("[ERROR] FFC not found. Run R1 initialization first.")
            return {"status": "failed", "reason": "FFC not found"}

        logger.info(f"[OK] Found FFC (company_id: {ffc.company_id})\n")

        # Step 1: Ingest announcements
        logger.info("Step 1: Ingesting announcements...")
        count = self.ingest_announcements(ffc.company_id, FFC_ANNOUNCEMENTS)
        logger.info(f"[OK] Ingested {count} announcements")

        # Step 2: Group into events
        logger.info("\nStep 2: Grouping announcements into corporate events...")
        events = self.group_into_events(ffc.company_id)
        logger.info(f"[OK] Created {events} corporate events")

        # Step 3: Display announcement summary
        logger.info("\n" + "="*60)
        logger.info("FFC Announcements Summary")
        logger.info("="*60)

        anns = self.session.query(Announcement).filter_by(
            company_id=ffc.company_id
        ).order_by(desc(Announcement.announcement_date)).all()

        logger.info(f"\nTotal Announcements: {len(anns)}\n")

        for ann in anns[:5]:  # Show last 5
            logger.info(f"Date: {ann.announcement_date}")
            logger.info(f"Type: {ann.announcement_type.value.upper()}")
            logger.info(f"Title: {ann.title}")

            if ann.parsed_data and "extracted_metrics" in ann.parsed_data:
                metrics = ann.parsed_data["extracted_metrics"]
                if metrics:
                    logger.info(f"Metrics: {', '.join(f'{k}={v:.2f}' for k, v in metrics.items())}")

            logger.info(f"Impact: {ann.impact_score:+.2f}")
            logger.info("")

        logger.info("="*60)
        logger.info("R6: Announcement Intelligence Complete")
        logger.info("="*60)
        logger.info(f"Announcements Ingested: {self.stats['announcements_ingested']}")
        logger.info(f"Metrics Extracted:      {self.stats['metrics_extracted']}")
        logger.info(f"Events Created:         {self.stats['events_created']}")
        logger.info("="*60 + "\n")

        logger.info("\nKey Insights:")

        # Calculate YoY growth from announcements
        latest_ann = next((a for a in anns if a.announcement_type.value == "result"), None)
        if latest_ann and latest_ann.parsed_data:
            metrics = latest_ann.parsed_data.get("extracted_metrics", {})
            if "PAT" in metrics:
                logger.info(f"- Latest PAT: Rs. {metrics['PAT']:,.0f}")
            if "EPS" in metrics:
                logger.info(f"- Latest EPS: Rs. {metrics['EPS']:.2f}")

        # Dividend announcements
        div_anns = [a for a in anns if a.announcement_type.value == "dividend"]
        if div_anns:
            latest_div = div_anns[0]
            if latest_div.parsed_data and "extracted_metrics" in latest_div.parsed_data:
                metrics = latest_div.parsed_data["extracted_metrics"]
                if "DPS" in metrics:
                    logger.info(f"- Latest Dividend Per Share: Rs. {metrics['DPS']:.2f}")

        logger.info("\nNext Steps:")
        logger.info("1. R7: AI Copilot (Answer 'Why did earnings grow?')")
        logger.info("2. R8: Research Workspace UI (Unified company research hub)")

        return {
            "status": "completed",
            "stats": self.stats
        }

def main():
    """Run announcement intelligence"""
    import os
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/research_studio"
    )

    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()

    try:
        intelligence = AnnouncementIntelligence(session)
        result = intelligence.process_ffc_announcements()
        print(f"\nResult: {result}")
    finally:
        session.close()

if __name__ == "__main__":
    main()
