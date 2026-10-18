"""Renders the dashboard's chart images. The plotted net-income values exist ONLY in the PNG
(no table lists them), so a text-only agent cannot find anomalies A9/A10."""
import argparse
from io import BytesIO
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from generate_data import QUARTERS, generate

COMPANY = "Meridian Logistics, Inc."


def _png(fig):
    buf = BytesIO()
    fig.savefig(buf, format="png", dpi=110, bbox_inches="tight")
    plt.close(fig)
    return buf.getvalue()


def net_income_chart(data, reconciled=False):
    table = data["income_statement"]["net_income"]
    vals = {q: (table[q] if reconciled else data["chart_net_income"][q]) / 1000 for q in QUARTERS}
    top = max(vals.values()) * 1.35
    fig, ax = plt.subplots(figsize=(6, 4))
    bars = ax.bar(QUARTERS, [vals[q] for q in QUARTERS], color="#2b6cb0", edgecolor="black", width=0.6)
    for q, b in zip(QUARTERS, bars):
        ax.text(b.get_x() + b.get_width() / 2, vals[q] + top * 0.01, f"{vals[q]:,.0f}",
                ha="center", va="bottom", fontweight="bold", fontsize=9)
    ax.set_ylim(0, top)
    ax.set_title(f"Net Income by Quarter ({'RECONCILED, ' if reconciled else ''}USD thousands)", fontsize=10)
    if reconciled:   # answer-key view: red notes show what the dashboard chart wrongly drew
        for i, q in enumerate(QUARTERS):
            drawn = data["chart_net_income"][q] / 1000
            if drawn != vals[q]:
                ax.annotate(f"chart drew {q} = {drawn:,.0f} \u2192 {vals[q]:,.0f}", xy=(i, vals[q]),
                            xytext=(i - 0.4, top * (0.92 - 0.1 * (i % 2))), color="crimson", fontsize=8,
                            arrowprops=dict(arrowstyle="->", color="crimson"))
    fig.suptitle(f"{COMPANY} \u2014 FY2025 Dashboard", fontweight="bold")
    return _png(fig)


def margins_chart(data):
    IS = data["income_statement"]
    fig, ax = plt.subplots(figsize=(6, 4))
    for label, line, color in [("Gross margin", "gross_profit", "#2b6cb0"),
                               ("Operating margin", "operating_income", "#dd8a1b"),
                               ("Net margin", "net_income", "#2f855a")]:
        ys = [100 * IS[line][q] / IS["revenue"][q] for q in QUARTERS]
        ax.plot(QUARTERS, ys, marker="o", label=label, color=color)
        for q, y in zip(QUARTERS, ys):
            ax.text(q, y + 1.2, f"{y:.1f}", ha="center", fontsize=7, color=color)
    ax.set_ylim(0, 60)
    ax.legend(fontsize=8, ncol=3, loc="upper center")
    ax.set_title("Profitability Margins (%), computed from reported statements", fontsize=10)
    fig.suptitle(f"{COMPANY} \u2014 FY2025 Dashboard", fontweight="bold")
    return _png(fig)


def render_all(data):
    return {"net_income_by_quarter.png": net_income_chart(data),
            "margins.png": margins_chart(data),
            "answer_net_income_reconciled.png": net_income_chart(data, reconciled=True)}


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--seed", type=int, default=7)
    out = Path("charts"); (out / "answer").mkdir(parents=True, exist_ok=True)
    for name, png in render_all(generate(ap.parse_args().seed)[0]).items():
        (out / ("answer" if name.startswith("answer") else "") / name).write_bytes(png)
    print("wrote charts/ (agent-facing) and charts/answer/ (answer key only)")
