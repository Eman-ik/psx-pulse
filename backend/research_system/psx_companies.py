"""
PSX Company Master Data

Core PSX companies with essential metadata.
This is the seed data for Security Master (Sprint 1).
In production, this would be fetched from PSX API or regulatory database.

Focus: 8 core tickers + major index constituents
"""

PSX_COMPANIES = [
    # Fertilizer Sector
    {
        "ticker": "FFC",
        "company_name": "Fauji Fertilizer Company Limited",
        "legal_name": "Fauji Fertilizer Company Limited",
        "sector": "Fertilizer",
        "industry": "Nitrogenous Fertilizer",
        "listing_date": "1977-06-01",
        "fiscal_year_end": "30-JUN",
        "website": "https://www.fauji.com.pk",
        "psx_profile_url": "https://www.psx.com.pk/psx-listed-companies/sectors/chemicals-and-pharmaceuticals/ffc",
    },
    {
        "ticker": "EFERT",
        "company_name": "Engro Fertilizers Limited",
        "legal_name": "Engro Fertilizers Limited",
        "sector": "Fertilizer",
        "industry": "Nitrogenous Fertilizer",
        "listing_date": "2001-04-02",
        "fiscal_year_end": "31-DEC",
        "website": "https://www.engro.com.pk",
        "psx_profile_url": "https://www.psx.com.pk/psx-listed-companies/sectors/chemicals-and-pharmaceuticals/efert",
    },
    {
        "ticker": "LUCK",
        "company_name": "Lucky Cement Limited",
        "legal_name": "Lucky Cement Limited",
        "sector": "Cement",
        "industry": "Portland Cement",
        "listing_date": "1998-08-10",
        "fiscal_year_end": "31-MAR",
        "website": "https://www.luckycement.com",
        "psx_profile_url": "https://www.psx.com.pk/psx-listed-companies/sectors/cement-sector/luck",
    },

    # Cement Sector
    {
        "ticker": "FCCL",
        "company_name": "Fauji Cement Company Limited",
        "legal_name": "Fauji Cement Company Limited",
        "sector": "Cement",
        "industry": "Portland Cement",
        "listing_date": "1993-02-08",
        "fiscal_year_end": "31-DEC",
        "website": "https://www.fauji.com.pk",
        "psx_profile_url": "https://www.psx.com.pk/psx-listed-companies/sectors/cement-sector/fccl",
    },
    {
        "ticker": "DGKC",
        "company_name": "D.G. Khan Cement Company Limited",
        "legal_name": "D.G. Khan Cement Company Limited",
        "sector": "Cement",
        "industry": "Portland Cement",
        "listing_date": "1997-01-13",
        "fiscal_year_end": "31-DEC",
        "website": "https://www.dgkhan.com.pk",
        "psx_profile_url": "https://www.psx.com.pk/psx-listed-companies/sectors/cement-sector/dgkc",
    },

    # Banking Sector
    {
        "ticker": "MCB",
        "company_name": "MCB Bank Limited",
        "legal_name": "MCB Bank Limited",
        "sector": "Banking",
        "industry": "Commercial Banking",
        "listing_date": "1992-01-06",
        "fiscal_year_end": "31-DEC",
        "website": "https://www.mcb.com.pk",
        "psx_profile_url": "https://www.psx.com.pk/psx-listed-companies/sectors/banking-sector/mcb",
    },

    # Oil & Gas Exploration & Production
    {
        "ticker": "OGDC",
        "company_name": "Oil and Gas Development Company Limited",
        "legal_name": "Oil and Gas Development Company Limited",
        "sector": "E&P",
        "industry": "Oil & Gas Exploration & Production",
        "listing_date": "1991-11-11",
        "fiscal_year_end": "30-JUN",
        "website": "https://www.ogdcl.com",
        "psx_profile_url": "https://www.psx.com.pk/psx-listed-companies/sectors/exploration-and-production/ogdc",
    },

    # Power Sector
    {
        "ticker": "PPL",
        "company_name": "Pakistan Petroleum Limited",
        "legal_name": "Pakistan Petroleum Limited",
        "sector": "E&P",
        "industry": "Oil & Gas Exploration & Production",
        "listing_date": "1989-12-18",
        "fiscal_year_end": "31-DEC",
        "website": "https://www.pappl.com",
        "psx_profile_url": "https://www.psx.com.pk/psx-listed-companies/sectors/exploration-and-production/ppl",
    },

    # Insurance Sector
    {
        "ticker": "UBL",
        "company_name": "United Breweries Limited",
        "legal_name": "United Breweries Limited",
        "sector": "Miscellaneous",
        "industry": "Beverages",
        "listing_date": "1999-01-01",
        "fiscal_year_end": "31-DEC",
        "website": "https://www.ubl.com",
        "psx_profile_url": "https://www.psx.com.pk/psx-listed-companies/sectors/miscellaneous/ubl",
    },

    # Additional Cement Companies
    {
        "ticker": "MLCF",
        "company_name": "Maple Leaf Cement Factory Limited",
        "legal_name": "Maple Leaf Cement Factory Limited",
        "sector": "Cement",
        "industry": "Portland Cement",
        "listing_date": "1990-06-01",
        "fiscal_year_end": "31-MAR",
        "website": "https://www.mapleleafcement.com",
        "psx_profile_url": "https://www.psx.com.pk/psx-listed-companies/sectors/cement-sector/mlcf",
    },

    # Additional E&P
    {
        "ticker": "PIOC",
        "company_name": "Pakistan Oilfields Limited",
        "legal_name": "Pakistan Oilfields Limited",
        "sector": "E&P",
        "industry": "Oil & Gas Exploration & Production",
        "listing_date": "1988-04-18",
        "fiscal_year_end": "31-DEC",
        "website": "https://www.pioc.com.pk",
        "psx_profile_url": "https://www.psx.com.pk/psx-listed-companies/sectors/exploration-and-production/pioc",
    },

    # Banking
    {
        "ticker": "HBL",
        "company_name": "Habib Bank Limited",
        "legal_name": "Habib Bank Limited",
        "sector": "Banking",
        "industry": "Commercial Banking",
        "listing_date": "1991-03-18",
        "fiscal_year_end": "31-DEC",
        "website": "https://www.hbl.com",
        "psx_profile_url": "https://www.psx.com.pk/psx-listed-companies/sectors/banking-sector/hbl",
    },

    # Fertilizer
    {
        "ticker": "FATIMA",
        "company_name": "Fatima Fertilizer Company Limited",
        "legal_name": "Fatima Fertilizer Company Limited",
        "sector": "Fertilizer",
        "industry": "Nitrogenous Fertilizer",
        "listing_date": "2003-01-20",
        "fiscal_year_end": "31-DEC",
        "website": "https://www.ffl.com.pk",
        "psx_profile_url": "https://www.psx.com.pk/psx-listed-companies/sectors/chemicals-and-pharmaceuticals/fatima",
    },
]

# Quick validation
print(f"PSX Companies loaded: {len(PSX_COMPANIES)}")
print(f"Unique tickers: {len(set(c['ticker'] for c in PSX_COMPANIES))}")
print(f"Sectors: {set(c['sector'] for c in PSX_COMPANIES)}")
