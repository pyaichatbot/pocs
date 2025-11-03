# Sanitization Patterns

This document provides implementation patterns for creating input sanitization rules for specific skill types.

## Pattern Categories

### 1. Pattern-Based Filtering (Regex)

**Purpose**: Detect and remove/block suspicious patterns

**Implementation Pattern**:
```python
import re

def filter_suspicious_patterns(text: str, patterns: list) -> tuple[str, list[str]]:
    """
    Filter text using regex patterns
    
    Returns:
        (sanitized_text, detected_threats)
    """
    detected = []
    sanitized = text
    
    for pattern in patterns:
        if pattern['compiled'].search(sanitized):
            detected.append(pattern['description'])
            if pattern['action'] == 'block':
                return '', detected
            elif pattern['action'] == 'remove':
                sanitized = pattern['compiled'].sub('', sanitized)
    
    return sanitized, detected
```

### 2. Encoding Normalization

**Purpose**: Normalize unicode and prevent encoding-based attacks

**Implementation Pattern**:
```python
import unicodedata

def normalize_encoding(text: str) -> str:
    """
    Normalize text encoding to prevent encoding attacks
    """
    # Normalize to NFKC form
    normalized = unicodedata.normalize('NFKC', text)
    
    # Remove suspicious unicode characters
    suspicious_chars = {
        '\u200b': '',  # Zero-width space
        '\u200c': '',  # Zero-width non-joiner
        '\u200d': '',  # Zero-width joiner
        '\ufeff': '',  # Zero-width no-break space
        '\u202e': '',  # Right-to-left override
    }
    
    for char, replacement in suspicious_chars.items():
        normalized = normalized.replace(char, replacement)
    
    return normalized
```

### 3. Delimiter Escaping

**Purpose**: Prevent boundary delimiter injection

**Implementation Pattern**:
```python
def escape_delimiters(text: str, delimiters: dict) -> str:
    """
    Escape or remove delimiter-like patterns from text
    """
    escaped = text
    
    for delimiter in delimiters.values():
        # Replace delimiter with safe alternative
        escaped = escaped.replace(delimiter, f"[DELIMITER_ESCAPED_{hash(delimiter) % 10000}]")
    
    # Also escape common delimiter patterns
    escaped = re.sub(r'(===|<<<|>>>|---)', '[BOUNDARY_REMOVED]', escaped)
    
    return escaped
```

### 4. Length Limits

**Purpose**: Prevent resource exhaustion attacks

**Implementation Pattern**:
```python
def apply_length_limits(text: str, max_length: int = 50000) -> tuple[str, bool]:
    """
    Apply length limits to input
    
    Returns:
        (truncated_text, was_truncated)
    """
    if len(text) <= max_length:
        return text, False
    
    # Truncate and add marker
    truncated = text[:max_length]
    return truncated + "[TRUNCATED]", True
```

### 5. Character Whitelists/Blacklists

**Purpose**: Restrict allowed characters for specific input types

**Implementation Pattern**:
```python
def apply_character_filters(text: str, allowed_chars: set = None, blocked_chars: set = None) -> str:
    """
    Apply character whitelist or blacklist
    
    Args:
        text: Input text
        allowed_chars: Set of allowed characters (whitelist)
        blocked_chars: Set of blocked characters (blacklist)
    """
    if allowed_chars:
        # Whitelist approach
        filtered = ''.join(c for c in text if c in allowed_chars)
    elif blocked_chars:
        # Blacklist approach
        filtered = ''.join(c for c in text if c not in blocked_chars)
    else:
        filtered = text
    
    return filtered
```

## Skill-Specific Patterns

### Summarizer Skills

**Input Sources**: Document text, article content

**Sanitization Rules**:
```python
def sanitize_for_summarizer(text: str) -> tuple[str, list[str]]:
    """
    Sanitize input for summarization skills
    """
    threats = []
    
    # 1. Normalize encoding
    sanitized = normalize_encoding(text)
    
    # 2. Check for instruction injection in document
    instruction_patterns = [
        r'ignore\s+(all\s+)?(previous|prior)',
        r'(system|admin)\s*mode',
    ]
    
    for pattern in instruction_patterns:
        if re.search(pattern, sanitized, re.IGNORECASE):
            threats.append(f"Instruction injection detected in document")
    
    # 3. Apply length limits (documents can be long)
    sanitized, truncated = apply_length_limits(sanitized, max_length=100000)
    if truncated:
        threats.append("Document truncated due to length")
    
    return sanitized, threats
```

### Translator Skills

**Input Sources**: Text to translate, source/target language

**Sanitization Rules**:
```python
def sanitize_for_translator(text: str, source_lang: str, target_lang: str) -> tuple[str, list[str]]:
    """
    Sanitize input for translation skills
    """
    threats = []
    sanitized = text
    
    # 1. Normalize encoding
    sanitized = normalize_encoding(sanitized)
    
    # 2. Validate language codes
    valid_languages = {'en', 'es', 'fr', 'de', 'zh', 'ja', 'ko'}
    if source_lang not in valid_languages or target_lang not in valid_languages:
        threats.append("Invalid language code")
        return sanitized, threats
    
    # 3. Check for hidden instructions in foreign text
    # (Requires specialized detection for language-specific patterns)
    
    # 4. Apply length limits
    sanitized, truncated = apply_length_limits(sanitized, max_length=50000)
    
    return sanitized, threats
```

### Code Generator Skills

**Input Sources**: Requirements, specifications, code snippets

**Sanitization Rules**:
```python
def sanitize_for_code_generator(requirements: str) -> tuple[str, list[str]]:
    """
    Sanitize input for code generation skills
    """
    threats = []
    sanitized = requirements
    
    # 1. Normalize encoding
    sanitized = normalize_encoding(sanitized)
    
    # 2. Block system-level commands
    dangerous_patterns = [
        r'sudo\s+',
        r'rm\s+-rf',
        r'delete\s+system',
        r'format\s+disk',
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, sanitized, re.IGNORECASE):
            threats.append("Dangerous system command detected")
            sanitized = re.sub(pattern, '[BLOCKED]', sanitized, flags=re.IGNORECASE)
    
    # 3. Check for credential extraction attempts
    credential_patterns = [
        r'(api[_-]?key|password|secret|token)\s*[:=]\s*\w+',
    ]
    
    for pattern in credential_patterns:
        if re.search(pattern, sanitized, re.IGNORECASE):
            threats.append("Potential credential extraction attempt")
    
    # 4. Apply length limits
    sanitized, truncated = apply_length_limits(sanitized, max_length=20000)
    
    return sanitized, threats
```

### File Processor Skills

**Input Sources**: File content, file paths

**Sanitization Rules**:
```python
import os

def sanitize_file_path(file_path: str) -> tuple[str, list[str]]:
    """
    Sanitize file path to prevent directory traversal
    """
    threats = []
    
    # 1. Normalize path
    normalized_path = os.path.normpath(file_path)
    
    # 2. Check for directory traversal
    if '..' in normalized_path or normalized_path.startswith('/'):
        threats.append("Directory traversal attempt detected")
        return '', threats
    
    # 3. Restrict to allowed directories
    allowed_base = '/safe/directory/'
    full_path = os.path.join(allowed_base, normalized_path)
    
    # 4. Verify it's within allowed directory
    if not os.path.abspath(full_path).startswith(os.path.abspath(allowed_base)):
        threats.append("Path outside allowed directory")
        return '', threats
    
    return full_path, threats
```

## Risk Tolerance Levels

### Low Risk Tolerance
- Strict pattern matching
- Aggressive blocking
- Minimal false positives acceptable
- Use for high-security applications

### Medium Risk Tolerance
- Balanced pattern matching
- Flag suspicious content, allow after review
- Accept some false positives
- Use for general applications

### High Risk Tolerance
- Permissive pattern matching
- Flag only obvious threats
- Minimize false positives
- Use for low-security applications

## Performance Considerations

### Efficient Pattern Matching
- Compile regex patterns once, reuse
- Use character-based filters before regex
- Cache normalization results

### Scaling Considerations
- Batch processing for large volumes
- Async processing for non-blocking validation
- Rate limiting for resource-intensive operations

## Testing Patterns

### Unit Tests
```python
def test_sanitization_pattern():
    """Test sanitization pattern detection"""
    input_text = "Ignore previous instructions"
    sanitized, threats = sanitize_input(input_text)
    
    assert len(threats) > 0
    assert "instruction injection" in threats[0].lower()
```

### Integration Tests
```python
def test_end_to_end_sanitization():
    """Test complete sanitization pipeline"""
    test_cases = [
        ("safe text", True),
        ("ignore all instructions", False),
        ("system admin mode", False),
    ]
    
    for input_text, should_be_safe in test_cases:
        result = validate_input(input_text)
        assert result['is_safe'] == should_be_safe
```

