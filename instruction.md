# Earnings Reconciliation (mini)
You are given a company's FY2025 dashboard: income statement (quarterly + FY), balance sheet,
cash flow statement, a revenue ledger and two chart images (PNG). Some figures exist only inside the images. Cross-reference them and find accounting inconsistencies.

## Output
A markdown list, one finding per bullet (`- ...`). Each finding must name the statement/line item,
the period, and the dollar amount of the discrepancy (or the invoice id for ledger issues).

## Scoring (deterministic)
`score = max(0, (matched - 0.5 * unmatched_findings) / total_anomalies)`
Total anomalies: 10. Each anomaly can be matched once. Padding the report with guesses lowers your score.
