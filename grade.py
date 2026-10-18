"""Deterministic scorer. The matcher says which anomalies were found; the score is arithmetic:
    score = max(0, (TP - 0.5 * FP) / N)"""
import argparse, re
from generate_data import generate
from matcher import rule_match, llm_match

BULLET = re.compile(r"^\s*(?:[-*\u2022]|\d+[.)])\s+(.*\S)")


def parse_findings(text):
    return [m.group(1) for line in text.splitlines() if (m := BULLET.match(line))]


def grade(report, key, ask=None):
    findings = parse_findings(report)
    matches = llm_match(findings, key, ask) if ask else rule_match(findings, key)
    tp, n = len(matches), len(key)
    fp = len(findings) - tp
    return dict(
        score=round(max(0.0, (tp - 0.5 * fp) / n), 4), tp=tp, fp=fp, missed=n - tp,
        recall=round(tp / n, 4), precision=round(tp / len(findings), 4) if findings else 0.0,
        matches=matches, findings=findings)


if __name__ == "__main__":
    import oracle, nop
    p = argparse.ArgumentParser()
    p.add_argument("report", nargs="?", help="path to a markdown report")
    p.add_argument("--seed", type=int, default=7)
    p.add_argument("--llm", action="store_true", help="use Gemini matcher (needs GEMINI_API_KEY)")
    p.add_argument("--selfcheck", action="store_true")
    a = p.parse_args()
    _, key = generate(a.seed)
    if a.selfcheck:
        half = "\n".join(oracle.report(key).splitlines()[:1 + len(key) // 2])
        for name, rep in [("oracle", oracle.report(key)), ("nop", nop.report()), ("half", half)]:
            print(f"{name:7s} score={grade(rep, key)['score']}")
    else:
        ask = None
        if a.llm:
            from matcher import make_gemini_ask
            ask = make_gemini_ask()
        r = grade(open(a.report).read(), key, ask)
        print({k: v for k, v in r.items() if k != "findings"})
