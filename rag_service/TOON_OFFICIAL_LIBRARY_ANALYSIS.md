# TOON Official Library Analysis

## Overview

You've discovered the official TOON Python library: [toon-format/toon-python](https://github.com/toon-format/toon-python)

**Package**: `toon_format` (install via `pip install toon_format`)

This document analyzes whether you should migrate from your custom implementation to the official library.

---

## Current Implementation vs Official Library

### Your Custom Implementation (`utils/toon_encoder.py`)

**Strengths:**
- ✅ **Tailored to your use case**: Specifically designed for `DocumentChunk` objects
- ✅ **Domain-specific helpers**: 
  - `encode_contexts_to_toon()` - handles DocumentChunk directly
  - `encode_web_results_to_toon()` - handles web search results
  - `encode_contexts_hybrid()` - your hybrid TOON+JSON approach
  - `encode_contexts_flattened()` - fully flattened format
  - `compare_formats()` - comprehensive format comparison
- ✅ **Already integrated**: Working in production, tested, validated
- ✅ **Custom features**: 
  - Automatic field selection
  - Content truncation (max 500 chars)
  - Score inclusion logic
  - Format recommendation (`choose_best_format()`)

**Limitations:**
- ⚠️ **Token counting**: Uses simple estimation (`0.25 tokens/char`) instead of `tiktoken`
- ⚠️ **Maintenance burden**: You maintain the code
- ⚠️ **Spec compliance**: May not be 100% compliant with latest TOON spec

---

### Official Library (`toon_format`)

**Strengths:**
- ✅ **Official & maintained**: Community-driven, actively maintained
- ✅ **Spec compliant**: 100% compatible with TOON specification
- ✅ **Better token counting**: Uses `tiktoken` for accurate counts
- ✅ **Utilities**: Built-in `estimate_savings()`, `compare_formats()`, `count_tokens()`
- ✅ **CLI tools**: Command-line interface for encoding/decoding
- ✅ **Decode support**: Can decode TOON back to Python objects
- ✅ **Type normalization**: Handles edge cases (Infinity, NaN, datetime, etc.)
- ✅ **Battle-tested**: 792 tests, 91% coverage

**Limitations:**
- ⚠️ **Generic**: Not tailored to your `DocumentChunk` objects
- ⚠️ **Requires adaptation**: You'd need wrapper functions
- ⚠️ **Different API**: Uses `encode()`/`decode()` instead of your custom functions

---

## Comparison Table

| Feature | Your Implementation | Official Library |
|---------|-------------------|------------------|
| **TOON Encoding** | ✅ Custom functions | ✅ `encode()` |
| **TOON Decoding** | ❌ Not implemented | ✅ `decode()` |
| **Token Counting** | ⚠️ Estimation (0.25/char) | ✅ `tiktoken` (accurate) |
| **DocumentChunk Support** | ✅ Direct support | ⚠️ Needs wrapper |
| **Web Results Support** | ✅ Direct support | ⚠️ Needs wrapper |
| **Hybrid Format** | ✅ Built-in | ⚠️ Needs custom logic |
| **Format Comparison** | ✅ `compare_formats()` | ✅ `compare_formats()` |
| **Format Recommendation** | ✅ `choose_best_format()` | ❌ Not provided |
| **CLI Tools** | ❌ Not provided | ✅ Full CLI |
| **Spec Compliance** | ⚠️ Custom | ✅ 100% compliant |
| **Maintenance** | ⚠️ You maintain | ✅ Community maintained |
| **Testing** | ✅ Your tests | ✅ 792 tests, 91% coverage |

---

## Recommendation: **Hybrid Approach** ⭐

### Option 1: Keep Your Implementation (Recommended for Now)

**Why:**
- ✅ Already working in production
- ✅ Tailored to your specific needs
- ✅ No migration risk
- ✅ Custom features (hybrid format, format recommendation)

**Action Items:**
1. **Improve token counting**: Replace estimation with `tiktoken`
   ```python
   # In toon_encoder.py
   import tiktoken
   
   def estimate_token_count(text: str) -> int:
       try:
           encoding = tiktoken.encoding_for_model("gpt-4")
           return len(encoding.encode(text))
       except:
           return int(len(text) * 0.25)  # Fallback
   ```

2. **Add spec compliance check**: Compare your output with official library
3. **Keep monitoring**: Watch official library for useful features

---

### Option 2: Migrate to Official Library (Future Consideration)

**When to consider:**
- Official library adds features you need
- You want to reduce maintenance burden
- You need decode functionality
- You want 100% spec compliance

**Migration Strategy:**
1. Create wrapper functions that use official library
2. Keep your domain-specific helpers
3. Gradually migrate functions one by one
4. Run both in parallel during transition

**Example Migration:**
```python
# New approach using official library
from toon_format import encode, count_tokens

def encode_contexts_to_toon(contexts: List[DocumentChunk]) -> str:
    """Encode using official library."""
    # Convert DocumentChunk to dict
    data = [
        {
            "path": ctx.path[:50],
            "content": ctx.content[:500],
            "score": ctx.metadata.get("score", 0.0) if ctx.metadata else 0.0
        }
        for ctx in contexts
    ]
    
    # Use official library
    return encode(data, {"delimiter": ",", "indent": 2})

def estimate_token_count(text: str) -> int:
    """Use official library's token counting."""
    return count_tokens(text)  # Uses tiktoken
```

---

## Immediate Action: Improve Token Counting

The biggest improvement you can make **right now** without migration:

### Update `estimate_token_count()` in `toon_encoder.py`

**Current:**
```python
def estimate_token_count(text: str, tokens_per_char: float = 0.25) -> int:
    return int(len(text) * tokens_per_char)
```

**Improved (using tiktoken like official library):**
```python
import tiktoken

def estimate_token_count(text: str, model: str = "gpt-4") -> int:
    """Count tokens using tiktoken (accurate) with fallback."""
    try:
        encoding = tiktoken.encoding_for_model(model)
        return len(encoding.encode(text))
    except Exception:
        # Fallback to estimation if tiktoken fails
        return int(len(text) * 0.25)
```

**Benefits:**
- ✅ Accurate token counts (matches official library)
- ✅ Better savings calculations
- ✅ More reliable cost estimates
- ✅ No breaking changes to your API

---

## Testing Official Library

If you want to experiment with the official library:

### Install
```bash
pip install toon_format
# or with token counting utilities
pip install toon_format[benchmark]
```

### Quick Test
```python
from toon_format import encode, decode, count_tokens, estimate_savings

# Test with your data structure
data = [
    {"path": "docs/auth.md", "content": "Authentication...", "score": 0.85},
    {"path": "docs/api.md", "content": "API endpoints...", "score": 0.82},
]

# Encode
toon_str = encode(data)
print(toon_str)

# Count tokens
tokens = count_tokens(toon_str)
print(f"Tokens: {tokens}")

# Estimate savings vs JSON
result = estimate_savings(data)
print(f"Savings: {result['savings_percent']:.1f}%")
```

### Compare with Your Implementation
```python
# Your implementation
from rag_service.utils.toon_encoder import encode_contexts_to_toon, estimate_token_count

your_toon = encode_contexts_to_toon(contexts)
your_tokens = estimate_token_count(your_toon)

# Official library
from toon_format import encode, count_tokens

data = [{"path": ctx.path, "content": ctx.content, "score": ctx.metadata.get("score", 0.0)} 
        for ctx in contexts]
official_toon = encode(data)
official_tokens = count_tokens(official_toon)

# Compare
print(f"Your tokens: {your_tokens}")
print(f"Official tokens: {official_tokens}")
print(f"Difference: {abs(your_tokens - official_tokens)}")
```

---

## Decision Matrix

### Keep Your Implementation If:
- ✅ You're happy with current functionality
- ✅ You want domain-specific helpers
- ✅ You want to avoid migration risk
- ✅ You have custom features (hybrid format) you need

### Migrate to Official Library If:
- ✅ You want accurate token counting (tiktoken)
- ✅ You need decode functionality
- ✅ You want to reduce maintenance burden
- ✅ You want 100% spec compliance
- ✅ You want CLI tools

---

## Recommended Path Forward

### Phase 1: Immediate (This Week)
1. ✅ **Improve token counting**: Replace estimation with `tiktoken`
   - Update `estimate_token_count()` in `toon_encoder.py`
   - Test with your existing code
   - Verify token counts match official library

### Phase 2: Short Term (This Month)
2. ✅ **Test official library**: Install and compare outputs
   - Run side-by-side comparison
   - Verify spec compliance
   - Measure token count differences

### Phase 3: Long Term (Future)
3. ⚠️ **Consider migration**: If official library adds features you need
   - Create wrapper functions
   - Gradual migration
   - Keep domain-specific helpers

---

## Code Changes Needed (If Improving Token Counting)

### Update `rag_service/utils/toon_encoder.py`

```python
# Add import at top
import tiktoken

# Replace estimate_token_count function
def estimate_token_count(text: str, model: str = "gpt-4") -> int:
    """Count tokens using tiktoken (accurate) with fallback.
    
    Args:
        text: Text to count tokens for.
        model: Model name for tokenizer (default: "gpt-4").
    
    Returns:
        Token count.
    """
    try:
        encoding = tiktoken.encoding_for_model(model)
        return len(encoding.encode(text))
    except Exception as e:
        # Fallback to estimation if tiktoken fails
        logger.warning(f"tiktoken failed, using estimation: {e}")
        return int(len(text) * 0.25)
```

### Update `rag_service/requirements.txt`

```txt
# Token counting (for TOON format token measurement)
tiktoken>=0.5.0  # Already present, but ensure it's installed
```

---

## Summary

**Current Status**: Your custom implementation is working well and tailored to your needs.

**Recommendation**: 
1. **Keep your implementation** for now (it's working)
2. **Improve token counting** using `tiktoken` (easy win)
3. **Monitor official library** for useful features
4. **Consider migration** in the future if benefits outweigh costs

**Quick Win**: Update `estimate_token_count()` to use `tiktoken` - this will give you accurate token counts without changing your API or breaking anything.

---

## References

- [Official TOON Python Library](https://github.com/toon-format/toon-python)
- [TOON Format Specification](https://github.com/toon-format/toon/blob/main/SPEC.md)
- [Your Current Implementation](rag_service/utils/toon_encoder.py)

