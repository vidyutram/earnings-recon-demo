"""Seeded generator: builds internally consistent financials, then plants 10 anomalies.
Each anomaly is recorded in the answer key (never shown to the agent)."""
import argparse, json, random
from pathlib import Path

YEAR = 2025
QUARTERS = ["Q1", "Q2", "Q3", "Q4"]
CUSTOMERS = ["Northwind", "Contoso", "Globex", "Initech", "Umbrella", "Hooli"]
IS_LINES = ["revenue", "cogs", "gross_profit", "opex", "operating_income",
            "interest_expense", "pretax_income", "tax", "net_income"]


def generate(seed: int = 7):
    r = random.Random(seed)
    # distinct planted deltas so numeric matching can tell anomalies apart
    d_bs, d_ni, d_fy, d_gp, d_cash, d_led, d_c1, d_c2 = [k * 1000 for k in r.sample(range(12, 95), 8)]

    # ---- revenue ledger (source of truth for revenue) ----
    ledger, n = [], 1000
    for qi, q in enumerate(QUARTERS):
        for _ in range(6):
            n += 1
            ledger.append(dict(
                invoice_id=f"INV-{n}", customer=r.choice(CUSTOMERS),
                invoice_date=f"{YEAR}-{qi * 3 + r.randint(1, 3):02d}-{r.randint(1, 28):02d}",
                posted_quarter=q, amount=r.randint(40, 160) * 1000))
    dup_src = r.choice([x for x in ledger if x["posted_quarter"] == "Q1"])
    ledger.append(dict(dup_src))                                    # A8: duplicate invoice
    late = r.choice([x for x in ledger if x["posted_quarter"] == "Q3"])
    late["invoice_date"] = f"{YEAR}-10-{r.randint(2, 20):02d}"      # A7: Q4 invoice booked in Q3
    ledger.sort(key=lambda x: (QUARTERS.index(x["posted_quarter"]), x["invoice_date"]))

    # ---- income statement (consistent with ledger, incl. dup and late invoice) ----
    IS = {k: {} for k in IS_LINES}
    for q in QUARTERS:
        rev = sum(x["amount"] for x in ledger if x["posted_quarter"] == q)
        cogs = int(round(rev * r.uniform(0.55, 0.62), -3))
        gp = rev - cogs + (d_gp if q == "Q3" else 0)                # A4: Q3 GP miscalculated
        opex = r.randint(90, 140) * 1000
        opinc = gp - opex
        pretax = opinc - 12000
        tax = int(round(pretax * 0.21, -3))   # keep NI in whole thousands
        vals = dict(revenue=rev, cogs=cogs, gross_profit=gp, opex=opex, operating_income=opinc,
                    interest_expense=12000, pretax_income=pretax, tax=tax, net_income=pretax - tax)
        for k, v in vals.items():
            IS[k][q] = v
    for k in IS_LINES:
        IS[k]["FY"] = sum(IS[k][q] for q in QUARTERS)
    # chart data: what the "Net Income by Quarter" image draws. Two bars disagree with the table (A9, A10).
    cq = sorted(r.sample(QUARTERS, 2))
    plotted = {q: IS["net_income"][q] for q in QUARTERS}
    plotted[cq[0]] += d_c1
    plotted[cq[1]] += d_c2
    IS["revenue"]["FY"] += d_fy                                     # A3: FY != sum of quarters

    q2 = r.choice([x for x in ledger if x["posted_quarter"] == "Q2"])
    q2["amount"] += d_led                                           # A6: ledger Q2 != IS Q2

    # ---- cash flow ----
    ni_line = IS["net_income"]["FY"] + d_ni                         # A2: NI differs from IS
    wc, capex = -r.randint(20, 60) * 1000, -r.randint(200, 400) * 1000
    cff = -r.randint(50, 120) * 1000 - r.randint(30, 80) * 1000
    cfo = ni_line + 180000 + wc
    net = cfo + capex + cff
    end_cash = r.randint(900, 1400) * 1000
    CF = dict(net_income=ni_line, depreciation=180000, change_in_working_capital=wc,
              cash_from_operations=cfo, capex=capex, cash_from_investing=capex,
              cash_from_financing=cff, net_change_in_cash=net,
              beginning_cash=end_cash - net, ending_cash=end_cash)

    # ---- balance sheet (built balanced, then perturbed) ----
    cash = end_cash - d_cash                                        # A5: BS cash != CF ending cash
    ar, inv, ppe = (r.randint(300, 500) * 1000, r.randint(200, 400) * 1000, r.randint(1200, 1800) * 1000)
    ap, acc, debt = (r.randint(200, 350) * 1000, r.randint(100, 200) * 1000, r.randint(600, 900) * 1000)
    liab = ap + acc + debt
    equity = cash + ar + inv + ppe - liab                           # plug => balanced
    ar += d_bs                                                      # A1: assets no longer = L + E
    BS = dict(cash=cash, accounts_receivable=ar, inventory=inv, ppe_net=ppe,
              total_assets=cash + ar + inv + ppe, accounts_payable=ap, accrued_expenses=acc,
              long_term_debt=debt, total_liabilities=liab, common_stock=1_000_000,
              retained_earnings=equity - 1_000_000, total_equity=equity,
              total_liabilities_and_equity=liab + equity)

    f = lambda v: f"${v:,}"
    key = [
        dict(id="A1", title="Balance sheet does not balance", amount=d_bs, token=None,
             truth=f"Balance sheet does not balance: total assets exceed total liabilities and equity by {f(d_bs)}."),
        dict(id="A2", title="Net income differs between IS and cash flow", amount=d_ni, token=None,
             truth=f"Net income mismatch: the cash flow statement starts from net income {f(d_ni)} higher than the income statement."),
        dict(id="A3", title="FY revenue != sum of quarters", amount=d_fy, token=None,
             truth=f"FY revenue on the income statement is {f(d_fy)} higher than the sum of Q1-Q4 revenue."),
        dict(id="A4", title="Q3 gross profit miscalculated", amount=d_gp, token=None,
             truth=f"Q3 gross profit is overstated by {f(d_gp)} versus revenue minus COGS."),
        dict(id="A5", title="Cash: BS vs cash flow ending cash", amount=d_cash, token=None,
             truth=f"Cash mismatch: balance sheet cash is {f(d_cash)} lower than ending cash on the cash flow statement."),
        dict(id="A6", title="Ledger Q2 total != IS Q2 revenue", amount=d_led, token=None,
             truth=f"Revenue ledger total for Q2 is {f(d_led)} higher than Q2 revenue on the income statement."),
        dict(id="A7", title="Cutoff/timing: Q4 invoice booked in Q3", amount=None, token=late["invoice_id"],
             truth=f"Timing/cutoff error: invoice {late['invoice_id']} is dated {late['invoice_date']} (Q4) but posted to Q3 revenue."),
        dict(id="A8", title="Duplicate invoice in ledger", amount=None, token=dup_src["invoice_id"],
             truth=f"Duplicate invoice {dup_src['invoice_id']} appears twice in the Q1 ledger, overstating Q1 revenue."),
        dict(id="A9", title=f"Chart vs table: {cq[0]} net income", amount=d_c1, token=cq[0].lower(),
             amounts=[d_c1, plotted[cq[0]]],
             truth=f"Chart vs table: the Net Income by Quarter chart draws {cq[0]} at {f(plotted[cq[0]])}, "
                   f"but the income statement shows {f(IS['net_income'][cq[0]])} ({f(d_c1)} overstated)."),
        dict(id="A10", title=f"Chart vs table: {cq[1]} net income", amount=d_c2, token=cq[1].lower(),
             amounts=[d_c2, plotted[cq[1]]],
             truth=f"Chart vs table: the Net Income by Quarter chart draws {cq[1]} at {f(plotted[cq[1]])}, "
                   f"but the income statement shows {f(IS['net_income'][cq[1]])} ({f(d_c2)} overstated)."),
    ]
    data = dict(income_statement=IS, chart_net_income=plotted, balance_sheet=BS, cash_flow=CF, ledger=ledger)
    return data, key


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=7)
    a = ap.parse_args()
    data, key = generate(a.seed)
    Path("data.json").write_text(json.dumps(data, indent=2))
    Path("answer_key.json").write_text(json.dumps(key, indent=2))
    print(f"wrote data.json and answer_key.json (seed={a.seed}, {len(key)} anomalies)")
