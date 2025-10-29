
import re, pathlib
from typing import List, Tuple

DATA_PATH = pathlib.Path(__file__).resolve().parents[1] / "data" / "faq.md"

def _split_sections(text: str) -> List[Tuple[str, str]]:
    # Returns list of (question, answer)
    blocks = re.split(r"^##\s+", text, flags=re.M)
    qa = []
    for blk in blocks:
        if not blk.strip(): continue
        lines = blk.strip().splitlines()
        q = lines[0].strip()
        a = " ".join(lines[1:]).strip()
        if q and a:
            qa.append((q, a))
    return qa

def load_kb():
    text = DATA_PATH.read_text(encoding="utf-8")
    return _split_sections(text)

def retrieve(question: str, kb=None, top_k=1):
    if kb is None:
        kb = load_kb()
    # Very naive similarity: overlap score
    def score(q, cand):
        qs = set(re.findall(r"[a-zA-Z0-9]+", q.lower()))
        cs = set(re.findall(r"[a-zA-Z0-9]+", cand.lower()))
        return len(qs & cs) / (len(qs) + 1e-6)
    ranked = sorted(kb, key=lambda qa: score(question, qa[0]), reverse=True)
    return ranked[:top_k]
