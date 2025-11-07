# TOON Format Audit for RAG Service

## Executive Summary

**TOON (Token-Oriented Object Notation)** is a format designed to reduce token usage by ~50% compared to JSON for LLM prompts. This audit analyzes where TOON can be integrated into our RAG service to save tokens and costs.

**Reference**: [TOON Format GitHub](https://github.com/toon-format/toon)

## Current Implementation Analysis

### 1. LLM Context Formatting (`llm_client.py`)

**Current Implementation:**
```python
# Current: Plain text concatenation
context_text = "\n\n".join(chunk.content for chunk in contexts)

# Prompt sent to LLM:
f"Context:\n{context_text}\n\nQuestion: {query}"
```

**Token Usage:**
- Plain text format
- No structured metadata included
- Each chunk separated by `\n\n`
- No chunk identification or source tracking in context

**Current Token Count Example:**
```
Context:
This is the first chunk of content about authentication...

This is the second chunk about authorization...

This is the third chunk about security...
```

**Estimated tokens**: ~50-100 tokens per chunk (depending on content)

### 2. DocumentChunk Structure

**Current Structure:**
```python
@dataclass
class DocumentChunk:
    doc_id: str
    chunk_id: str
    path: str
    content: str
    metadata: dict  # Contains: repo_url, repo_id, file_hash, etc.
```

**Issue**: Metadata is available but **not sent to LLM** - only `content` is used.

### 3. Web Search Results Formatting

**Current Implementation** (`search_service.py`):
```python
# Web search results formatted as plain text
full_content = f"Title: {search_result.get('title', '')}\n\n{content}"
# OR
full_content = f"Title: {search_result.get('title', '')}\n\nSnippet: {snippet}\n\nURL: {search_result.get('url', '')}"
```

**Token Usage:**
- Title, snippet, URL sent as plain text
- No structured format
- Repetitive formatting strings

## Where TOON Can Help

### Opportunity 1: Structured Context with Metadata

**Current Format (Plain Text):**
```
Context:
This is chunk 1 content...

This is chunk 2 content...

This is chunk 3 content...
```

**TOON Format (Structured):**
```toon
contexts[3]{path,content,score}:
  docs/auth.md,This is chunk 1 content...,0.85
  docs/api.md,This is chunk 2 content...,0.82
  docs/security.md,This is chunk 3 content...,0.79
```

**Token Savings:**
- **Before**: ~300 tokens (100 per chunk × 3)
- **After**: ~180 tokens (tabular format, no repetition)
- **Savings**: ~40% reduction

### Opportunity 2: Web Search Results

**Current Format:**
```
Title: Google ADK Agent Creation

Snippet: Learn how to create agents using Google ADK...

URL: https://docs.google.com/adk/agents
```

**TOON Format:**
```toon
web_results[2]{title,url,content}:
  Google ADK Agent Creation,https://docs.google.com/adk/agents,Learn how to create agents using Google ADK...
  LiteLLM Integration,https://docs.litellm.ai,Integrate LiteLLM with your application...
```

**Token Savings:**
- **Before**: ~150 tokens per result
- **After**: ~80 tokens per result
- **Savings**: ~47% reduction

### Opportunity 3: Mixed Context (KB + Web Search)

**Current Format:**
```
Context:
[KB Chunk 1]...

[KB Chunk 2]...

Web Search Result:
Title: ...
Snippet: ...
URL: ...
```

**TOON Format:**
```toon
kb_contexts[2]{path,content,score}:
  docs/auth.md,Authentication involves...,0.85
  docs/api.md,API endpoints require...,0.82

web_results[1]{title,url,content}:
  Google ADK Guide,https://docs.google.com/adk,Learn how to create agents...
```

**Token Savings:**
- **Before**: ~400 tokens
- **After**: ~220 tokens
- **Savings**: ~45% reduction

## Implementation Plan

### Phase 1: Add TOON Support Library

**Option 1: Use Python Implementation** (if available)
```bash
# Check if Python library exists
pip install toon-format  # May not exist yet - in development
```

**Option 2: Implement Basic TOON Encoder** (Recommended for now)
```python
# utils/toon_encoder.py
def encode_to_toon(data: List[Dict], fields: List[str]) -> str:
    """
    Convert list of dicts to TOON format.
    
    Args:
        data: List of dictionaries with uniform structure
        fields: List of field names to include
    
    Returns:
        TOON-formatted string
    """
    if not data:
        return ""
    
    # Build header
    header = f"{fields[0]}[{len(data)}]{{{','.join(fields)}}}:"
    
    # Build rows
    rows = []
    for item in data:
        row_values = []
        for field in fields:
            value = str(item.get(field, ""))
            # Escape commas and quotes if needed
            if "," in value or '"' in value:
                value = f'"{value}"'
            row_values.append(value)
        rows.append("  " + ",".join(row_values))
    
    return header + "\n" + "\n".join(rows)
```

### Phase 2: Update LLM Client

**Before:**
```python
def generate_answer(self, query: str, contexts: List[DocumentChunk]) -> str:
    context_text = "\n\n".join(chunk.content for chunk in contexts)
    # ... send to LLM
```

**After:**
```python
def generate_answer(
    self, 
    query: str, 
    contexts: List[DocumentChunk],
    use_toon: bool = True
) -> str:
    if use_toon and len(contexts) > 1:
        # Format as TOON for uniform structures
        context_data = [
            {
                "path": chunk.path,
                "content": chunk.content[:500],  # Truncate for TOON
                "score": chunk.metadata.get("score", 0.0)
            }
            for chunk in contexts
        ]
        context_text = encode_to_toon(context_data, ["path", "content", "score"])
        context_text = f"```toon\n{context_text}\n```"
    else:
        # Fallback to plain text
        context_text = "\n\n".join(chunk.content for chunk in contexts)
    # ... send to LLM
```

### Phase 3: Update Web Search Results Formatting

**Before:**
```python
full_content = f"Title: {title}\n\nSnippet: {snippet}\n\nURL: {url}"
```

**After:**
```python
# Format web search results as TOON
web_results = [
    {
        "title": result.get("title", ""),
        "url": result.get("url", ""),
        "content": result.get("content", "")[:500]  # Truncate
    }
    for result in search_results
]
web_content = encode_to_toon(web_results, ["title", "url", "content"])
```

## Token Savings Analysis

### Scenario 1: 5 KB Chunks + 3 Web Results

**Current Format:**
```
Context:
[Chunk 1 - 100 tokens]
[Chunk 2 - 100 tokens]
[Chunk 3 - 100 tokens]
[Chunk 4 - 100 tokens]
[Chunk 5 - 100 tokens]

Web Result 1:
Title: ... (20 tokens)
Snippet: ... (80 tokens)
URL: ... (10 tokens)

Web Result 2:
Title: ... (20 tokens)
Snippet: ... (80 tokens)
URL: ... (10 tokens)

Web Result 3:
Title: ... (20 tokens)
Snippet: ... (80 tokens)
URL: ... (10 tokens)
```
**Total: ~630 tokens**

**TOON Format:**
```toon
kb_contexts[5]{path,content,score}:
  docs/auth.md,Authentication content...,0.85
  docs/api.md,API content...,0.82
  docs/security.md,Security content...,0.79
  docs/user.md,User content...,0.76
  docs/admin.md,Admin content...,0.73

web_results[3]{title,url,content}:
  Google ADK Guide,https://docs.google.com/adk,Learn how to create agents...
  LiteLLM Docs,https://docs.litellm.ai,Integrate LiteLLM with your app...
  GitHub Guide,https://github.com/guide,Follow this guide for...
```
**Total: ~350 tokens**

**Savings: 44% reduction (280 tokens saved)**

### Scenario 2: Large Context (10 chunks)

**Current Format:**
- 10 chunks × 100 tokens = 1,000 tokens
- Separators: ~20 tokens
- **Total: ~1,020 tokens**

**TOON Format:**
- Header: ~30 tokens
- 10 rows × 60 tokens = 600 tokens
- **Total: ~630 tokens**

**Savings: 38% reduction (390 tokens saved)**

## Cost Impact

### Assumptions:
- Average query: 5 KB chunks + 3 web results
- Token savings per query: ~280 tokens
- Input tokens: $0.002 per 1K tokens (GPT-4 pricing example)
- 1,000 queries per month

### Cost Calculation:
- **Before**: 630 tokens × $0.002/1K × 1,000 = $1.26/query × 1,000 = **$1,260/month**
- **After**: 350 tokens × $0.002/1K × 1,000 = $0.70/query × 1,000 = **$700/month**
- **Savings**: **$560/month** (44% reduction)

### Annual Savings:
- **$6,720/year** for 1,000 queries/month
- **$67,200/year** for 10,000 queries/month
- **$672,000/year** for 100,000 queries/month

## Implementation Considerations

### Pros ✅
1. **Significant token savings** (~40-50% for structured data)
2. **Self-describing format** - LLMs understand structure naturally
3. **Better for uniform arrays** - Perfect for document chunks
4. **Reduced repetition** - No repeated field names
5. **Explicit structure** - Length markers and field headers help LLMs

### Cons ⚠️
1. **Python library not yet available** - Need to implement encoder
2. **Best for uniform data** - Mixed types may not benefit
3. **LLM familiarity** - Models need to see format to understand
4. **Content truncation** - TOON works best with shorter values
5. **Non-uniform data** - Falls back to list format (less efficient)

### When TOON Works Best:
- ✅ Uniform arrays of objects (document chunks)
- ✅ Same fields across all items
- ✅ Primitive values (strings, numbers)
- ✅ Tabular data (web search results)

### When JSON/Plain Text is Better:
- ❌ Non-uniform structures
- ❌ Deeply nested objects
- ❌ Varying field sets
- ❌ Very long content (needs truncation for TOON)

## Recommended Implementation

### Step 1: Create TOON Encoder Utility
- Implement basic TOON encoder for uniform arrays
- Add to `utils/toon_encoder.py`

### Step 2: Add Configuration
- Add `USE_TOON_FORMAT` setting (default: `True`)
- Allow fallback to plain text if needed

### Step 3: Update LLM Client
- Format contexts as TOON when multiple chunks
- Include metadata (path, score) in TOON format
- Keep plain text as fallback

### Step 4: Update Web Search Formatting
- Format web results as TOON
- Include title, URL, content in structured format

### Step 5: Testing
- Compare token counts before/after
- Verify LLM response quality
- Measure cost savings

## Example Implementation

### TOON Encoder (`utils/toon_encoder.py`)
```python
def encode_contexts_to_toon(contexts: List[DocumentChunk]) -> str:
    """Encode document chunks to TOON format."""
    if not contexts:
        return ""
    
    # Prepare data
    data = []
    for ctx in contexts:
        data.append({
            "path": ctx.path[:50],  # Truncate path
            "content": ctx.content[:500],  # Truncate content
            "score": ctx.metadata.get("score", 0.0)
        })
    
    # Build TOON
    header = f"contexts[{len(data)}]{{path,content,score}}:"
    rows = []
    for item in data:
        # Escape commas and quotes
        path = item["path"].replace(",", " ").replace('"', "'")
        content = item["content"].replace(",", " ").replace('"', "'")
        score = f"{item['score']:.2f}"
        rows.append(f"  {path},{content},{score}")
    
    return header + "\n" + "\n".join(rows)
```

### Updated LLM Client
```python
def generate_answer(self, query: str, contexts: List[DocumentChunk]) -> str:
    # Use TOON for structured context
    if len(contexts) > 1 and self.settings.use_toon_format:
        context_text = encode_contexts_to_toon(contexts)
        context_text = f"```toon\n{context_text}\n```"
    else:
        context_text = "\n\n".join(chunk.content for chunk in contexts)
    
    # Send to LLM...
```

## Next Steps

1. **Implement TOON encoder** - Create `utils/toon_encoder.py`
2. **Add configuration** - Add `USE_TOON_FORMAT` to `config.py`
3. **Update LLM client** - Integrate TOON formatting
4. **Test token counts** - Compare before/after
5. **Measure LLM quality** - Ensure response quality maintained
6. **Deploy gradually** - Feature flag for gradual rollout

## References

- [TOON Format GitHub](https://github.com/toon-format/toon)
- [TOON Specification](https://github.com/toon-format/toon/blob/main/SPEC.md)
- [TOON Format Website](https://toonformat.dev)

