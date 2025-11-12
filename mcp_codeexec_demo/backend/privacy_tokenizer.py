"""
Privacy Tokenizer - Tokenizes PII before data reaches the model.

Implements privacy-preserving operations as described in the blog post:
https://www.anthropic.com/engineering/code-execution-with-mcp
"""
import re
import uuid
from typing import Any, Dict, List, Union
from collections.abc import Mapping, Iterable


class PrivacyTokenizer:
    """Tokenizes PII in data before sending to model, untokenizes when needed."""
    
    def __init__(self):
        self.token_map: Dict[str, str] = {}  # Maps tokens to original values
        self.reverse_map: Dict[str, str] = {}  # Maps original values to tokens
        
        # PII detection patterns
        self.pii_patterns = [
            # Email addresses
            (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', 'EMAIL'),
            # Phone numbers (US format)
            (r'\b\d{3}-\d{3}-\d{4}\b', 'PHONE'),
            (r'\b\(\d{3}\)\s?\d{3}-\d{4}\b', 'PHONE'),
            (r'\b\d{3}\.\d{3}\.\d{4}\b', 'PHONE'),
            # SSN
            (r'\b\d{3}-\d{2}-\d{4}\b', 'SSN'),
            # Credit card (basic pattern)
            (r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b', 'CARD'),
            # IP addresses
            (r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', 'IP'),
        ]
    
    def _generate_token(self, pii_type: str) -> str:
        """Generate a unique token for PII."""
        token = f"[{pii_type}_{uuid.uuid4().hex[:8].upper()}]"
        return token
    
    def _detect_pii(self, text: str) -> List[tuple]:
        """Detect PII in text and return (match, type) tuples."""
        detected = []
        for pattern, pii_type in self.pii_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                detected.append((match.group(), pii_type))
        return detected
    
    def tokenize(self, data: Any) -> Any:
        """Tokenize PII in data before sending to model.
        
        Args:
            data: Data structure that may contain PII
        
        Returns:
            Data with PII replaced by tokens
        """
        if isinstance(data, str):
            return self._tokenize_string(data)
        elif isinstance(data, dict):
            return {k: self.tokenize(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self.tokenize(item) for item in data]
        else:
            return data
    
    def _tokenize_string(self, text: str) -> str:
        """Tokenize PII in a string."""
        detected = self._detect_pii(text)
        result = text
        
        for original, pii_type in detected:
            if original not in self.reverse_map:
                token = self._generate_token(pii_type)
                self.token_map[token] = original
                self.reverse_map[original] = token
            else:
                token = self.reverse_map[original]
            
            result = result.replace(original, token)
        
        return result
    
    def untokenize(self, data: Any) -> Any:
        """Restore original PII values from tokens.
        
        Args:
            data: Data structure with tokens
        
        Returns:
            Data with tokens replaced by original PII
        """
        if isinstance(data, str):
            return self._untokenize_string(data)
        elif isinstance(data, dict):
            return {k: self.untokenize(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self.untokenize(item) for item in data]
        else:
            return data
    
    def _untokenize_string(self, text: str) -> str:
        """Untokenize PII in a string."""
        result = text
        for token, original in self.token_map.items():
            result = result.replace(token, original)
        return result
    
    def clear(self):
        """Clear tokenization maps (for security/privacy)."""
        self.token_map.clear()
        self.reverse_map.clear()
    
    def get_stats(self) -> Dict[str, int]:
        """Get statistics about tokenized PII."""
        stats = {}
        for token, original in self.token_map.items():
            pii_type = token.split('_')[0].strip('[')
            stats[pii_type] = stats.get(pii_type, 0) + 1
        return stats


# Global tokenizer instance
_tokenizer = PrivacyTokenizer()


def tokenize_data(data: Any) -> Any:
    """Convenience function to tokenize data."""
    return _tokenizer.tokenize(data)


def untokenize_data(data: Any) -> Any:
    """Convenience function to untokenize data."""
    return _tokenizer.untokenize(data)


def get_tokenizer() -> PrivacyTokenizer:
    """Get the global tokenizer instance."""
    return _tokenizer

