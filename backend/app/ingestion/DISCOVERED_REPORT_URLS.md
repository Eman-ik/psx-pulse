# Discovered Annual Report URLs

## Source: Official IR Sites (Oct 2026)
Discovered via automated JS extraction from official investor relations pages.

### FFC (Fauji Fertilizer Company Limited)

**IR Page:** https://ffc.com.pk/investor-relations/reports/

| Year | URL | Status |
|------|-----|--------|
| 2025 | https://ffc.com.pk/wp-content/uploads/2026/03/FFC-AR-2025-2.pdf | ✓ Available |
| 2024 | https://ffc.com.pk/wp-content/uploads/2025/03/FFC-AR-2024.pdf | ✓ Available |
| 2023 | https://ffc.com.pk/wp-content/uploads/2024/11/FFC-Annual-Integrated-Report-2023_a.pdf | ✓ Available |
| 2022 | https://ffc.com.pk/wp-content/uploads/2024/11/FFC-AR-2022-2.pdf | ✓ Available |

### EFERT (Engro Fertilizers Limited)

**IR Page:** https://www.engrofertilizers.com/investments/

| Year | URL | Status |
|------|-----|--------|
| 2025 | https://www.engrofertilizers.com/themes/engro/documents/Engro-Fertilizers-Annual-Report-2025.pdf | ✓ Available |
| 2024 | https://www.engrofertilizers.com/themes/engro/documents/efert-annual-report-2024.pdf | ✓ Available |
| 2023 | https://www.engrofertilizers.com/themes/engro/documents/EFERT_Annual_Report_2023_Final.pdf | ✓ Available |
| 2022 | https://www.engrofertilizers.com/themes/engro/documents/EFERT-Annual-Report-2022.pdf | ✓ Available |

## Next Steps

### Phase 1: Verify Accessibility
- [ ] Download 2024 & 2025 reports from both companies
- [ ] Confirm file size, PDF magic bytes, and readability
- [ ] Check for extraction blockers (encrypted, scanned images, etc)

### Phase 2: Run Extractor
- [ ] Test MetricExtractor on FFC-AR-2025.pdf
- [ ] Test MetricExtractor on EFERT-Annual-Report-2025.pdf
- [ ] Log what extracts successfully vs what fails
- [ ] Identify statement types (IS, BS, CF) and layouts

### Phase 3: Build Fixtures
- [ ] For each report, extract expected metric values from PDF manually
- [ ] Create test fixtures with (input_pdf, expected_metrics_dict)
- [ ] Document extraction accuracy baseline

### Phase 4: Document Gaps
- [ ] Identify metrics that fail extraction
- [ ] Categorize failures: layout changes, metric naming variance, calculation complexity
- [ ] Prioritize which failures need fallback strategies

### Phase 5: Implement Fallbacks (if needed)
- [ ] Statement-aware parsing (detect statement type first)
- [ ] Column-position-invariant extraction (don't assume fixed positions)
- [ ] Metric alias mapping (urea vs urea production, etc)
