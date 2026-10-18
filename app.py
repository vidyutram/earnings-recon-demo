import os
import pandas as pd
import streamlit as st
import nop, oracle
from generate_data import generate, QUARTERS
from grade import grade
from charts import render_all

st.set_page_config(page_title="Earnings Reconciliation Demo", layout="wide")
st.title("Earnings Reconciliation: mini benchmark demo")
st.caption("Rebuilt miniature of the task type I designed. Synthetic data, not the original project.")

seed = int(st.sidebar.number_input("Seed", value=7, step=1))
data, key = generate(seed)
IS, BS, CF = data["income_statement"], data["balance_sheet"], data["cash_flow"]
ledger = pd.DataFrame(data["ledger"])
imgs = render_all(data)
usd = lambda df: df.style.format("{:,.0f}")

t1, t2, t3, t4, t7, t5, t6 = st.tabs(["Income statement", "Balance sheet", "Cash flow", "Revenue ledger", "Charts (images)",
                                  "Grade a report", "Oracle / NOP checks"])
with t1:
    st.dataframe(usd(pd.DataFrame(IS).T[QUARTERS + ["FY"]]))
with t2:
    st.dataframe(usd(pd.DataFrame({"USD": BS})))
with t3:
    st.dataframe(usd(pd.DataFrame({"USD": CF})))
with t4:
    q = st.selectbox("Filter quarter", ["All"] + QUARTERS)
    st.dataframe(ledger if q == "All" else ledger[ledger.posted_quarter == q])

with t7:
    st.caption("Plotted values exist only in these images. A text-only agent cannot find the chart anomalies.")
    c1, c2 = st.columns(2)
    c1.image(imgs["net_income_by_quarter.png"]); c2.image(imgs["margins.png"])

with t5:
    st.write("Paste an agent's report (one finding per `-` bullet).")
    report = st.text_area("Report", height=220)
    mode = st.radio("Matcher", ["Rules (no API key)", "Gemini judge (optional)"], horizontal=True)
    ask = None
    if mode.startswith("Gemini"):
        k = st.text_input("Gemini API key (kept in memory only; or set GEMINI_API_KEY)", type="password")
        try:
            from matcher import make_gemini_ask
            ask = make_gemini_ask(k or os.getenv("GEMINI_API_KEY"))
        except Exception as e:
            st.warning(f"Gemini judge unavailable: {e}")
    if st.button("Grade") and (ask or mode.startswith("Rules")):
        r = grade(report, key, ask)
        c = st.columns(4)
        c[0].metric("Score", r["score"]); c[1].metric("Matched", f"{r['tp']}/{len(key)}")
        c[2].metric("False positives", r["fp"]); c[3].metric("Precision", r["precision"])
        st.dataframe(pd.DataFrame([dict(id=a["id"], anomaly=a["title"], found=a["id"] in r["matches"],
                                        finding=r["findings"][r["matches"][a["id"]]] if a["id"] in r["matches"] else "")
                                   for a in key]))
        st.caption("score = max(0, (TP - 0.5*FP) / N). The matcher only decides TP/FP; it never sets the score.")
    with st.expander("Answer key (hidden from the agent in a real run)"):
        st.json(key)
        st.image(imgs["answer_net_income_reconciled.png"], caption="Reference: what the chart should show")

with t6:
    half = "\n".join(oracle.report(key).splitlines()[:1 + len(key) // 2])
    rows = [("Oracle (perfect report)", oracle.report(key), 1.0), ("NOP (empty report)", nop.report(), 0.0),
            (f"Half report ({len(key) // 2} of {len(key)})", half, 0.5)]
    out = [dict(case=n, expected=e, got=grade(rep, key)["score"], passed=grade(rep, key)["score"] == e)
           for n, rep, e in rows]
    st.dataframe(pd.DataFrame(out))
    st.caption("If oracle != 1.0 or NOP != 0.0, the task or grader is broken. These run in tests/ as well.")
