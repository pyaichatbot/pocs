#!/usr/bin/env python3
import json
import os
import sys
import time
import urllib.error
import urllib.request


def http_request(url: str, method: str = "GET", data: dict | None = None, timeout: float = 15.0) -> tuple[int, str]:
    req = urllib.request.Request(url=url, method=method)
    if data is not None:
        payload = json.dumps(data).encode("utf-8")
        req.add_header("Content-Type", "application/json")
        req.data = payload
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            return resp.getcode(), body
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace") if e.fp else ""
        return e.code, body
    except Exception as e:
        return 0, str(e)


def main() -> int:
    base_url = os.getenv("RAG_BASE_URL", "http://localhost:8000")
    print(f"Base URL: {base_url}")
    failures: list[str] = []

    # 1) Health: GET /
    code, body = http_request(f"{base_url}/")
    print(f"GET / => {code}")
    if code != 200:
        failures.append(f"GET / expected 200, got {code}, body={body[:200]}")

    # 2) POST /ask with sample questions
    questions = [
        "What is refund policy?",
        "How do I cancel my subscription?",
        "Do you support SSO?",
    ]
    for q in questions:
        code, body = http_request(f"{base_url}/ask", method="POST", data={"question": q})
        print(f"POST /ask '{q}' => {code}")
        if code != 200:
            failures.append(f"POST /ask 200 expected, got {code}, body={body[:200]}")
            continue
        try:
            j = json.loads(body)
        except Exception:
            failures.append(f"POST /ask invalid JSON body: {body[:200]}")
            continue
        if not ("answer" in j and "retrieved_question" in j):
            failures.append(f"POST /ask missing keys in response: {j}")

    # 3) POST /offline-eval
    code, body = http_request(f"{base_url}/offline-eval", method="POST")
    print(f"POST /offline-eval => {code}")
    if code == 200:
        try:
            j = json.loads(body)
            print(f"offline-eval metrics: {j}")
        except Exception:
            failures.append(f"/offline-eval returned non-JSON body: {body[:200]}")
    else:
        failures.append(f"/offline-eval expected 200, got {code}, body={body[:200]}")

    # 4) Opik evaluation endpoints (optional but recommended)
    # 4a) Create dataset (idempotent name)
    ds_name = os.getenv("OPIK_DATASET_NAME", "rag-faq-demo-dataset")
    code, body = http_request(f"{base_url}/opik/create-dataset", method="POST", data={"name": ds_name})
    print(f"POST /opik/create-dataset => {code}")
    if code == 200:
        try:
            j = json.loads(body)
            if not ("dataset_name" in j and "dataset_id" in j):
                failures.append(f"/opik/create-dataset missing keys: {j}")
        except Exception:
            failures.append(f"/opik/create-dataset returned non-JSON body: {body[:200]}")
    else:
        failures.append(f"/opik/create-dataset expected 200, got {code}, body={body[:200]}")

    # 4b) Evaluate dataset (increased timeout for LLM evaluation)
    # First ensure dataset exists by creating it
    create_code, _ = http_request(f"{base_url}/opik/create-dataset", method="POST", data={"name": ds_name})
    if create_code != 200:
        failures.append(f"Failed to create dataset for evaluation: {create_code}")
        return 1
    
    code, body = http_request(f"{base_url}/opik/evaluate", method="POST", data={"name": ds_name}, timeout=60.0)
    print(f"POST /opik/evaluate => {code}")
    if code == 200:
        try:
            j = json.loads(body)
            # Expect experiment keys present
            expected_keys = {"experiment_id", "dataset_id", "experiment_name", "test_results", "experiment_url", "trial_count"}
            if not expected_keys.issubset(set(j.keys())):
                failures.append(f"/opik/evaluate missing expected keys: {set(j.keys())}")
        except Exception:
            failures.append(f"/opik/evaluate returned non-JSON body: {body[:200]}")
    else:
        failures.append(f"/opik/evaluate expected 200, got {code}, body={body[:200]}")

    # 4c) Evaluate prompt (increased timeout for LLM evaluation)
    # Ensure dataset exists for prompt evaluation too
    create_code, _ = http_request(f"{base_url}/opik/create-dataset", method="POST", data={"name": ds_name})
    if create_code != 200:
        failures.append(f"Failed to create dataset for prompt evaluation: {create_code}")
        return 1
        
    code, body = http_request(
        f"{base_url}/opik/evaluate-prompt",
        method="POST",
        data={"name": ds_name, "prompt": "Use only this context to answer: {{context}}\nQuestion: {{input}}"},
        timeout=60.0,
    )
    print(f"POST /opik/evaluate-prompt => {code}")
    if code == 200:
        try:
            j = json.loads(body)
            # Minimal shape check
            if not isinstance(j, dict):
                failures.append(f"/opik/evaluate-prompt unexpected body type")
        except Exception:
            failures.append(f"/opik/evaluate-prompt returned non-JSON body: {body[:200]}")
    else:
        failures.append(f"/opik/evaluate-prompt expected 200, got {code}, body={body[:200]}")

    if failures:
        print("\nFAILURES:")
        for f in failures:
            print(f"- {f}")
        return 1

    print("\nAll endpoint checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())


