# Opik Integration Guide: RAG FAQ Demo

## What is Opik?

**Opik** is an open-source observability platform designed specifically for AI applications. It provides comprehensive monitoring, evaluation, and debugging capabilities for LLM-based systems, making it easier to build, deploy, and maintain production AI applications.

### Key Features of Opik:

1. **🔍 LLM Tracing**: Track every LLM call with detailed metadata
2. **📊 Evaluation Framework**: Built-in metrics for measuring AI performance
3. **🛡️ Guardrails**: Content safety and compliance monitoring
4. **📈 Experiment Tracking**: Compare different models and prompts
5. **🎯 Prompt Engineering**: Test and optimize prompts systematically
6. **🔧 Self-Hosting**: Deploy in your own infrastructure for full control

## Repository Overview

This repository demonstrates a **RAG (Retrieval-Augmented Generation) FAQ system** integrated with Opik for comprehensive observability and evaluation.

### Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   RAG Service   │    │   Opik Platform │    │  LLM Providers  │
│                 │    │                 │    │                 │
│ • FastAPI       │◄──►│ • Tracing       │    │ • Anthropic     │
│ • Vector Search │    │ • Evaluation    │    │ • Azure OpenAI  │
│ • Context RAG   │    │ • Guardrails    │    │ • Local Fallback│
│ • Opik SDK      │    │ • Experiments   │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## What We've Built

### 1. **RAG FAQ Service** (`app/main.py`)
A FastAPI-based service that answers questions using retrieved context from a knowledge base.

**Key Endpoints:**
- `GET /` - Health check
- `POST /ask` - Ask a question, get an answer with context
- `POST /offline-eval` - Run offline evaluation metrics
- `POST /opik/create-dataset` - Create Opik evaluation dataset
- `POST /opik/evaluate` - Run comprehensive LLM-judge evaluation
- `POST /opik/evaluate-prompt` - Evaluate prompt performance

### 2. **Opik Integration** (`app/opik_instrumentation.py`)
Seamless integration with Opik SDK for tracing and monitoring.

**Features:**
- Automatic LLM call tracing with `@track` decorator
- Guardrails for content safety (`Guardrail`, `PII`)
- Environment-based configuration (local vs server mode)
- Graceful fallbacks when Opik is unavailable

### 3. **Multi-Provider LLM Support** (`app/azure_client.py`)
Flexible LLM client supporting multiple providers with intelligent fallbacks.

**Provider Priority:**
1. **Anthropic Claude** (primary) - `claude-3-5-sonnet-20241022`
2. **Azure OpenAI** (secondary) - `gpt-4o-mini`
3. **Local LLM** (fallback) - Simple echo for testing

### 4. **Comprehensive Evaluation** (`app/opik_eval.py`)
Advanced evaluation system using Opik's LLM-judge metrics.

**Evaluation Metrics:**
- **Answer Relevance**: How well the answer addresses the question
- **Context Precision**: How much of the retrieved context was relevant
- **Context Recall**: How much relevant information was retrieved
- **Hallucination Detection**: Identifies made-up information

## How Opik Works in This System

### 1. **Tracing LLM Calls**

Every LLM interaction is automatically traced:

```python
@track  # Opik decorator
def generate_with_context(question: str, context: str) -> str:
    # This function call is automatically traced
    # You can see it in the Opik dashboard
    return model_call(messages)
```

**What gets tracked:**
- Input prompts and responses
- Model parameters and costs
- Execution time and tokens used
- Context and retrieved documents
- Error handling and retries

### 2. **Evaluation with LLM Judges**

Opik uses other LLMs to evaluate your AI system's performance:

```python
metrics = [
    AnswerRelevance(model="anthropic/claude-sonnet-4-20250514"),
    ContextPrecision(model="anthropic/claude-sonnet-4-20250514"),
    ContextRecall(model="anthropic/claude-sonnet-4-20250514"),
    Hallucination(model="anthropic/claude-sonnet-4-20250514"),
]
```

**How it works:**
1. Run your RAG system on test questions
2. Opik's LLM judges evaluate the quality of responses
3. Get numerical scores (0.0 to 1.0) for each metric
4. View detailed explanations for each evaluation

### 3. **Experiment Tracking**

Compare different approaches systematically:

```python
# Create dataset from test cases
dataset = create_dataset_from_json("faq-dataset", "tests/eval_dataset.json")

# Run evaluation experiment
results = run_experiment_evaluate("faq-dataset")
# Returns: experiment_id, scores, detailed metrics
```

**Benefits:**
- Track performance over time
- Compare different models
- A/B test different prompts
- Identify performance regressions

## Testing and Validation

### End-to-End Test Suite (`e2e_test.py`)

Comprehensive testing covering all functionality:

```bash
python e2e_test.py
```

**Test Coverage:**
1. ✅ **Health Check** - Service availability
2. ✅ **RAG Functionality** - Question answering with context
3. ✅ **Offline Evaluation** - Jaccard similarity metrics
4. ✅ **Opik Dataset Creation** - Test data management
5. ✅ **Opik Evaluation** - LLM-judge metrics (25s runtime)
6. ✅ **Prompt Evaluation** - Prompt performance testing

### LLM Unit Testing (`tests/test_llm_unit.py`)

Opik's `llm_unit` decorator for testing individual functions:

```python
@llm_unit
def test_generate_with_context():
    question = "What is the capital of France?"
    context = "Paris is the capital of France."
    result = generate_with_context(question, context)
    assert "Paris" in result
```

## Deployment Architecture

### Self-Hosted Opik Setup

```bash
# Start Opik platform
./self_host_opik.sh

# Start RAG service
docker compose up -d
```

**Docker Services:**
- `opik-frontend-1`: Opik web interface (port 5173)
- `opik-api-1`: Opik backend API
- `rag-service`: Our RAG application (port 8000)

**Network Configuration:**
- Services communicate via `opik_default` Docker network
- RAG service connects to Opik at `http://opik-frontend-1:5173/api/`

## Key Configuration

### Environment Variables

```bash
# Opik Configuration
OPIK_URL_OVERRIDE=http://opik-frontend-1:5173/api/
USE_OPIK=1
OPIK_USE_LOCAL=0

# LLM Configuration
ANTHROPIC_API_KEY=your_anthropic_key
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022
ANTHROPIC_MAX_TOKENS=512

# Optional: Azure OpenAI
AZURE_OPENAI_KEY=your_azure_key
AZURE_OPENAI_ENDPOINT=your_endpoint
AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini
```

### Opik Dashboard Access

Once running, access the Opik dashboard at:
- **Local**: http://localhost:5173
- **Docker**: http://opik-frontend-1:5173

## What You Can Do With This Setup

### 1. **Monitor Production Performance**
- View all LLM calls in real-time
- Track costs and token usage
- Monitor response times and errors

### 2. **Evaluate System Quality**
- Run comprehensive evaluations on test datasets
- Get detailed scores for answer relevance, context usage, and hallucination
- Compare different models and prompts

### 3. **Debug Issues**
- Trace problematic LLM calls
- Identify where context retrieval fails
- Understand why certain answers are generated

### 4. **Optimize Performance**
- A/B test different prompts
- Compare model performance
- Identify the best retrieval strategies

### 5. **Ensure Safety**
- Use guardrails to catch inappropriate content
- Monitor for PII leakage
- Set up alerts for quality degradation

## Sample Evaluation Results

When you run the evaluation, you'll see results like:

```
rag-faq-demo-dataset (3 samples) ──────────────╮
│                                             │
│ Total time:        00:00:25                 │
│ Number of samples: 3                        │
│                                             │
│ answer_relevance_metric: 0.1000 (avg)      │
│ context_precision_metric: 0.0667 (avg)     │
│ context_recall_metric: 0.1333 (avg)        │
│ hallucination_metric: 0.3333 (avg)         │
│                                             │
╰─────────────────────────────────────────────╯
```

**Interpreting Scores:**
- **Answer Relevance (0.10)**: Low - answers may not be addressing questions well
- **Context Precision (0.07)**: Low - retrieved context may not be very relevant
- **Context Recall (0.13)**: Low - may be missing important information
- **Hallucination (0.33)**: Moderate - some made-up information detected

## Next Steps

### For Production Use:
1. **Add more test data** to `tests/eval_dataset.json`
2. **Tune retrieval parameters** (top_k, similarity thresholds)
3. **Optimize prompts** based on evaluation feedback
4. **Set up monitoring alerts** for quality degradation
5. **Add more evaluation metrics** as needed

### For Development:
1. **Experiment with different models** (GPT-4, Claude variants)
2. **Try different retrieval strategies** (semantic search, hybrid search)
3. **Test different prompt templates**
4. **Add custom evaluation metrics**

## Troubleshooting

### Common Issues:

1. **"Dataset not found"**: Run dataset creation before evaluation
2. **Timeout errors**: Evaluation takes ~25s, increase test timeouts
3. **Authentication errors**: Ensure API keys are set correctly
4. **Network issues**: Check Docker network connectivity

### Debug Commands:

```bash
# Check service status
docker ps

# View logs
docker logs rag_faq_opik_demo-rag-service-1

# Test connectivity
curl http://localhost:8000/
curl http://localhost:5173/api/health

# Run specific tests
python e2e_test.py
```

## Conclusion

This repository demonstrates a production-ready RAG system with comprehensive Opik integration. It shows how to:

- Build robust AI applications with proper observability
- Use LLM-judge metrics for quality evaluation
- Deploy and monitor AI systems in production
- Debug and optimize AI performance systematically

The combination of RAG + Opik provides a solid foundation for building reliable, observable AI applications that can be continuously improved through data-driven insights.
