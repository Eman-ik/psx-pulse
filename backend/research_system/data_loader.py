"""
CSV Data Loader for Khronos Research System

Load company, peer group, and metric configurations from CSV files.

Supports:
- Company master data (security_master.csv)
- Peer group definitions (peer_groups.csv)
- Metric alias mappings (metric_aliases.csv)
"""

import csv
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

from sqlalchemy.orm import Session

from .schema import Security, Sector, Industry, MetricDefinition, MetricAlias
from .config import get_config


class CSVDataLoader:
    """Load configuration and master data from CSV files."""

    def __init__(self, data_dir: str = "data"):
        """Initialize loader with data directory.

        Args:
            data_dir: Path to directory containing CSV files
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)

    def load_securities_from_csv(self, session: Session, filepath: str) -> Dict[str, Any]:
        """Load securities (companies) from CSV file.

        CSV Format:
            ticker,company_name,legal_name,sector_name,industry_name,listing_date,fiscal_year_end,website,active

        Example:
            FFC,Fauji Fertilizer Company Limited,Fauji Fertilizer Company Limited,Fertilizer,Nitrogenous Fertilizer,1992-01-01,6,www.ffc.com.pk,true

        Args:
            session: SQLAlchemy session
            filepath: Path to CSV file

        Returns:
            Dictionary with counts: {created: int, skipped: int, errors: list}
        """
        results = {"created": 0, "skipped": 0, "errors": []}

        if not Path(filepath).exists():
            results["errors"].append(f"File not found: {filepath}")
            return results

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)

                for row_num, row in enumerate(reader, start=2):  # start=2 to account for header
                    try:
                        # Get or create sector
                        sector = session.query(Sector).filter_by(
                            sector_name=row["sector_name"]
                        ).first()
                        if not sector:
                            sector = Sector(sector_name=row["sector_name"])
                            session.add(sector)
                            session.flush()

                        # Get or create industry
                        industry = session.query(Industry).filter_by(
                            industry_name=row["industry_name"]
                        ).first()
                        if not industry:
                            industry = Industry(
                                industry_name=row["industry_name"],
                                sector_id=sector.sector_id,
                            )
                            session.add(industry)
                            session.flush()

                        # Check if security already exists
                        existing = session.query(Security).filter_by(
                            ticker=row["ticker"]
                        ).first()
                        if existing:
                            results["skipped"] += 1
                            continue

                        # Create security
                        security = Security(
                            ticker=row["ticker"],
                            company_name=row["company_name"],
                            legal_name=row["legal_name"],
                            sector_id=sector.sector_id,
                            industry_id=industry.industry_id,
                            listing_date=self._parse_date(row.get("listing_date")),
                            fiscal_year_end=int(row.get("fiscal_year_end", 12)),
                            website=row.get("website", ""),
                            active=self._parse_bool(row.get("active", "true")),
                        )
                        session.add(security)
                        results["created"] += 1

                    except Exception as e:
                        results["errors"].append(f"Row {row_num}: {str(e)}")

                session.commit()

        except Exception as e:
            results["errors"].append(f"File read error: {str(e)}")

        return results

    def load_metric_aliases_from_csv(
        self, session: Session, filepath: str
    ) -> Dict[str, Any]:
        """Load metric alias mappings from CSV file.

        CSV Format:
            metric_code,metric_name,alias,confidence

        Example:
            REVENUE,Revenue,Sales,0.95
            REVENUE,Revenue,Sales - Net,0.95
            NET_PROFIT,Net Profit,Net Income,0.90

        Args:
            session: SQLAlchemy session
            filepath: Path to CSV file

        Returns:
            Dictionary with counts: {created: int, skipped: int, errors: list}
        """
        results = {"created": 0, "skipped": 0, "errors": []}

        if not Path(filepath).exists():
            results["errors"].append(f"File not found: {filepath}")
            return results

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)

                for row_num, row in enumerate(reader, start=2):
                    try:
                        # Get or create metric definition
                        metric = session.query(MetricDefinition).filter_by(
                            metric_code=row["metric_code"]
                        ).first()
                        if not metric:
                            metric = MetricDefinition(
                                metric_code=row["metric_code"],
                                metric_name=row.get("metric_name", row["metric_code"]),
                                metric_type="INCOME_STATEMENT",  # Default type
                            )
                            session.add(metric)
                            session.flush()

                        # Check if alias already exists
                        existing = session.query(MetricAlias).filter_by(
                            metric_id=metric.metric_id,
                            alias=row["alias"],
                        ).first()
                        if existing:
                            results["skipped"] += 1
                            continue

                        # Create alias
                        alias = MetricAlias(
                            metric_id=metric.metric_id,
                            alias=row["alias"],
                            confidence=float(row.get("confidence", 0.9)),
                        )
                        session.add(alias)
                        results["created"] += 1

                    except Exception as e:
                        results["errors"].append(f"Row {row_num}: {str(e)}")

                session.commit()

        except Exception as e:
            results["errors"].append(f"File read error: {str(e)}")

        return results

    def export_securities_to_csv(
        self, session: Session, filepath: str
    ) -> Dict[str, Any]:
        """Export all securities to CSV file.

        Args:
            session: SQLAlchemy session
            filepath: Path to output CSV file

        Returns:
            Dictionary with count: {exported: int, errors: list}
        """
        results = {"exported": 0, "errors": []}

        try:
            securities = session.query(Security).all()

            with open(filepath, "w", newline="", encoding="utf-8") as f:
                fieldnames = [
                    "ticker", "company_name", "legal_name", "sector_name",
                    "industry_name", "listing_date", "fiscal_year_end",
                    "website", "active"
                ]
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()

                for sec in securities:
                    writer.writerow({
                        "ticker": sec.ticker,
                        "company_name": sec.company_name,
                        "legal_name": sec.legal_name,
                        "sector_name": sec.sector.sector_name if sec.sector else "",
                        "industry_name": sec.industry.industry_name if sec.industry else "",
                        "listing_date": sec.listing_date.isoformat() if sec.listing_date else "",
                        "fiscal_year_end": sec.fiscal_year_end,
                        "website": sec.website or "",
                        "active": "true" if sec.active else "false",
                    })
                    results["exported"] += 1

        except Exception as e:
            results["errors"].append(f"Export error: {str(e)}")

        return results

    def export_metric_aliases_to_csv(
        self, session: Session, filepath: str
    ) -> Dict[str, Any]:
        """Export all metric aliases to CSV file.

        Args:
            session: SQLAlchemy session
            filepath: Path to output CSV file

        Returns:
            Dictionary with count: {exported: int, errors: list}
        """
        results = {"exported": 0, "errors": []}

        try:
            aliases = session.query(MetricAlias).join(MetricDefinition).all()

            with open(filepath, "w", newline="", encoding="utf-8") as f:
                fieldnames = ["metric_code", "metric_name", "alias", "confidence"]
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()

                for alias in aliases:
                    writer.writerow({
                        "metric_code": alias.metric.metric_code,
                        "metric_name": alias.metric.metric_name,
                        "alias": alias.alias,
                        "confidence": alias.confidence or 0.9,
                    })
                    results["exported"] += 1

        except Exception as e:
            results["errors"].append(f"Export error: {str(e)}")

        return results

    @staticmethod
    def _parse_date(date_str: Optional[str]) -> Optional[datetime]:
        """Parse date string to datetime object.

        Args:
            date_str: Date string in ISO format (YYYY-MM-DD)

        Returns:
            datetime object or None
        """
        if not date_str or date_str.strip() == "":
            return None

        try:
            return datetime.fromisoformat(date_str)
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _parse_bool(value: str) -> bool:
        """Parse string to boolean.

        Args:
            value: String value (true/false, yes/no, 1/0)

        Returns:
            Boolean value
        """
        return value.lower() in ("true", "1", "yes", "t", "y")

    def create_sample_csv_files(self) -> None:
        """Create sample CSV files in data directory."""
        # Sample securities CSV
        securities_file = self.data_dir / "securities.csv"
        if not securities_file.exists():
            with open(securities_file, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "ticker", "company_name", "legal_name", "sector_name",
                    "industry_name", "listing_date", "fiscal_year_end", "website", "active"
                ])
                writer.writerow([
                    "FFC", "Fauji Fertilizer Company Limited",
                    "Fauji Fertilizer Company Limited", "Fertilizer",
                    "Nitrogenous Fertilizer", "1992-01-01", "6",
                    "www.ffc.com.pk", "true"
                ])
                writer.writerow([
                    "MCB", "MCB Bank Limited", "MCB Bank Limited",
                    "Banking", "Commercial Banking", "1947-06-24", "12",
                    "www.mcb.com.pk", "true"
                ])

        # Sample aliases CSV
        aliases_file = self.data_dir / "metric_aliases.csv"
        if not aliases_file.exists():
            with open(aliases_file, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "metric_code", "metric_name", "alias", "confidence"
                ])
                writer.writerow(["REVENUE", "Revenue", "Sales", "0.95"])
                writer.writerow(["REVENUE", "Revenue", "Sales - Net", "0.95"])
                writer.writerow(["NET_PROFIT", "Net Profit", "Net Income", "0.90"])
                writer.writerow(["TOTAL_ASSETS", "Total Assets", "Assets", "0.85"])
