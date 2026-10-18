import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import pytest
import nop, oracle
from generate_data import generate
from grade import grade

KEY = generate(7)[1]


@pytest.mark.parametrize("seed", range(20))
def test_oracle_scores_one_on_every_seed(seed):
    assert grade(oracle.report(generate(seed)[1]), generate(seed)[1])["score"] == 1.0


def test_nop_scores_zero():
    assert grade(nop.report(), KEY)["score"] == 0.0


def test_half_report_scores_half():
    half = "\n".join(oracle.report(KEY).splitlines()[:1 + len(KEY) // 2])   # header + half the findings
    assert grade(half, KEY)["score"] == 0.5


def test_false_positives_are_penalised():
    rep = oracle.report(KEY) + "- Marketing spend looks high.\n- Tax rate seems odd.\n"
    assert grade(rep, KEY)["score"] == pytest.approx((len(KEY) - 1) / len(KEY))


def test_wrong_amount_is_not_a_match():
    bad = oracle.report(KEY).replace(f"{KEY[0]['amount']:,}", "1")
    assert "A1" not in grade(bad, KEY)["matches"]


def test_repeating_a_finding_does_not_double_count():
    line = f"- {KEY[0]['truth']}\n"
    r = grade(line * 3, KEY)
    assert (r["tp"], r["fp"]) == (1, 2)


def test_lenient_llm_cannot_inflate_score():
    always_first = lambda truth, findings: [0] if findings else []   # a "judge" that says yes to everything
    r = grade(oracle.report(KEY), KEY, ask=always_first)
    assert r["tp"] == 1 and r["score"] < 0.5


def test_llm_path_matches_rules_with_faithful_judge():
    faithful = lambda truth, findings: [i for i, f in enumerate(findings) if f == truth]
    assert grade(oracle.report(KEY), KEY, ask=faithful)["score"] == 1.0
