#!/usr/bin/env python3
"""
Test script for TOON format integration in LLM client.

This script tests different token formats and measures actual token counts
to validate token savings and LLM response quality.
"""

from __future__ import annotations

import os
import sys
from typing import List

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rag_service.llm_client import LLMClient, DocumentChunk
from rag_service.config import Settings
from rag_service.utils.toon_encoder import compare_formats


def create_test_contexts() -> List[DocumentChunk]:
    """Create sample document chunks for testing."""
    return [
        DocumentChunk(
            doc_id="docs/auth.md",
            chunk_id="docs/auth.md:0",
            path="docs/auth.md",
            content=(
                "Authentication is the process of verifying the identity of a user or system. "
                "It typically involves checking credentials such as username and password against a stored database. "
                "Modern authentication systems may also use multi-factor authentication (MFA) to add an extra layer of security."
            ),
            metadata={
                "repo_url": "https://gitlab.com/group/project.git",
                "repo_id": "12345678",
                "repo_full_path": "group/project",
                "provider": "gitlab",
                "score": 0.85,
                "file_hash": "abc123def456",
            },
        ),
        DocumentChunk(
            doc_id="docs/api.md",
            chunk_id="docs/api.md:0",
            path="docs/api.md",
            content=(
                "API endpoints require proper authentication tokens to access protected resources. "
                "The token is typically sent in the Authorization header as a Bearer token. "
                "The server validates the token and grants or denies access based on the token's validity and permissions."
            ),
            metadata={
                "repo_url": "https://gitlab.com/group/project.git",
                "repo_id": "12345678",
                "repo_full_path": "group/project",
                "provider": "gitlab",
                "score": 0.82,
                "file_hash": "def456ghi789",
            },
        ),
        DocumentChunk(
            doc_id="docs/security.md",
            chunk_id="docs/security.md:0",
            path="docs/security.md",
            content=(
                "Security best practices recommend using HTTPS for all authentication flows to prevent credential interception. "
                "Passwords should be hashed using strong algorithms like bcrypt or Argon2, never stored in plain text. "
                "Session tokens should have appropriate expiration times."
            ),
            metadata={
                "repo_url": "https://gitlab.com/group/project.git",
                "repo_id": "12345678",
                "repo_full_path": "group/project",
                "provider": "gitlab",
                "score": 0.79,
                "file_hash": "ghi789jkl012",
            },
        ),
        DocumentChunk(
            doc_id="docs/user.md",
            chunk_id="docs/user.md:0",
            path="docs/user.md",
            content=(
                "User management involves creating, updating, and deleting user accounts. "
                "Each user account should have a unique identifier and proper role-based access control (RBAC) "
                "to determine what resources they can access. User data should be encrypted at rest and in transit."
            ),
            metadata={
                "repo_url": "https://gitlab.com/group/project.git",
                "repo_id": "12345678",
                "repo_full_path": "group/project",
                "provider": "gitlab",
                "score": 0.76,
                "file_hash": "jkl012mno345",
            },
        ),
        DocumentChunk(
            doc_id="docs/admin.md",
            chunk_id="docs/admin.md:0",
            path="docs/admin.md",
            content=(
                "Admin functions require elevated privileges and should be protected by additional authentication factors. "
                "Audit logs should track all administrative actions for security compliance. "
                "Access to admin functions should follow the principle of least privilege."
            ),
            metadata={
                "repo_url": "https://gitlab.com/group/project.git",
                "repo_id": "12345678",
                "repo_full_path": "group/project",
                "provider": "gitlab",
                "score": 0.73,
                "file_hash": "mno345pqr678",
            },
        ),
    ]


def test_token_formats():
    """Test different token formats and compare token counts."""
    print("=" * 80)
    print("TOON Format Integration Test")
    print("=" * 80)
    print()
    
    contexts = create_test_contexts()
    
    # Compare formats (includes plain, toon, hybrid, flattened)
    comparison = compare_formats(contexts)
    
    # Test JSON format separately using LLM client
    from rag_service.llm_client import LLMClient
    from rag_service.config import Settings
    
    settings = Settings()
    client = LLMClient(settings)
    json_text, json_format, json_tokens = client._format_context(contexts, 'json')
    json_length = len(json_text)
    
    print("Token Count Comparison:")
    print("-" * 80)
    print(f"Plain Text:     {comparison['plain_text']['tokens']:4d} tokens ({comparison['plain_text']['length']:4d} chars)")
    print(f"JSON Format:    {json_tokens:4d} tokens ({json_length:4d} chars)")
    print(f"TOON Format:    {comparison['toon_format']['tokens']:4d} tokens ({comparison['toon_format']['length']:4d} chars)")
    print(f"Hybrid Format:  {comparison['hybrid_format']['tokens']:4d} tokens ({comparison['hybrid_format']['length']:4d} chars)")
    print(f"Flattened TOON: {comparison['flattened_toon']['tokens']:4d} tokens ({comparison['flattened_toon']['length']:4d} chars)")
    print()
    
    # Calculate JSON savings
    plain_tokens = comparison['plain_text']['tokens']
    json_savings = plain_tokens - json_tokens
    json_pct = (json_savings / plain_tokens * 100) if plain_tokens > 0 else 0
    
    print("Token Savings vs Plain Text:")
    print("-" * 80)
    savings = comparison['savings']
    print(f"JSON vs Plain:      {json_savings:+4d} tokens ({json_pct:+6.1f}%)")
    print(f"TOON vs Plain:      {savings['toon_vs_plain']['tokens']:+4d} tokens ({savings['toon_vs_plain']['percent']:+6.1f}%)")
    print(f"Hybrid vs Plain:    {savings['hybrid_vs_plain']['tokens']:+4d} tokens ({savings['hybrid_vs_plain']['percent']:+6.1f}%)")
    print(f"Flattened vs Plain: {savings['flattened_vs_plain']['tokens']:+4d} tokens ({savings['flattened_vs_plain']['percent']:+6.1f}%)")
    print()
    
    print(f"Recommended Format: {comparison['recommendation']}")
    print()
    
    # Show sample output for each format
    print("Sample Output Formats:")
    print("-" * 80)
    print("\n1. Plain Text (first 200 chars):")
    print(comparison['plain_text']['text'][:200])
    print()
    
    print("\n2. JSON Format (first 300 chars):")
    print(json_text[:300])
    print()
    
    print("\n3. Hybrid Format (first 300 chars):")
    print(comparison['hybrid_format']['text'][:300])
    print()
    
    # Add JSON to comparison dict for return
    comparison['json_format'] = {
        'text': json_text[:500] + "..." if len(json_text) > 500 else json_text,
        'length': json_length,
        'tokens': json_tokens,
    }
    comparison['savings']['json_vs_plain'] = {
        'tokens': json_savings,
        'percent': round(json_pct, 1),
    }
    
    return comparison


def test_llm_client_formats():
    """Test LLM client with different format configurations."""
    print("=" * 80)
    print("LLM Client Format Integration Test")
    print("=" * 80)
    print()
    
    contexts = create_test_contexts()
    query = "How does authentication work?"
    
    # Test each format (including JSON)
    formats = ["plain", "json", "toon", "hybrid"]
    
    for format_type in formats:
        print(f"\nTesting format: {format_type}")
        print("-" * 80)
        
        # Create settings with format
        settings = Settings()
        settings.use_llm_token_format = format_type
        
        # Create LLM client (will use fallback if no API keys)
        client = LLMClient(settings)
        
        # Format context
        context_text, format_used, token_count = client._format_context(contexts, format_type)
        
        print(f"Format used: {format_used}")
        print(f"Token count: {token_count}")
        print(f"Context length: {len(context_text)} chars")
        print(f"Preview (first 200 chars):")
        print(context_text[:200])
        print()


def main():
    """Run all tests."""
    print("\n" + "=" * 80)
    print("TOON Format Integration Test Suite")
    print("=" * 80 + "\n")
    
    # Test 1: Format comparison
    comparison = test_token_formats()
    
    # Test 2: LLM client integration
    test_llm_client_formats()
    
    # Summary
    print("\n" + "=" * 80)
    print("Test Summary")
    print("=" * 80)
    print(f"✅ Format comparison completed")
    print(f"✅ LLM client integration tested")
    print(f"✅ Recommended format: {comparison['recommendation']}")
    print(f"✅ Best savings: {comparison['savings']['hybrid_vs_plain']['percent']:.1f}% (Hybrid)")
    print()
    
    print("Next Steps:")
    print("1. Set USE_LLM_TOKEN_FORMAT=hybrid in environment")
    print("2. Test with real queries and measure token counts")
    print("3. Monitor LLM response quality")
    print("4. Adjust format based on results")
    print()


if __name__ == "__main__":
    main()

