import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from charts import render_all
from generate_data import generate, QUARTERS


def test_charts_are_pngs():
    for png in render_all(generate(7)[0]).values():
        assert png[:4] == b"\x89PNG"


def test_exactly_two_bars_disagree_with_table():
    d = generate(7)[0]
    bad = [q for q in QUARTERS if d["chart_net_income"][q] != d["income_statement"]["net_income"][q]]
    assert len(bad) == 2
