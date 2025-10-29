import os
from typing import Dict

from opik.plugins.pytest.decorator import llm_unit
from app.main import generate_with_context


@llm_unit
def test_generate_with_context_simple() -> Dict:
    ctx = "We offer a 30-day refund policy on most products purchased directly from us."
    q = "What is refund policy?"
    out = generate_with_context(q, ctx)
    return {"input": q, "output": out, "context": ctx}


