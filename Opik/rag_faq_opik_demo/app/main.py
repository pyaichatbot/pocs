
import os, json
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from jinja2 import Template

from app.retriever import retrieve, load_kb
from app.azure_client import get_model
from app.opik_instrumentation import track, Guardrail, PII, USE_OPIK
from app.evaluation import evaluate_batch, jaccard_similarity
from app.opik_eval import (
    create_dataset_from_json,
    run_experiment_evaluate,
    run_prompt_eval,
)

app = FastAPI(title="RAG FAQ Demo with Opik")
model_call = get_model()
KB = load_kb()

# Optional guardrails
guard = None
if USE_OPIK and Guardrail and PII:
    try:
        guard = Guardrail(guards=[PII()])
    except Exception as e:
        print(f"[opik] Guardrail init failed: {e}")

INDEX_HTML = Template("""
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8" />
  <title>RAG FAQ Demo</title>
  <style>
    body { font-family: system-ui, Arial, sans-serif; max-width: 880px; margin: 2rem auto; }
    textarea, input { width: 100%; padding: .6rem; font-size: 1rem; }
    button { padding: .6rem 1rem; font-size: 1rem; cursor: pointer; }
    .card { border: 1px solid #e5e7eb; padding: 1rem; border-radius: .5rem; margin-top: 1rem; }
    .meta { color: #6b7280; font-size: .9rem; }
  </style>
</head>
<body>
  <h1>RAG FAQ Demo <span style="font-size:.8em;color:#6b7280;">with Opik tracing</span></h1>
  <form onsubmit="ask(event)">
    <textarea id="q" rows="3" placeholder="Ask a question, e.g., What is refund policy?"></textarea>
    <button type="submit">Ask</button>
  </form>
  <div id="out"></div>
<script>
async function ask(e){
  e.preventDefault();
  const q = document.getElementById('q').value;
  const r = await fetch('/ask', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({question:q})});
  const j = await r.json();
  const div = document.createElement('div');
  div.className='card';
  div.innerHTML = `<div><b>Answer</b><br>${j.answer}</div>
  <div class='meta'>Retrieved: ${j.retrieved_question}</div>`;
  document.getElementById('out').prepend(div);
}
</script>
</body>
</html>
""")

@app.get("/", response_class=HTMLResponse)
def index():
    return INDEX_HTML.render()

@track
def generate_with_context(question: str, context: str) -> str:
    messages = [
        {"role": "system", "content": f"Use only this context to answer:\n{context}"},
        {"role": "user", "content": question},
    ]
    answer = model_call(messages)
    return answer

@app.post("/ask")
def ask(payload: dict):
    q = payload.get("question","").strip()
    hits = retrieve(q, KB, top_k=1)
    if not hits:
        return JSONResponse({"answer": "No relevant context found.", "retrieved_question": None})
    rq, ra = hits[0]
    answer = generate_with_context(q, ra)
    if guard:
        try:
            guard.validate(answer)
        except Exception as e:
            answer = "[BLOCKED by guardrails]"
    return JSONResponse({"answer": answer, "retrieved_question": rq})

@app.post("/offline-eval")
def offline_eval():
    # Run simple evaluation on the provided dataset
    path = os.path.join(os.path.dirname(__file__), "..", "tests", "eval_dataset.json")
    with open(path, "r", encoding="utf-8") as f:
        ds = json.load(f)
    def ask_fn(question: str):
        hits = retrieve(question, KB, top_k=1)
        rq, ra = hits[0] if hits else ("","")
        return generate_with_context(question, ra)
    metrics = evaluate_batch(ds, ask_fn)
    return metrics

@app.post("/opik/create-dataset")
def opik_create_dataset(payload: dict | None = None):
    name = (payload or {}).get("name") or os.getenv("OPIK_DATASET_NAME", "rag-faq-demo-dataset")
    path = os.path.join(os.path.dirname(__file__), "..", "tests", "eval_dataset.json")
    ds_id = create_dataset_from_json(name, path)
    return {"dataset_name": name, "dataset_id": ds_id}

@app.post("/opik/evaluate")
def opik_evaluate(payload: dict | None = None):
    name = (payload or {}).get("name") or os.getenv("OPIK_DATASET_NAME", "rag-faq-demo-dataset")
    result = run_experiment_evaluate(name)
    return result

@app.post("/opik/evaluate-prompt")
def opik_evaluate_prompt(payload: dict | None = None):
    name = (payload or {}).get("name") or os.getenv("OPIK_DATASET_NAME", "rag-faq-demo-dataset")
    prompt_text = (payload or {}).get("prompt") or "Use only this context to answer: {{context}}\nQuestion: {{input}}"
    result = run_prompt_eval(prompt_text, name)
    return result

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
