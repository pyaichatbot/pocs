import json
import os
from typing import Dict, List

from opik import Opik, track
from opik.evaluation import evaluate, evaluate_prompt
from opik.evaluation.metrics import (
    AnswerRelevance,
    ContextPrecision,
    ContextRecall,
    Hallucination,
)

from app.retriever import retrieve, load_kb


def create_dataset_from_json(name: str, path: str) -> str:
    client = Opik()
    ds = client.get_or_create_dataset(name=name)
    with open(path, "r", encoding="utf-8") as f:
        rows = json.load(f)
    items = []
    for row in rows:
        items.append({"input": {"user_question": row["question"], "expected": row.get("expected", "")}})
    ds.insert(items)
    return ds.id


def run_experiment_evaluate(dataset_name: str) -> Dict:
    client = Opik()
    ds = client.get_dataset(name=dataset_name)

    KB = load_kb()

    @track
    def task(x: Dict) -> Dict:
        # Dataset items are inserted with top-level keys per Opik docs
        question = x.get("user_question", "")
        expected_output = x.get("expected_output", "")
        hits = retrieve(question, KB, top_k=1)
        rq, rc = hits[0] if hits else ("", "")
        # Lazy import to avoid circular import at module import time
        from app.main import generate_with_context
        output = generate_with_context(question, rc)
        return {
            "input": question,
            "output": output,
            "context": rc,
            "expected_output": expected_output,
            # Additional fields that some metrics might need
            "retrieved_context": rc,
            "ground_truth": expected_output,
        }

    # Configure metrics to use Anthropic and handle context properly
    metrics = [
        AnswerRelevance(
            model="anthropic/claude-sonnet-4-20250514",
            require_context=True
        ),
        ContextPrecision(model="anthropic/claude-sonnet-4-20250514"),
        ContextRecall(model="anthropic/claude-sonnet-4-20250514"),
        Hallucination(model="anthropic/claude-sonnet-4-20250514"),
    ]

    return evaluate(dataset=ds, task=task, scoring_metrics=metrics)


def run_prompt_eval(prompt_text: str, dataset_name: str) -> Dict:
    client = Opik()
    ds = client.get_dataset(name=dataset_name)

    # Convert prompt text to messages format
    messages = [{"role": "user", "content": prompt_text}]
    metrics = [AnswerRelevance(
        model="anthropic/claude-sonnet-4-20250514",
        require_context=False  # Prompt eval might not have context
    )]
    # Use Anthropic to avoid requiring OPENAI_API_KEY
    return evaluate_prompt(
        dataset=ds,
        messages=messages,
        scoring_metrics=metrics,
        model="anthropic/claude-sonnet-4-20250514",
    )


if __name__ == "__main__":
    # Example usage from CLI
    json_path = os.path.join(os.path.dirname(__file__), "..", "tests", "eval_dataset.json")
    ds_name = os.getenv("OPIK_DATASET_NAME", "rag-faq-demo-dataset")
    if os.getenv("CREATE_DATASET", "0") == "1":
        ds_id = create_dataset_from_json(ds_name, json_path)
        print(f"Created dataset {ds_name}: {ds_id}")
    if os.getenv("RUN_EVALUATE", "1") == "1":
        res = run_experiment_evaluate(ds_name)
        print(json.dumps(res, indent=2))
    if os.getenv("RUN_PROMPT_EVAL", "0") == "1":
        res = run_prompt_eval("Use only this context to answer: {{context}}\nQuestion: {{input}}", ds_name)
        print(json.dumps(res, indent=2))


