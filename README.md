# Earnings Reconciliation: mini benchmark demo
Rebuilt miniature of a task type I designed (multi-statement reconciliation with planted anomalies).
Synthetic data and my own code; not the original project.

    pip install -r requirements.txt
    python -m pytest -q            # oracle=1.0, nop=0.0, half=0.5, FP penalty, lenient-judge test
    streamlit run app.py

Design: seeded generator plants 10 anomalies + answer key -> matcher decides which findings hit which
anomaly (rules by default, optional Gemini) -> score is plain arithmetic, so the rubric can't contradict itself.
Known limits: rule matcher needs exact amounts (writing "$45K" works, "~$45.2K" doesn't); knock-on symptoms
(e.g. A3 also makes FY gross profit not foot) are counted as false positives if reported separately.
