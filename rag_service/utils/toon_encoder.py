"""
TOON (Token-Oriented Object Notation) encoder for RAG service.

TOON format reduces token usage by ~50% compared to JSON for uniform arrays.
Reference: https://github.com/toon-format/toon

This implementation supports encoding document chunks and web search results
into TOON format for more efficient LLM prompts.
"""

from __future__ import annotations

from typing import Any, Dict, List


def escape_toon_value(value: str) -> str:
    """Escape TOON value if it contains commas or quotes.
    
    Args:
        value: String value to escape.
    
    Returns:
        Escaped value (quoted if needed).
    """
    if not value:
        return ""
    
    # Escape quotes
    value = value.replace('"', "'")
    
    # Quote if contains comma or starts/ends with space
    if "," in value or value.strip() != value:
        return f'"{value}"'
    
    return value


def encode_to_toon(
    data: List[Dict[str, Any]],
    fields: List[str],
    name: str = "items",
    delimiter: str = ",",
    max_value_length: int = 500,
) -> str:
    """Convert list of dictionaries to TOON format.
    
    Args:
        data: List of dictionaries with uniform structure.
        fields: List of field names to include in output.
        name: Name for the array (e.g., "contexts", "web_results").
        delimiter: Delimiter to use (default: ","). Can use "\t" for tabs.
        max_value_length: Maximum length for each value (truncate if longer).
    
    Returns:
        TOON-formatted string.
    
    Example:
        >>> data = [
        ...     {"path": "docs/auth.md", "content": "Authentication...", "score": 0.85},
        ...     {"path": "docs/api.md", "content": "API endpoints...", "score": 0.82},
        ... ]
        >>> encode_to_toon(data, ["path", "content", "score"], "contexts")
        'contexts[2]{path,content,score}:\\n  docs/auth.md,Authentication...,0.85\\n  docs/api.md,API endpoints...,0.82'
    """
    if not data:
        return f"{name}[0]:"
    
    # Build header: items[N]{field1,field2,...}:
    header = f"{name}[{len(data)}]{{{delimiter.join(fields)}}}:"
    
    # Build rows
    rows = []
    for item in data:
        row_values = []
        for field in fields:
            value = item.get(field, "")
            
            # Convert to string and truncate if needed
            if isinstance(value, (int, float)):
                # Format numbers nicely
                if isinstance(value, float):
                    value_str = f"{value:.2f}" if value < 1.0 else f"{value:.0f}"
                else:
                    value_str = str(value)
            else:
                value_str = str(value)
            
            # Truncate long values
            if len(value_str) > max_value_length:
                value_str = value_str[:max_value_length] + "..."
            
            # Escape if needed
            if delimiter == ",":
                value_str = escape_toon_value(value_str)
            
            row_values.append(value_str)
        
        # Join with delimiter
        row = delimiter.join(row_values)
        rows.append(f"  {row}")
    
    return header + "\n" + "\n".join(rows)


def encode_contexts_to_toon(
    contexts: List[Any],  # List[DocumentChunk] - avoiding circular import
    include_score: bool = True,
    max_content_length: int = 500,
) -> str:
    """Encode document chunks to TOON format.
    
    Args:
        contexts: List of DocumentChunk objects.
        include_score: Whether to include similarity score.
        max_content_length: Maximum length for content field.
    
    Returns:
        TOON-formatted string.
    """
    if not contexts:
        return ""
    
    # Prepare data
    data = []
    for ctx in contexts:
        item = {
            "path": getattr(ctx, "path", "")[:50],  # Truncate path
            "content": getattr(ctx, "content", "")[:max_content_length],  # Truncate content
        }
        
        if include_score:
            metadata = getattr(ctx, "metadata", {}) or {}
            item["score"] = metadata.get("score", 0.0)
        
        data.append(item)
    
    # Determine fields
    fields = ["path", "content"]
    if include_score:
        fields.append("score")
    
    return encode_to_toon(data, fields, name="contexts")


def encode_web_results_to_toon(
    web_results: List[Dict[str, Any]],
    max_content_length: int = 500,
) -> str:
    """Encode web search results to TOON format.
    
    Args:
        web_results: List of web search result dictionaries.
        max_content_length: Maximum length for content field.
    
    Returns:
        TOON-formatted string.
    """
    if not web_results:
        return ""
    
    # Prepare data
    data = []
    for result in web_results:
        content = result.get("content", "")
        snippet = result.get("snippet", "")
        
        # Use full content if available and longer, otherwise snippet
        if content and len(content) > len(snippet):
            display_content = content[:max_content_length]
        elif snippet:
            display_content = snippet[:max_content_length]
        else:
            display_content = ""
        
        data.append({
            "title": result.get("title", "")[:100],  # Truncate title
            "url": result.get("url", "")[:100],  # Truncate URL
            "content": display_content,
        })
    
    return encode_to_toon(data, ["title", "url", "content"], name="web_results")


def estimate_token_count(text: str, tokens_per_char: float = 0.25) -> int:
    """Estimate token count for text.
    
    Note: This is a rough estimate. Actual token counts vary by tokenizer.
    GPT-style tokenizers typically use ~0.25 tokens per character.
    
    Args:
        text: Text to estimate.
        tokens_per_char: Tokens per character (default: 0.25 for GPT-style).
    
    Returns:
        Estimated token count.
    """
    return int(len(text) * tokens_per_char)


def encode_contexts_hybrid(
    contexts: List[Any],  # List[DocumentChunk]
    include_metadata: bool = True,
    max_content_length: int = 500,
) -> str:
    """Encode contexts using hybrid TOON + JSON approach.
    
    Uses TOON for uniform content (efficient) and JSON for complex metadata.
    This approach provides best token efficiency while preserving structure.
    
    Args:
        contexts: List of DocumentChunk objects.
        include_metadata: Whether to include metadata in JSON format.
        max_content_length: Maximum length for content field.
    
    Returns:
        Hybrid TOON + JSON formatted string.
    
    Example:
        ```toon
        contexts[2]{path,content,score}:
          docs/auth.md,Authentication content...,0.85
          docs/api.md,API endpoints...,0.82
        
        metadata:
        {"contexts":[{"path":"docs/auth.md","repo_url":"https://gitlab.com/project.git","repo_id":"12345678"}]}
        ```
    """
    if not contexts:
        return ""
    
    # TOON format for main content (uniform structure)
    toon_data = []
    for ctx in contexts:
        metadata = getattr(ctx, "metadata", {}) or {}
        toon_data.append({
            "path": getattr(ctx, "path", "")[:50],  # Truncate path
            "content": getattr(ctx, "content", "")[:max_content_length],  # Truncate content
            "score": metadata.get("score", 0.0),
        })
    
    toon_part = encode_to_toon(toon_data, ["path", "content", "score"], "contexts")
    
    if not include_metadata:
        return toon_part
    
    # JSON format for metadata (compact, preserves structure)
    import json
    metadata_list = []
    for ctx in contexts:
        metadata = getattr(ctx, "metadata", {}) or {}
        if metadata:
            # Only include essential metadata fields
            metadata_item = {
                "path": getattr(ctx, "path", ""),
            }
            
            # Add repository info if available
            if "repo_url" in metadata:
                metadata_item["repo_url"] = metadata["repo_url"]
            if "repo_id" in metadata:
                metadata_item["repo_id"] = metadata["repo_id"]
            if "repo_full_path" in metadata:
                metadata_item["repo_full_path"] = metadata["repo_full_path"]
            if "provider" in metadata:
                metadata_item["provider"] = metadata["provider"]
            
            # Add source info
            if "source" in metadata:
                metadata_item["source"] = metadata["source"]
            
            metadata_list.append(metadata_item)
    
    metadata_dict = {"contexts": metadata_list}
    json_part = json.dumps(metadata_dict, separators=(",", ":"))  # Compact JSON
    
    return f"{toon_part}\n\nmetadata:\n{json_part}"


def flatten_chunk_metadata(chunk: Any) -> Dict[str, Any]:
    """Flatten DocumentChunk metadata for TOON encoding.
    
    Flattens nested metadata structure to top-level fields,
    making it suitable for TOON format.
    
    Args:
        chunk: DocumentChunk object.
    
    Returns:
        Flattened dictionary with all fields at top level.
    """
    flat = {
        "path": getattr(chunk, "path", "")[:50],
        "content": getattr(chunk, "content", "")[:500],
    }
    
    # Flatten metadata
    metadata = getattr(chunk, "metadata", {}) or {}
    for key, value in metadata.items():
        if isinstance(value, (str, int, float, bool)):
            # Simple values - add directly
            flat[key] = str(value)[:100]  # Truncate
        elif isinstance(value, dict):
            # Nested dicts - flatten with prefix
            for nested_key, nested_value in value.items():
                flat_key = f"{key}_{nested_key}"
                flat[flat_key] = str(nested_value)[:100]  # Truncate
        elif value is None:
            flat[key] = ""
    
    # Add score if available
    if "score" not in flat and "score" in metadata:
        flat["score"] = metadata.get("score", 0.0)
    
    return flat


def encode_contexts_flattened(
    contexts: List[Any],
    max_content_length: int = 500,
) -> str:
    """Encode contexts with fully flattened structure (all fields in TOON).
    
    This approach flattens all metadata to top-level fields,
    providing maximum token savings but losing some structure.
    
    Args:
        contexts: List of DocumentChunk objects.
        max_content_length: Maximum length for content field.
    
    Returns:
        TOON-formatted string with all fields flattened.
    """
    if not contexts:
        return ""
    
    # Flatten all chunks
    flattened_data = [flatten_chunk_metadata(ctx) for ctx in contexts]
    
    # Get all unique fields across all chunks
    all_fields = set()
    for item in flattened_data:
        all_fields.update(item.keys())
    
    # Prioritize important fields
    priority_fields = ["path", "content", "score"]
    other_fields = sorted([f for f in all_fields if f not in priority_fields])
    fields = priority_fields + other_fields
    
    return encode_to_toon(flattened_data, fields, "contexts")


def choose_best_format(
    contexts: List[Any],
    threshold: int = 3,
) -> str:
    """Choose best format based on data structure.
    
    Args:
        contexts: List of DocumentChunk objects.
        threshold: Minimum number of chunks to use TOON.
    
    Returns:
        Format choice: "toon", "hybrid", "json", or "plain"
    """
    if not contexts:
        return "plain"
    
    if len(contexts) < threshold:
        # Too few chunks - use plain text
        return "plain"
    
    # Check metadata complexity
    has_complex_metadata = False
    has_uniform_metadata = True
    first_metadata_keys = None
    
    for ctx in contexts:
        metadata = getattr(ctx, "metadata", {}) or {}
        
        # Check for nested structures
        for value in metadata.values():
            if isinstance(value, dict):
                has_complex_metadata = True
                break
        
        # Check uniformity
        if first_metadata_keys is None:
            first_metadata_keys = set(metadata.keys())
        else:
            if set(metadata.keys()) != first_metadata_keys:
                has_uniform_metadata = False
    
    if has_complex_metadata:
        # Use hybrid: TOON for content, JSON for metadata
        return "hybrid"
    elif has_uniform_metadata:
        # Use fully flattened TOON
        return "toon"
    else:
        # Non-uniform - use JSON or hybrid
        return "hybrid"


def compare_formats(
    contexts: List[Any],
    web_results: List[Dict[str, Any]] | None = None,
) -> Dict[str, Any]:
    """Compare token counts between plain text and TOON formats.
    
    Args:
        contexts: List of DocumentChunk objects.
        web_results: Optional list of web search results.
    
    Returns:
        Dictionary with token counts and savings.
    """
    # Plain text format (current)
    plain_text_parts = []
    
    # KB contexts
    for ctx in contexts:
        content = getattr(ctx, "content", "")
        plain_text_parts.append(content)
    
    # Web results
    if web_results:
        for result in web_results:
            title = result.get("title", "")
            content = result.get("content", "") or result.get("snippet", "")
            url = result.get("url", "")
            plain_text_parts.append(f"Title: {title}\n\n{content}\n\nURL: {url}")
    
    plain_text = "\n\n".join(plain_text_parts)
    plain_tokens = estimate_token_count(plain_text)
    
    # TOON format
    toon_parts = []
    
    # KB contexts
    if contexts:
        kb_toon = encode_contexts_to_toon(contexts)
        toon_parts.append(kb_toon)
    
    # Web results
    if web_results:
        web_toon = encode_web_results_to_toon(web_results)
        toon_parts.append(web_toon)
    
    toon_text = "\n\n".join(toon_parts)
    toon_tokens = estimate_token_count(toon_text)
    
    # Calculate savings
    savings = plain_tokens - toon_tokens
    savings_percent = (savings / plain_tokens * 100) if plain_tokens > 0 else 0
    
    # Also calculate hybrid format
    if contexts:
        hybrid_text = encode_contexts_hybrid(contexts, include_metadata=True)
        hybrid_tokens = estimate_token_count(hybrid_text)
    else:
        hybrid_text = ""
        hybrid_tokens = 0
    
    # Calculate flattened TOON format
    if contexts:
        flattened_text = encode_contexts_flattened(contexts)
        flattened_tokens = estimate_token_count(flattened_text)
    else:
        flattened_text = ""
        flattened_tokens = 0
    
    return {
        "plain_text": {
            "text": plain_text[:500] + "..." if len(plain_text) > 500 else plain_text,
            "length": len(plain_text),
            "tokens": plain_tokens,
        },
        "toon_format": {
            "text": toon_text[:500] + "..." if len(toon_text) > 500 else toon_text,
            "length": len(toon_text),
            "tokens": toon_tokens,
        },
        "hybrid_format": {
            "text": hybrid_text[:500] + "..." if len(hybrid_text) > 500 else hybrid_text,
            "length": len(hybrid_text),
            "tokens": hybrid_tokens,
        },
        "flattened_toon": {
            "text": flattened_text[:500] + "..." if len(flattened_text) > 500 else flattened_text,
            "length": len(flattened_text),
            "tokens": flattened_tokens,
        },
        "savings": {
            "toon_vs_plain": {
                "tokens": plain_tokens - toon_tokens,
                "percent": round(((plain_tokens - toon_tokens) / plain_tokens * 100) if plain_tokens > 0 else 0, 1),
            },
            "hybrid_vs_plain": {
                "tokens": plain_tokens - hybrid_tokens,
                "percent": round(((plain_tokens - hybrid_tokens) / plain_tokens * 100) if plain_tokens > 0 else 0, 1),
            },
            "flattened_vs_plain": {
                "tokens": plain_tokens - flattened_tokens,
                "percent": round(((plain_tokens - flattened_tokens) / plain_tokens * 100) if plain_tokens > 0 else 0, 1),
            },
        },
        "recommendation": choose_best_format(contexts),
    }

