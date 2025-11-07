# Hybrid TOON + JSON Strategy for RAG Service

## Problem Statement

TOON format excels at **uniform arrays** but struggles with:
- **Deeply nested structures** (metadata objects)
- **Non-uniform fields** (varying metadata per chunk)
- **Mixed types** (complex nested objects)

**Question**: Can we flatten nested data and use a hybrid approach (JSON + TOON)?

## Current Data Structure Analysis

### DocumentChunk Structure

```python
@dataclass
class DocumentChunk:
    doc_id: str
    chunk_id: str
    path: str
    content: str
    metadata: dict  # Contains: repo_url, repo_id, repo_full_path, file_hash, score, etc.
```

### Example Metadata (Nested)

```python
metadata = {
    "repo_url": "https://gitlab.com/group/project.git",
    "repo_id": "12345678",
    "repo_full_path": "group/project",
    "provider": "gitlab",
    "file_hash": "abc123...",
    "score": 0.85,
    "source": "kb_search"
}
```

### Web Search Result Structure

```python
{
    "title": "Google ADK Guide",
    "url": "https://docs.google.com/adk",
    "content": "Full crawled content...",
    "snippet": "Original snippet...",
    "metadata": {
        "source": "web_search",
        "provider": "duckduckgo",
        "crawled": True,
        "score": 0.82
    }
}
```

## Strategy 1: Flatten Everything to TOON

### Approach: Flatten all nested fields to top level

**Before (JSON - nested):**
```json
{
  "contexts": [
    {
      "path": "docs/auth.md",
      "content": "Authentication...",
      "metadata": {
        "repo_url": "https://gitlab.com/project.git",
        "score": 0.85
      }
    }
  ]
}
```
**Tokens**: ~80 tokens

**After (TOON - flattened):**
```toon
contexts[1]{path,content,repo_url,score}:
  docs/auth.md,Authentication...,https://gitlab.com/project.git,0.85
```
**Tokens**: ~35 tokens

**Savings**: 56% reduction

### Pros ✅
- Maximum token savings
- Simple structure
- LLMs understand flat data easily

### Cons ⚠️
- Loses structure information
- Field name conflicts (if metadata has same keys as top-level)
- Less readable for humans

### Implementation

```python
def flatten_chunk_to_toon(chunk: DocumentChunk) -> Dict[str, Any]:
    """Flatten DocumentChunk for TOON encoding."""
    flat = {
        "path": chunk.path,
        "content": chunk.content[:500],  # Truncate
    }
    
    # Flatten metadata
    metadata = chunk.metadata or {}
    for key, value in metadata.items():
        if isinstance(value, (str, int, float, bool)):
            flat[key] = value
        elif isinstance(value, dict):
            # Flatten nested dicts with prefix
            for nested_key, nested_value in value.items():
                flat[f"{key}_{nested_key}"] = nested_value
    
    return flat

# Use in encoding
data = [flatten_chunk_to_toon(chunk) for chunk in contexts]
# Get all unique fields across chunks
all_fields = set()
for item in data:
    all_fields.update(item.keys())
fields = sorted(list(all_fields))  # Or prioritize certain fields

toon_output = encode_to_toon(data, fields, "contexts")
```

## Strategy 2: Hybrid Approach (JSON for Metadata + TOON for Content)

### Approach: Use TOON for uniform content, JSON for complex metadata

**Structure:**
```toon
contexts[3]{path,content,score}:
  docs/auth.md,Authentication content...,0.85
  docs/api.md,API endpoints content...,0.82
  docs/security.md,Security best practices...,0.79

metadata:
{
  "contexts": [
    {
      "path": "docs/auth.md",
      "repo_url": "https://gitlab.com/project.git",
      "repo_id": "12345678",
      "provider": "gitlab"
    },
    {
      "path": "docs/api.md",
      "repo_url": "https://gitlab.com/project.git",
      "repo_id": "12345678",
      "provider": "gitlab"
    },
    {
      "path": "docs/security.md",
      "repo_url": "https://github.com/org/repo",
      "repo_id": "87654321",
      "provider": "github"
    }
  ]
}
```

### Pros ✅
- TOON for uniform content (efficient)
- JSON for complex metadata (preserves structure)
- Best of both worlds
- Preserves all information

### Cons ⚠️
- Slightly more complex
- Two formats in one prompt
- LLM needs to understand both

### Token Comparison

**Pure JSON (nested):**
```json
{
  "contexts": [
    {"path": "...", "content": "...", "metadata": {"repo_url": "...", "score": 0.85}},
    {"path": "...", "content": "...", "metadata": {"repo_url": "...", "score": 0.82}}
  ]
}
```
**Tokens**: ~150 tokens

**Hybrid (TOON + JSON):**
```toon
contexts[2]{path,content,score}:
  docs/auth.md,Authentication...,0.85
  docs/api.md,API endpoints...,0.82

metadata:
{"contexts": [{"path": "docs/auth.md", "repo_url": "..."}, {"path": "docs/api.md", "repo_url": "..."}]}
```
**Tokens**: ~100 tokens (TOON: 60, JSON: 40)

**Savings**: 33% reduction vs pure JSON

## Strategy 3: Selective Flattening (Recommended)

### Approach: Flatten only what's needed for LLM, keep structure for programmatic use

**For LLM Prompt (flattened TOON):**
```toon
contexts[3]{path,content,score,repo}:
  docs/auth.md,Authentication...,0.85,gitlab.com/group/project
  docs/api.md,API endpoints...,0.82,gitlab.com/group/project
  docs/security.md,Security...,0.79,github.com/org/repo
```

**Key insight**: LLM doesn't need full metadata structure - just essential fields flattened.

### Implementation

```python
def encode_contexts_hybrid(
    contexts: List[DocumentChunk],
    include_fields: List[str] = None,
    max_content_length: int = 500
) -> str:
    """Encode contexts using selective flattening.
    
    Args:
        contexts: List of DocumentChunk objects
        include_fields: Fields to include from metadata (default: essential only)
        max_content_length: Max content length
    
    Returns:
        TOON-formatted string with flattened essential fields
    """
    if include_fields is None:
        # Default: only essential fields for LLM
        include_fields = ["repo_url", "score"]
    
    # Prepare data with selective flattening
    data = []
    for ctx in contexts:
        item = {
            "path": ctx.path[:50],
            "content": ctx.content[:max_content_length],
        }
        
        # Add selected metadata fields (flattened)
        metadata = ctx.metadata or {}
        for field in include_fields:
            value = metadata.get(field)
            if value is not None:
                # Flatten nested values
                if isinstance(value, dict):
                    # For nested dicts, use first value or join
                    value = str(list(value.values())[0]) if value else ""
                item[field] = str(value)[:100]  # Truncate
        
        data.append(item)
    
    # Build field list
    fields = ["path", "content"] + include_fields
    
    return encode_to_toon(data, fields, "contexts")
```

## Strategy 4: Smart Format Selection

### Approach: Use TOON for uniform arrays, JSON for complex structures

**Decision logic:**
```python
def choose_format(data: List[Dict]) -> str:
    """Choose best format based on data structure."""
    
    # Check if uniform (all items have same keys)
    if len(data) == 0:
        return "empty"
    
    first_keys = set(data[0].keys())
    all_uniform = all(set(item.keys()) == first_keys for item in data)
    
    # Check if all values are primitive
    all_primitive = all(
        isinstance(v, (str, int, float, bool)) or v is None
        for item in data
        for v in item.values()
    )
    
    # Check nesting depth
    max_depth = max(get_depth(item) for item in data)
    
    if all_uniform and all_primitive and max_depth <= 1:
        return "toon"  # Use TOON
    elif max_depth > 2:
        return "json"  # Use JSON for deeply nested
    else:
        return "hybrid"  # Use hybrid approach
```

## Recommended Approach for RAG Service

### Hybrid Strategy: TOON for Content, JSON for Metadata

**Format:**
```toon
# Main content (uniform, use TOON)
contexts[3]{path,content,score}:
  docs/auth.md,Authentication involves verifying user identity...,0.85
  docs/api.md,API endpoints require authentication tokens...,0.82
  docs/security.md,Security best practices include HTTPS...,0.79

# Metadata (complex, use compact JSON)
metadata:
{"contexts":[
  {"path":"docs/auth.md","repo_url":"https://gitlab.com/project.git","repo_id":"12345678"},
  {"path":"docs/api.md","repo_url":"https://gitlab.com/project.git","repo_id":"12345678"},
  {"path":"docs/security.md","repo_url":"https://github.com/org/repo","repo_id":"87654321"}
]}
```

### Why This Works

1. **Content is uniform** → TOON is efficient
2. **Metadata is complex** → JSON preserves structure
3. **LLM can focus on content** → Metadata is optional reference
4. **Token efficient** → Best of both worlds

### Token Savings

**Pure JSON (current if we used it):**
- ~200 tokens for 3 chunks with full metadata

**Hybrid (TOON + JSON):**
- TOON: ~80 tokens (content)
- JSON: ~50 tokens (metadata)
- **Total: ~130 tokens**
- **Savings: 35%**

## Implementation Plan

### Step 1: Update TOON Encoder

```python
def encode_contexts_hybrid(
    contexts: List[DocumentChunk],
    include_metadata: bool = True,
    metadata_format: str = "json"  # "json" or "toon"
) -> str:
    """Encode contexts with hybrid TOON + JSON approach."""
    
    # TOON format for main content
    toon_data = [
        {
            "path": ctx.path[:50],
            "content": ctx.content[:500],
            "score": ctx.metadata.get("score", 0.0) if ctx.metadata else 0.0
        }
        for ctx in contexts
    ]
    toon_part = encode_to_toon(toon_data, ["path", "content", "score"], "contexts")
    
    if not include_metadata:
        return toon_part
    
    # JSON format for metadata (compact)
    metadata_part = {
        "contexts": [
            {
                "path": ctx.path,
                "repo_url": ctx.metadata.get("repo_url", ""),
                "repo_id": ctx.metadata.get("repo_id", ""),
                "provider": ctx.metadata.get("provider", ""),
            }
            for ctx in contexts
            if ctx.metadata
        ]
    }
    
    import json
    json_part = json.dumps(metadata_part, separators=(",", ":"))  # Compact JSON
    
    return f"{toon_part}\n\nmetadata:\n{json_part}"
```

### Step 2: Update LLM Client

```python
def generate_answer(self, query: str, contexts: List[DocumentChunk]) -> str:
    # Use hybrid format
    from .utils.toon_encoder import encode_contexts_hybrid
    
    if len(contexts) > 1:
        context_text = encode_contexts_hybrid(contexts, include_metadata=True)
        context_text = f"```toon\n{context_text}\n```"
    else:
        # Single context - use plain text
        context_text = contexts[0].content if contexts else ""
    
    # Send to LLM...
```

## Comparison Matrix

| Format | Uniform Arrays | Nested Data | Token Efficiency | LLM Understanding |
|--------|---------------|-------------|------------------|-------------------|
| **Pure JSON** | ⚠️ Verbose | ✅ Perfect | ❌ High tokens | ✅ Excellent |
| **Pure TOON** | ✅ Excellent | ❌ Struggles | ✅ Low tokens | ✅ Good |
| **Hybrid** | ✅ TOON part | ✅ JSON part | ✅ Balanced | ✅ Excellent |
| **Flattened TOON** | ✅ Excellent | ⚠️ Loses structure | ✅ Low tokens | ✅ Good |

## Real-World Example

### Scenario: 5 KB chunks with complex metadata

**Pure JSON (nested):**
```json
{
  "contexts": [
    {
      "path": "docs/auth.md",
      "content": "Authentication...",
      "metadata": {
        "repo_url": "https://gitlab.com/project.git",
        "repo_id": "12345678",
        "repo_full_path": "group/project",
        "provider": "gitlab",
        "file_hash": "abc123...",
        "score": 0.85
      }
    },
    // ... 4 more
  ]
}
```
**Tokens**: ~450 tokens

**Hybrid (TOON + JSON):**
```toon
contexts[5]{path,content,score}:
  docs/auth.md,Authentication...,0.85
  docs/api.md,API endpoints...,0.82
  docs/security.md,Security...,0.79
  docs/user.md,User management...,0.76
  docs/admin.md,Admin functions...,0.73

metadata:
{"contexts":[{"path":"docs/auth.md","repo_url":"https://gitlab.com/project.git","repo_id":"12345678"},{"path":"docs/api.md","repo_url":"https://gitlab.com/project.git","repo_id":"12345678"},{"path":"docs/security.md","repo_url":"https://gitlab.com/project.git","repo_id":"12345678"},{"path":"docs/user.md","repo_url":"https://gitlab.com/project.git","repo_id":"12345678"},{"path":"docs/admin.md","repo_url":"https://gitlab.com/project.git","repo_id":"12345678"}]}
```
**Tokens**: ~280 tokens (TOON: 200, JSON: 80)

**Savings**: 38% reduction (170 tokens saved)

## Recommendations

### ✅ Use Hybrid Approach When:
- Contexts have uniform content structure
- Metadata is complex/nested
- Need to preserve all information
- Want best token efficiency

### ✅ Use Pure TOON When:
- All data is uniform and flat
- Metadata is simple (just scores)
- Maximum token savings needed

### ✅ Use Pure JSON When:
- Data is highly non-uniform
- Deeply nested structures required
- Structure preservation is critical

### ✅ Use Flattened TOON When:
- Can afford to lose some structure
- Maximum token savings priority
- Metadata is less important for LLM

## Conclusion

**Best approach for RAG service**: **Hybrid TOON + JSON**

- Content → TOON (uniform, efficient)
- Metadata → Compact JSON (preserves structure)
- Best token efficiency while maintaining all information
- LLMs understand both formats naturally

**Expected savings**: 30-40% token reduction vs pure JSON, while preserving all structured information.

