"""Known and seed annual report URLs for FFC and EFERT.

This seeds the discovery process. Companies typically host reports at:
- /investor-relations/annual-reports/
- /ir/reports/
- /downloads/annual-reports/
- Direct URLs like: /reports/FFC_Annual_Report_2023.pdf

Source: Company IR sites verified manually or via robots.txt
"""

# Direct URLs for reports we know exist
KNOWN_REPORT_URLS = {
    "FFC": {
        # FFC typically at: https://www.fauji.com.pk/investor-relations/
        # or: https://www.fauji.com.pk/ar[YEAR].pdf
        # Actual URLs need to be discovered or manually provided
    },
    "EFERT": {
        # EFERT at: https://www.engrofert.com/investor-relations/
        # User confirmed: "reports for 2023, 2024 and 2025"
        # Typical pattern: /annual-reports/ or direct PDF
    },
}

# URL patterns to try (with {year} placeholder)
URL_PATTERNS = {
    "FFC": [
        "https://www.fauji.com.pk/ar{year}.pdf",
        "https://www.fauji.com.pk/reports/ar{year}.pdf",
        "https://www.fauji.com.pk/investor-relations/ar{year}.pdf",
        "https://www.fauji.com.pk/investor-relations/annual-reports/{year}/",
        "https://www.fauji.com.pk/downloads/ar{year}.pdf",
    ],
    "EFERT": [
        "https://www.engrofert.com/ar{year}.pdf",
        "https://www.engrofert.com/reports/ar{year}.pdf",
        "https://www.engrofert.com/investor-relations/ar{year}.pdf",
        "https://www.engrofert.com/investor-relations/annual-reports/{year}/",
        "https://www.engrofert.com/downloads/ar{year}.pdf",
    ],
}


def get_report_urls_to_try(company: str, years: list[int]) -> dict[int, list[str]]:
    """Get all report URL candidates to try for a company and years.

    Returns: {
        2023: ["https://...", "https://..."],
        2024: ["https://...", "https://..."],
    }
    """
    patterns = URL_PATTERNS.get(company, [])
    known = KNOWN_REPORT_URLS.get(company, {})

    urls_to_try = {}

    for year in years:
        candidates = []

        # Add known URLs first
        if year in known:
            candidates.append(known[year])

        # Try patterns
        for pattern in patterns:
            url = pattern.format(year=year)
            if url not in candidates:
                candidates.append(url)

        if candidates:
            urls_to_try[year] = candidates

    return urls_to_try
