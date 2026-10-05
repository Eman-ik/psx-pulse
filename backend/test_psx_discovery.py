#!/usr/bin/env python3
"""Test PSX discovery mechanism."""

import httpx
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) psx-fertilizer/0.1"}

url = "https://dps.psx.com.pk/company/FFC"
print(f"Fetching {url}...")

try:
    response = httpx.get(url, headers=HEADERS, timeout=20)
    print(f"Status: {response.status_code}\n")

    soup = BeautifulSoup(response.text, "lxml")

    # Look for announcements section
    section = soup.find("div", id="announcements")
    if section:
        print("[OK] Found announcements section")
        tables = section.find_all("table")
        print(f"  Tables: {len(tables)}")

        if tables:
            # Inspect first table
            first_table = tables[0]
            rows = first_table.find_all("tr")
            print(f"  Rows in first table: {len(rows)}")

            # Show first 3 rows
            for i, row in enumerate(rows[:3]):
                print(f"\n  Row {i}:")
                cells = row.find_all(["td", "th"])
                for j, cell in enumerate(cells):
                    text = cell.get_text(strip=True)[:60]
                    link = cell.find("a")
                    if link:
                        href = link.get("href", "")[:100]
                        # Get all attributes
                        attrs = {k: str(v)[:80] for k, v in link.attrs.items() if k != 'href'}
                        print(f"    Col {j}: {text}")
                        print(f"           href: {href}")
                        if attrs:
                            print(f"           attrs: {attrs}")
                    else:
                        print(f"    Col {j}: {text}")
    else:
        print("[FAIL] No announcements div found")

        # Look for any tbody with tables
        all_tables = soup.find_all("table")
        print(f"\nTotal tables on page: {len(all_tables)}")

        for i, table in enumerate(all_tables[:2]):
            rows = table.find_all("tr")
            print(f"\nTable {i}: {len(rows)} rows")
            for row in rows[:2]:
                print(f"\n  Row HTML:")
                print(f"    {str(row)[:300]}")

except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
