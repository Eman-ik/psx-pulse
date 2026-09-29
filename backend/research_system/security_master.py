"""
Security Master Implementation (Sprint 1)

Single source of truth for all PSX companies.
Every company gets exactly one security_id.
All data (prices, financials, announcements) attach to security_id, not ticker string.
"""

from datetime import datetime
from sqlalchemy.orm import Session
from .schema import Sector, Industry, Security, CompanyProfile, Source, SourceType, AuthorityLevel
from .database import get_session
from .psx_companies import PSX_COMPANIES


def ensure_sectors_exist(session: Session) -> dict:
    """
    Ensure all sectors exist in database.
    Returns mapping of sector_name -> sector_id.
    """
    sectors_data = {
        "Fertilizer": "Fertilizer manufacturers and producers",
        "Cement": "Cement and concrete manufacturers",
        "Banking": "Commercial and investment banks",
        "E&P": "Oil and gas exploration and production",
        "Miscellaneous": "Other sectors",
    }

    sector_map = {}
    for sector_name, description in sectors_data.items():
        existing = session.query(Sector).filter_by(sector_name=sector_name).first()
        if existing:
            sector_map[sector_name] = existing.sector_id
        else:
            sector = Sector(sector_name=sector_name)
            session.add(sector)
            session.flush()
            sector_map[sector_name] = sector.sector_id

    session.commit()
    print(f"[OK] Sectors ensured: {len(sector_map)} sectors in database")
    return sector_map


def ensure_industries_exist(session: Session, sector_map: dict) -> dict:
    """
    Ensure all industries exist in database.
    Returns mapping of (industry_name, sector_name) -> industry_id.
    """
    industries_data = {
        ("Nitrogenous Fertilizer", "Fertilizer"): "Producers of nitrogenous fertilizers",
        ("Portland Cement", "Cement"): "Manufacturers of Portland cement",
        ("Commercial Banking", "Banking"): "Commercial and retail banks",
        ("Oil & Gas Exploration & Production", "E&P"): "E&P operators",
        ("Beverages", "Miscellaneous"): "Beverage manufacturers",
    }

    industry_map = {}
    for (industry_name, sector_name), description in industries_data.items():
        existing = session.query(Industry).filter_by(industry_name=industry_name).first()
        if existing:
            industry_map[(industry_name, sector_name)] = existing.industry_id
        else:
            industry = Industry(
                industry_name=industry_name,
                sector_id=sector_map[sector_name]
            )
            session.add(industry)
            session.flush()
            industry_map[(industry_name, sector_name)] = industry.industry_id

    session.commit()
    print(f"[OK] Industries ensured: {len(industry_map)} industries in database")
    return industry_map


def ensure_psx_source_exists(session: Session) -> int:
    """
    Ensure PSX official source exists.
    Returns source_id.
    """
    existing = session.query(Source).filter_by(
        source_type=SourceType.PSX,
        source_name="PSX Official"
    ).first()

    if existing:
        return existing.source_id

    source = Source(
        source_type=SourceType.PSX,
        source_name="PSX Official",
        source_url="https://www.psx.com.pk",
        authority_level=AuthorityLevel.PRIMARY
    )
    session.add(source)
    session.commit()
    print(f"[OK] PSX source created: source_id={source.source_id}")
    return source.source_id


def ingest_companies(session: Session, sector_map: dict, industry_map: dict) -> int:
    """
    Ingest all PSX companies into security master.
    Returns count of companies ingested.
    """
    count = 0
    for company_data in PSX_COMPANIES:
        # Check if company already exists
        existing = session.query(Security).filter_by(ticker=company_data["ticker"]).first()
        if existing:
            print(f"  [--] {company_data['ticker']} already exists (security_id={existing.security_id})")
            count += 1
            continue

        # Create security record
        sector_name = company_data["sector"]
        industry_name = company_data["industry"]

        security = Security(
            ticker=company_data["ticker"],
            company_name=company_data["company_name"],
            legal_name=company_data.get("legal_name", company_data["company_name"]),
            sector_id=sector_map[sector_name],
            industry_id=industry_map[(industry_name, sector_name)],
            listing_date=datetime.strptime(company_data["listing_date"], "%Y-%m-%d").date(),
            fiscal_year_end=company_data["fiscal_year_end"],
            website=company_data.get("website"),
            psx_profile_url=company_data.get("psx_profile_url"),
            active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        session.add(security)
        session.flush()

        # Create company profile
        profile = CompanyProfile(
            security_id=security.security_id,
            description=f"{company_data['company_name']} is a {sector_name} sector company.",
            business_model=f"Operates in {industry_name} industry.",
            updated_at=datetime.utcnow(),
        )
        session.add(profile)

        count += 1
        print(f"  [OK] {company_data['ticker']}: {company_data['company_name']} (security_id={security.security_id})")

    session.commit()
    print(f"\n[OK] Companies ingested: {count} companies in database")
    return count


def verify_security_master(session: Session) -> dict:
    """
    Verify security master is complete and correct.
    Returns verification report.
    """
    total_securities = session.query(Security).count()
    total_sectors = session.query(Sector).count()
    total_industries = session.query(Industry).count()
    total_profiles = session.query(CompanyProfile).count()

    # Check for duplicates
    ticker_counts = session.query(Security.ticker).group_by(Security.ticker).all()
    duplicates = [t[0] for t in ticker_counts if session.query(Security).filter_by(ticker=t[0]).count() > 1]

    # Check all securities have profiles
    orphaned = total_securities - total_profiles

    report = {
        "total_securities": total_securities,
        "total_sectors": total_sectors,
        "total_industries": total_industries,
        "total_profiles": total_profiles,
        "duplicate_tickers": len(duplicates),
        "orphaned_securities": orphaned,
        "is_valid": len(duplicates) == 0 and orphaned == 0,
    }

    return report


def sprint_1_security_master():
    """
    Sprint 1: Security Master Implementation

    1. Create database tables
    2. Ensure sectors exist
    3. Ensure industries exist
    4. Ensure PSX source exists
    5. Ingest all PSX companies
    6. Verify data integrity
    """
    print("\n" + "="*70)
    print("SPRINT 1: SECURITY MASTER IMPLEMENTATION")
    print("="*70 + "\n")

    session = get_session()

    try:
        print("Step 1: Ensuring sectors exist...")
        sector_map = ensure_sectors_exist(session)
        print(f"  Sectors: {list(sector_map.keys())}\n")

        print("Step 2: Ensuring industries exist...")
        industry_map = ensure_industries_exist(session, sector_map)
        print(f"  Industries: {len(industry_map)}\n")

        print("Step 3: Ensuring PSX source exists...")
        psx_source_id = ensure_psx_source_exists(session)
        print()

        print("Step 4: Ingesting PSX companies...")
        count = ingest_companies(session, sector_map, industry_map)
        print()

        print("Step 5: Verifying security master...")
        report = verify_security_master(session)
        print(f"  Total securities: {report['total_securities']}")
        print(f"  Total sectors: {report['total_sectors']}")
        print(f"  Total industries: {report['total_industries']}")
        print(f"  Total profiles: {report['total_profiles']}")
        print(f"  Duplicate tickers: {report['duplicate_tickers']}")
        print(f"  Orphaned securities: {report['orphaned_securities']}")
        print(f"  Status: {'[OK] VALID' if report['is_valid'] else '[FAIL] INVALID'}\n")

        if report["is_valid"]:
            print("="*70)
            print("SPRINT 1 COMPLETE: Security Master is ready")
            print("="*70)
            return report
        else:
            print("⚠️ Verification failed! Fix issues before proceeding.")
            return report

    finally:
        session.close()


if __name__ == "__main__":
    # Initialize database
    from .database import init_db
    init_db()

    # Run Sprint 1
    report = sprint_1_security_master()
