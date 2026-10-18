"""Reference solution: the perfect report. Must score 1.0 or the task/grader is broken."""
def report(key):
    return "# Findings\n" + "\n".join(f"- {a['truth']}" for a in key) + "\n"
