#!/usr/bin/env python3
"""
OpenAI Codex Client Script
A utility script for interacting with OpenAI Codex API
"""

import openai
import json
import sys
from typing import Optional, Dict, Any

class CodexClient:
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the Codex client with API key"""
        if api_key:
            openai.api_key = api_key
        else:
            # Try to load from environment or config
            import os
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                raise ValueError("OpenAI API key not found. Set OPENAI_API_KEY environment variable or pass api_key parameter.")
            openai.api_key = api_key
    
    def generate_code(self, 
                     prompt: str, 
                     language: str = "python",
                     max_tokens: int = 1000,
                     temperature: float = 0.1,
                     engine: str = "code-davinci-002") -> str:
        """
        Generate code using OpenAI Codex
        
        Args:
            prompt: The prompt describing what code to generate
            language: Programming language (python, javascript, java, etc.)
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0 to 1.0)
            engine: OpenAI engine to use
            
        Returns:
            Generated code as string
        """
        try:
            response = openai.Completion.create(
                engine=engine,
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                stop=["\n\n\n", "```"]
            )
            return response.choices[0].text.strip()
        except Exception as e:
            print(f"Error generating code: {e}", file=sys.stderr)
            return ""
    
    def complete_code(self, 
                     code: str, 
                     language: str = "python",
                     max_tokens: int = 500) -> str:
        """
        Complete existing code using Codex
        
        Args:
            code: Partial code to complete
            language: Programming language
            max_tokens: Maximum tokens to generate
            
        Returns:
            Completed code as string
        """
        prompt = f"# {language}\n{code}\n\n# Complete the above code:\n"
        return self.generate_code(prompt, language, max_tokens)
    
    def explain_code(self, code: str, language: str = "python") -> str:
        """
        Generate explanation for code using Codex
        
        Args:
            code: Code to explain
            language: Programming language
            
        Returns:
            Code explanation as string
        """
        prompt = f"# {language}\n{code}\n\n# Explain what this code does:\n"
        return self.generate_code(prompt, language, 300)
    
    def debug_code(self, code: str, error_message: str = "", language: str = "python") -> str:
        """
        Debug code using Codex
        
        Args:
            code: Code with potential issues
            error_message: Error message if available
            language: Programming language
            
        Returns:
            Debugged code as string
        """
        prompt = f"# {language}\n{code}\n\n"
        if error_message:
            prompt += f"# Error: {error_message}\n"
        prompt += "# Fix the bugs in the above code:\n"
        return self.generate_code(prompt, language, 800)
    
    def optimize_code(self, code: str, language: str = "python") -> str:
        """
        Optimize code for performance using Codex
        
        Args:
            code: Code to optimize
            language: Programming language
            
        Returns:
            Optimized code as string
        """
        prompt = f"# {language}\n{code}\n\n# Optimize this code for better performance:\n"
        return self.generate_code(prompt, language, 800)

def main():
    """Command line interface for Codex client"""
    import argparse
    
    parser = argparse.ArgumentParser(description="OpenAI Codex Client")
    parser.add_argument("--prompt", required=True, help="Code generation prompt")
    parser.add_argument("--language", default="python", help="Programming language")
    parser.add_argument("--max-tokens", type=int, default=1000, help="Maximum tokens")
    parser.add_argument("--temperature", type=float, default=0.1, help="Sampling temperature")
    parser.add_argument("--action", choices=["generate", "complete", "explain", "debug", "optimize"], 
                       default="generate", help="Action to perform")
    parser.add_argument("--code", help="Existing code for complete/explain/debug/optimize actions")
    parser.add_argument("--error", help="Error message for debug action")
    
    args = parser.parse_args()
    
    try:
        client = CodexClient()
        
        if args.action == "generate":
            result = client.generate_code(args.prompt, args.language, args.max_tokens, args.temperature)
        elif args.action == "complete":
            if not args.code:
                print("Error: --code required for complete action", file=sys.stderr)
                sys.exit(1)
            result = client.complete_code(args.code, args.language, args.max_tokens)
        elif args.action == "explain":
            if not args.code:
                print("Error: --code required for explain action", file=sys.stderr)
                sys.exit(1)
            result = client.explain_code(args.code, args.language)
        elif args.action == "debug":
            if not args.code:
                print("Error: --code required for debug action", file=sys.stderr)
                sys.exit(1)
            result = client.debug_code(args.code, args.error, args.language)
        elif args.action == "optimize":
            if not args.code:
                print("Error: --code required for optimize action", file=sys.stderr)
                sys.exit(1)
            result = client.optimize_code(args.code, args.language)
        
        print(result)
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
