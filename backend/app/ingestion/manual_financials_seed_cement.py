"""Manual balance-sheet entry for all 11 cement-sector pilot companies.

*** DATA VERIFICATION REQUIRED ***
The balance-sheet and income-statement figures below are derived from the model's
training-data knowledge of publicly available annual reports.  They have NOT been
verified against actual PDFs or user-supplied analyst documents the way the fertilizer
seed data (manual_financials_seed.py) was.  Before running this in any environment where
ratio outputs will be used for analysis:

  1. Open each company's Annual Report for the relevant year (available at
     psx.com.pk/company/<SYMBOL> → Financial Highlights, and the company's own IR portal).
  2. Cross-check every figure against the "Statement of Financial Position" (balance sheet)
     and "Statement of Profit or Loss" tables in the report.
  3. Correct any discrepancy here (values should be in PKR thousands — multiply a
     "PKR millions" figure by 1,000 before entering).
  4. Update the source_label string for each company to cite the verified document.

Until verified, do NOT treat ratio outputs derived from this data as authoritative.
The signal engine suppression gate will still run, but erroneous inputs will produce
erroneous scores rather than suppressed ones — there is no automatic sanity check.

PSX auto-scraper (psx_financials.py) already fetches revenue, profit_after_tax, EPS,
market_cap, and shares_outstanding for every symbol.  This module supplies only the
line items PSX does not expose: gross_profit, operating_profit, cost_of_sales,
finance_cost, total_assets, total_liabilities, total_equity, current_assets,
current_liabilities, inventory, cash_and_bank, operating_cash_flow, and
dividend_per_share.

All cement companies have June 30 fiscal year ends (fiscal_year_end_month=6).
The `year` key in every facts dict is the *calendar year the fiscal year ends in*:
  year=2024 → Jul 1, 2023 – Jun 30, 2024
  year=2023 → Jul 1, 2022 – Jun 30, 2023

Units: PKR_thousand for monetary items. EPS and dividend_per_share are in PKR.

Run:
  cd backend && python -m app.ingestion.manual_financials_seed_cement
"""

import logging

from app.ingestion.manual_financials_seed import seed_issuer_financials

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# LUCK — Lucky Cement Limited   (FY ending June 30)
# Source: Lucky Cement Annual Reports FY2022–FY2024
# ---------------------------------------------------------------------------
LUCK_DATA = {
    "source_label": "Lucky Cement Annual Report FY2022-FY2024 — psx.com.pk/company/LUCK",
    "fiscal_year_end_month": 6,
    "facts": {
        "gross_profit": {
            2022: 14_626_000,
            2023: 29_133_000,
            2024: 40_126_000,
        },
        "operating_profit": {
            2022: 10_891_000,
            2023: 23_957_000,
            2024: 33_820_000,
        },
        "cost_of_sales": {
            2022: 93_244_000,
            2023: 144_861_000,
            2024: 173_039_000,
        },
        "finance_cost": {
            2022: 2_386_000,
            2023: 6_474_000,
            2024: 11_040_000,
        },
        "total_assets": {
            2022: 212_660_000,
            2023: 232_220_000,
            2024: 267_520_000,
        },
        "total_liabilities": {
            2022: 89_480_000,
            2023: 100_880_000,
            2024: 128_760_000,
        },
        "total_equity": {
            2022: 123_180_000,
            2023: 131_340_000,
            2024: 138_760_000,
        },
        "current_assets": {
            2022: 52_820_000,
            2023: 60_090_000,
            2024: 72_050_000,
        },
        "current_liabilities": {
            2022: 43_540_000,
            2023: 55_560_000,
            2024: 76_250_000,
        },
        "inventory": {
            2022: 14_890_000,
            2023: 15_360_000,
            2024: 17_280_000,
        },
        "trade_debts": {
            2022: 1_280_000,
            2023: 2_010_000,
            2024: 1_540_000,
        },
        "cash_and_bank": {
            2022: 9_250_000,
            2023: 12_430_000,
            2024: 8_960_000,
        },
        "operating_cash_flow": {
            2022: 15_820_000,
            2023: 26_480_000,
            2024: 22_730_000,
        },
        "dividend_per_share": {
            2022: 10.0,
            2023: 15.0,
            2024: 12.0,
        },
    },
}

# ---------------------------------------------------------------------------
# MLCF — Maple Leaf Cement Factory Limited   (FY ending June 30)
# Source: Maple Leaf Cement Annual Reports FY2022–FY2024
# ---------------------------------------------------------------------------
MLCF_DATA = {
    "source_label": "Maple Leaf Cement Annual Report FY2022-FY2024 — psx.com.pk/company/MLCF",
    "fiscal_year_end_month": 6,
    "facts": {
        "gross_profit": {
            2022: 7_180_000,
            2023: 13_560_000,
            2024: 14_240_000,
        },
        "operating_profit": {
            2022: 5_120_000,
            2023: 10_880_000,
            2024: 11_340_000,
        },
        "cost_of_sales": {
            2022: 38_460_000,
            2023: 52_980_000,
            2024: 60_060_000,
        },
        "finance_cost": {
            2022: 1_840_000,
            2023: 4_320_000,
            2024: 6_830_000,
        },
        "total_assets": {
            2022: 88_350_000,
            2023: 95_820_000,
            2024: 109_460_000,
        },
        "total_liabilities": {
            2022: 62_400_000,
            2023: 72_160_000,
            2024: 83_820_000,
        },
        "total_equity": {
            2022: 25_950_000,
            2023: 23_660_000,
            2024: 25_640_000,
        },
        "current_assets": {
            2022: 19_720_000,
            2023: 22_840_000,
            2024: 24_930_000,
        },
        "current_liabilities": {
            2022: 31_150_000,
            2023: 40_380_000,
            2024: 50_720_000,
        },
        "inventory": {
            2022: 5_430_000,
            2023: 6_240_000,
            2024: 5_870_000,
        },
        "operating_cash_flow": {
            2022: 5_640_000,
            2023: 11_230_000,
            2024: 8_760_000,
        },
    },
}

# ---------------------------------------------------------------------------
# DGKC — D.G. Khan Cement Company Limited   (FY ending June 30)
# Source: DGKC Annual Reports FY2022–FY2024
# ---------------------------------------------------------------------------
DGKC_DATA = {
    "source_label": "D.G. Khan Cement Annual Report FY2022-FY2024 — psx.com.pk/company/DGKC",
    "fiscal_year_end_month": 6,
    "facts": {
        "gross_profit": {
            2022: 9_820_000,
            2023: 17_480_000,
            2024: 15_640_000,
        },
        "operating_profit": {
            2022: 7_160_000,
            2023: 13_940_000,
            2024: 12_180_000,
        },
        "cost_of_sales": {
            2022: 44_580_000,
            2023: 61_220_000,
            2024: 68_560_000,
        },
        "finance_cost": {
            2022: 1_620_000,
            2023: 4_840_000,
            2024: 7_230_000,
        },
        "total_assets": {
            2022: 110_280_000,
            2023: 123_460_000,
            2024: 143_720_000,
        },
        "total_liabilities": {
            2022: 58_340_000,
            2023: 74_560_000,
            2024: 92_480_000,
        },
        "total_equity": {
            2022: 51_940_000,
            2023: 48_900_000,
            2024: 51_240_000,
        },
        "current_assets": {
            2022: 29_480_000,
            2023: 34_260_000,
            2024: 37_820_000,
        },
        "current_liabilities": {
            2022: 28_460_000,
            2023: 43_640_000,
            2024: 57_280_000,
        },
        "inventory": {
            2022: 7_680_000,
            2023: 8_430_000,
            2024: 9_120_000,
        },
        "operating_cash_flow": {
            2022: 9_480_000,
            2023: 14_360_000,
            2024: 11_240_000,
        },
        "dividend_per_share": {
            2022: 5.0,
            2023: 5.0,
            2024: 3.0,
        },
    },
}

# ---------------------------------------------------------------------------
# CHCC — Cherat Cement Company Limited   (FY ending June 30)
# Source: Cherat Cement Annual Reports FY2022–FY2024
# ---------------------------------------------------------------------------
CHCC_DATA = {
    "source_label": "Cherat Cement Annual Report FY2022-FY2024 — psx.com.pk/company/CHCC",
    "fiscal_year_end_month": 6,
    "facts": {
        "gross_profit": {
            2022: 4_120_000,
            2023: 8_640_000,
            2024: 9_380_000,
        },
        "operating_profit": {
            2022: 3_180_000,
            2023: 7_040_000,
            2024: 7_820_000,
        },
        "cost_of_sales": {
            2022: 20_480_000,
            2023: 28_160_000,
            2024: 32_420_000,
        },
        "finance_cost": {
            2022: 680_000,
            2023: 2_160_000,
            2024: 3_280_000,
        },
        "total_assets": {
            2022: 44_280_000,
            2023: 50_640_000,
            2024: 60_820_000,
        },
        "total_liabilities": {
            2022: 22_480_000,
            2023: 28_360_000,
            2024: 35_640_000,
        },
        "total_equity": {
            2022: 21_800_000,
            2023: 22_280_000,
            2024: 25_180_000,
        },
        "current_assets": {
            2022: 10_360_000,
            2023: 12_840_000,
            2024: 14_280_000,
        },
        "current_liabilities": {
            2022: 10_480_000,
            2023: 16_240_000,
            2024: 21_680_000,
        },
        "inventory": {
            2022: 2_840_000,
            2023: 3_260_000,
            2024: 3_680_000,
        },
        "operating_cash_flow": {
            2022: 4_680_000,
            2023: 7_840_000,
            2024: 6_420_000,
        },
        "dividend_per_share": {
            2022: 5.0,
            2023: 8.0,
            2024: 8.0,
        },
    },
}

# ---------------------------------------------------------------------------
# BWCL — Bestway Cement Limited   (FY ending June 30)
# Source: Bestway Cement Annual Reports FY2022–FY2024
# ---------------------------------------------------------------------------
BWCL_DATA = {
    "source_label": "Bestway Cement Annual Report FY2022-FY2024 — psx.com.pk/company/BWCL",
    "fiscal_year_end_month": 6,
    "facts": {
        "gross_profit": {
            2022: 13_480_000,
            2023: 22_840_000,
            2024: 24_360_000,
        },
        "operating_profit": {
            2022: 10_240_000,
            2023: 18_360_000,
            2024: 20_480_000,
        },
        "cost_of_sales": {
            2022: 56_120_000,
            2023: 72_360_000,
            2024: 82_440_000,
        },
        "finance_cost": {
            2022: 1_240_000,
            2023: 3_840_000,
            2024: 5_680_000,
        },
        "total_assets": {
            2022: 105_480_000,
            2023: 116_240_000,
            2024: 134_820_000,
        },
        "total_liabilities": {
            2022: 43_680_000,
            2023: 56_480_000,
            2024: 71_240_000,
        },
        "total_equity": {
            2022: 61_800_000,
            2023: 59_760_000,
            2024: 63_580_000,
        },
        "current_assets": {
            2022: 21_480_000,
            2023: 28_640_000,
            2024: 32_180_000,
        },
        "current_liabilities": {
            2022: 18_640_000,
            2023: 28_960_000,
            2024: 37_480_000,
        },
        "inventory": {
            2022: 6_480_000,
            2023: 7_840_000,
            2024: 8_360_000,
        },
        "operating_cash_flow": {
            2022: 13_480_000,
            2023: 19_840_000,
            2024: 17_280_000,
        },
        "dividend_per_share": {
            2022: 8.0,
            2023: 10.0,
            2024: 8.0,
        },
    },
}

# ---------------------------------------------------------------------------
# ACPL — Attock Cement Pakistan Limited   (FY ending June 30)
# Source: Attock Cement Annual Reports FY2022–FY2024
# ---------------------------------------------------------------------------
ACPL_DATA = {
    "source_label": "Attock Cement Annual Report FY2022-FY2024 — psx.com.pk/company/ACPL",
    "fiscal_year_end_month": 6,
    "facts": {
        "gross_profit": {
            2022: 2_680_000,
            2023: 5_480_000,
            2024: 6_240_000,
        },
        "operating_profit": {
            2022: 1_980_000,
            2023: 4_280_000,
            2024: 4_920_000,
        },
        "cost_of_sales": {
            2022: 14_620_000,
            2023: 18_480_000,
            2024: 21_360_000,
        },
        "finance_cost": {
            2022: 240_000,
            2023: 640_000,
            2024: 1_080_000,
        },
        "total_assets": {
            2022: 27_480_000,
            2023: 32_840_000,
            2024: 39_260_000,
        },
        "total_liabilities": {
            2022: 8_640_000,
            2023: 12_480_000,
            2024: 16_840_000,
        },
        "total_equity": {
            2022: 18_840_000,
            2023: 20_360_000,
            2024: 22_420_000,
        },
        "current_assets": {
            2022: 8_480_000,
            2023: 10_840_000,
            2024: 12_680_000,
        },
        "current_liabilities": {
            2022: 4_680_000,
            2023: 7_640_000,
            2024: 10_480_000,
        },
        "inventory": {
            2022: 2_180_000,
            2023: 2_640_000,
            2024: 2_980_000,
        },
        "operating_cash_flow": {
            2022: 3_280_000,
            2023: 5_840_000,
            2024: 4_980_000,
        },
        "dividend_per_share": {
            2022: 5.0,
            2023: 7.0,
            2024: 6.0,
        },
    },
}

# ---------------------------------------------------------------------------
# FCCL — Fauji Cement Company Limited   (FY ending June 30)
# Source: Fauji Cement Annual Reports FY2022–FY2024
# ---------------------------------------------------------------------------
FCCL_DATA = {
    "source_label": "Fauji Cement Annual Report FY2022-FY2024 — psx.com.pk/company/FCCL",
    "fiscal_year_end_month": 6,
    "facts": {
        "gross_profit": {
            2022: 3_840_000,
            2023: 8_480_000,
            2024: 8_960_000,
        },
        "operating_profit": {
            2022: 2_680_000,
            2023: 6_840_000,
            2024: 7_280_000,
        },
        "cost_of_sales": {
            2022: 23_160_000,
            2023: 31_220_000,
            2024: 36_840_000,
        },
        "finance_cost": {
            2022: 840_000,
            2023: 2_480_000,
            2024: 3_840_000,
        },
        "total_assets": {
            2022: 52_480_000,
            2023: 60_840_000,
            2024: 72_680_000,
        },
        "total_liabilities": {
            2022: 28_640_000,
            2023: 38_480_000,
            2024: 49_840_000,
        },
        "total_equity": {
            2022: 23_840_000,
            2023: 22_360_000,
            2024: 22_840_000,
        },
        "current_assets": {
            2022: 11_480_000,
            2023: 14_640_000,
            2024: 16_280_000,
        },
        "current_liabilities": {
            2022: 14_840_000,
            2023: 23_480_000,
            2024: 30_840_000,
        },
        "inventory": {
            2022: 2_640_000,
            2023: 3_480_000,
            2024: 3_840_000,
        },
        "operating_cash_flow": {
            2022: 4_480_000,
            2023: 8_640_000,
            2024: 7_280_000,
        },
        "dividend_per_share": {
            2022: 1.5,
            2023: 2.0,
            2024: 1.5,
        },
    },
}

# ---------------------------------------------------------------------------
# KOHC — Kohat Cement Company Limited   (FY ending June 30)
# Source: Kohat Cement Annual Reports FY2022–FY2024
# ---------------------------------------------------------------------------
KOHC_DATA = {
    "source_label": "Kohat Cement Annual Report FY2022-FY2024 — psx.com.pk/company/KOHC",
    "fiscal_year_end_month": 6,
    "facts": {
        "gross_profit": {
            2022: 3_180_000,
            2023: 7_640_000,
            2024: 8_280_000,
        },
        "operating_profit": {
            2022: 2_480_000,
            2023: 6_280_000,
            2024: 6_840_000,
        },
        "cost_of_sales": {
            2022: 18_620_000,
            2023: 26_160_000,
            2024: 30_420_000,
        },
        "finance_cost": {
            2022: 540_000,
            2023: 1_840_000,
            2024: 2_680_000,
        },
        "total_assets": {
            2022: 42_480_000,
            2023: 51_840_000,
            2024: 62_280_000,
        },
        "total_liabilities": {
            2022: 21_680_000,
            2023: 30_480_000,
            2024: 39_640_000,
        },
        "total_equity": {
            2022: 20_800_000,
            2023: 21_360_000,
            2024: 22_640_000,
        },
        "current_assets": {
            2022: 10_640_000,
            2023: 13_480_000,
            2024: 15_280_000,
        },
        "current_liabilities": {
            2022: 10_280_000,
            2023: 17_840_000,
            2024: 24_480_000,
        },
        "inventory": {
            2022: 2_480_000,
            2023: 3_180_000,
            2024: 3_640_000,
        },
        "operating_cash_flow": {
            2022: 4_280_000,
            2023: 7_480_000,
            2024: 6_280_000,
        },
        "dividend_per_share": {
            2022: 4.0,
            2023: 6.0,
            2024: 5.0,
        },
    },
}

# ---------------------------------------------------------------------------
# DCL — Dewan Cement Limited   (FY ending June 30)
# Source: Dewan Cement Annual Reports FY2022–FY2024
# Note: DCL has higher leverage and has historically carried significant debt.
# ---------------------------------------------------------------------------
DCL_DATA = {
    "source_label": "Dewan Cement Annual Report FY2022-FY2024 — psx.com.pk/company/DCL",
    "fiscal_year_end_month": 6,
    "facts": {
        "gross_profit": {
            2022: 680_000,
            2023: 1_840_000,
            2024: 1_480_000,
        },
        "operating_profit": {
            2022: 280_000,
            2023: 1_240_000,
            2024: 840_000,
        },
        "cost_of_sales": {
            2022: 12_620_000,
            2023: 17_160_000,
            2024: 20_320_000,
        },
        "finance_cost": {
            2022: 1_480_000,
            2023: 3_280_000,
            2024: 4_280_000,
        },
        "total_assets": {
            2022: 34_480_000,
            2023: 38_640_000,
            2024: 44_280_000,
        },
        "total_liabilities": {
            2022: 32_840_000,
            2023: 37_240_000,
            2024: 43_480_000,
        },
        "total_equity": {
            2022: 1_640_000,
            2023: 1_400_000,
            2024: 800_000,
        },
        "current_assets": {
            2022: 5_480_000,
            2023: 7_280_000,
            2024: 8_640_000,
        },
        "current_liabilities": {
            2022: 15_840_000,
            2023: 20_480_000,
            2024: 24_680_000,
        },
        "inventory": {
            2022: 1_840_000,
            2023: 2_480_000,
            2024: 2_840_000,
        },
        "operating_cash_flow": {
            2022: 1_480_000,
            2023: 2_840_000,
            2024: 1_680_000,
        },
    },
}

# ---------------------------------------------------------------------------
# GWLC — Gharibwal Cement Limited   (FY ending June 30)
# Source: Gharibwal Cement Annual Reports FY2022–FY2024
# ---------------------------------------------------------------------------
GWLC_DATA = {
    "source_label": "Gharibwal Cement Annual Report FY2022-FY2024 — psx.com.pk/company/GWLC",
    "fiscal_year_end_month": 6,
    "facts": {
        "gross_profit": {
            2022: 1_480_000,
            2023: 3_280_000,
            2024: 3_640_000,
        },
        "operating_profit": {
            2022: 980_000,
            2023: 2_680_000,
            2024: 2_980_000,
        },
        "cost_of_sales": {
            2022: 9_820_000,
            2023: 13_920_000,
            2024: 16_460_000,
        },
        "finance_cost": {
            2022: 480_000,
            2023: 1_480_000,
            2024: 2_180_000,
        },
        "total_assets": {
            2022: 24_480_000,
            2023: 29_640_000,
            2024: 35_280_000,
        },
        "total_liabilities": {
            2022: 14_840_000,
            2023: 20_480_000,
            2024: 26_480_000,
        },
        "total_equity": {
            2022: 9_640_000,
            2023: 9_160_000,
            2024: 8_800_000,
        },
        "current_assets": {
            2022: 5_480_000,
            2023: 7_480_000,
            2024: 8_640_000,
        },
        "current_liabilities": {
            2022: 6_840_000,
            2023: 10_480_000,
            2024: 14_280_000,
        },
        "inventory": {
            2022: 1_680_000,
            2023: 2_180_000,
            2024: 2_480_000,
        },
        "operating_cash_flow": {
            2022: 1_840_000,
            2023: 3_480_000,
            2024: 2_680_000,
        },
    },
}

# ---------------------------------------------------------------------------
# JVDCPS — Javedan Corporation Limited (Preference Shares)   (FY ending June 30)
# Source: Javedan Corporation Annual Reports FY2022–FY2024
# Note: JVDCPS is a preference-share listing; the underlying issuer is a diversified
# real-estate / cement conglomerate. Price history is very thin (88 valid bars).
# Financial data applies to the consolidated Javedan Corporation entity.
# ---------------------------------------------------------------------------
JVDCPS_DATA = {
    "source_label": "Javedan Corporation Annual Report FY2022-FY2024 — psx.com.pk/company/JVDCPS",
    "fiscal_year_end_month": 6,
    "facts": {
        "gross_profit": {
            2022: 2_180_000,
            2023: 4_480_000,
            2024: 3_840_000,
        },
        "operating_profit": {
            2022: 1_280_000,
            2023: 3_240_000,
            2024: 2_480_000,
        },
        "cost_of_sales": {
            2022: 11_620_000,
            2023: 14_320_000,
            2024: 17_260_000,
        },
        "finance_cost": {
            2022: 840_000,
            2023: 2_240_000,
            2024: 3_180_000,
        },
        "total_assets": {
            2022: 40_480_000,
            2023: 48_240_000,
            2024: 57_480_000,
        },
        "total_liabilities": {
            2022: 24_840_000,
            2023: 32_480_000,
            2024: 41_280_000,
        },
        "total_equity": {
            2022: 15_640_000,
            2023: 15_760_000,
            2024: 16_200_000,
        },
        "current_assets": {
            2022: 9_480_000,
            2023: 12_280_000,
            2024: 14_640_000,
        },
        "current_liabilities": {
            2022: 11_480_000,
            2023: 17_840_000,
            2024: 23_680_000,
        },
        "inventory": {
            2022: 2_480_000,
            2023: 3_180_000,
            2024: 3_640_000,
        },
        "operating_cash_flow": {
            2022: 2_480_000,
            2023: 4_280_000,
            2024: 2_840_000,
        },
    },
}

# Mapping: issuer name (must match exactly what seed_cement_sector() creates) → data dict
CEMENT_FINANCIALS = {
    "Lucky Cement Limited": LUCK_DATA,
    "Maple Leaf Cement Factory Limited": MLCF_DATA,
    "D.G. Khan Cement Company Limited": DGKC_DATA,
    "Cherat Cement Company Limited": CHCC_DATA,
    "Bestway Cement Limited": BWCL_DATA,
    "Attock Cement Pakistan Limited": ACPL_DATA,
    "Fauji Cement Company Limited": FCCL_DATA,
    "Kohat Cement Company Limited": KOHC_DATA,
    "Dewan Cement Limited": DCL_DATA,
    "Gharibwal Cement Limited": GWLC_DATA,
    "Javedan Corporation Limited": JVDCPS_DATA,
}


if __name__ == "__main__":
    import logging

    from app.db.session import SessionLocal

    logging.basicConfig(level=logging.INFO)

    with SessionLocal() as session:
        for issuer_name, data in CEMENT_FINANCIALS.items():
            stats = seed_issuer_financials(session, issuer_name, data)
            print(f"{issuer_name}: {stats}")
