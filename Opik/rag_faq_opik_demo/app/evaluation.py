
import re
from typing import List

def jaccard_similarity(a: str, b: str) -> float:
    ta = set(re.findall(r"[a-zA-Z0-9]+", a.lower()))
    tb = set(re.findall(r"[a-zA-Z0-9]+", b.lower()))
    if not ta and not tb: return 1.0
    return len(ta & tb) / max(1, len(ta | tb))

def evaluate_batch(dataset: List[dict], ask_fn) -> dict:
    scores = []
    for row in dataset:
        out = ask_fn(row["question"])
        score = jaccard_similarity(out, row["expected"])
        scores.append(score)
    avg = sum(scores)/len(scores) if scores else 0.0
    return {"avg_jaccard": round(avg, 3), "n": len(scores)}
