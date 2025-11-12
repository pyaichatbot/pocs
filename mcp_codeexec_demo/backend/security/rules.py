"""
Security Rules Engine - AST-based dangerous pattern detection.

Implements security rules for code validation following SOLID principles:
- Single Responsibility: Each rule type has one responsibility
- Open/Closed: Rules can be extended without modifying core engine
- Liskov Substitution: All rules follow the same interface
- Interface Segregation: Rule interface is minimal and focused
- Dependency Inversion: Engine depends on rule abstractions
"""
import ast
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass
from enum import Enum


class SecurityLevel(Enum):
    """Security violation severity levels."""
    BLOCK = "block"  # Block execution
    WARN = "warn"    # Allow but warn
    INFO = "info"    # Informational


@dataclass
class SecurityViolation:
    """Represents a security violation found in code."""
    rule_name: str
    level: SecurityLevel
    message: str
    line_number: Optional[int] = None
    column: Optional[int] = None
    code_snippet: Optional[str] = None


class SecurityRule(ABC):
    """Abstract base class for security rules.
    
    Follows Open/Closed Principle: New rules can be added without modifying existing code.
    """
    
    @abstractmethod
    def check(self, tree: ast.AST, code: str) -> List[SecurityViolation]:
        """Check code for violations of this rule.
        
        Args:
            tree: Parsed AST of the code
            code: Original source code (for context)
            
        Returns:
            List of security violations found
        """
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Rule name for identification."""
        pass
    
    @property
    @abstractmethod
    def level(self) -> SecurityLevel:
        """Default security level for this rule."""
        pass


class DangerousImportRule(SecurityRule):
    """Blocks dangerous imports that could compromise security."""
    
    # Blocked imports (base modules)
    BLOCKED_IMPORTS: Set[str] = {
        'os', 'subprocess', 'sys', 'socket', 'urllib', 'requests',
        'http', 'ftplib', 'smtplib', 'telnetlib', 'pickle', 'marshal',
        'ctypes', 'multiprocessing', 'threading', 'concurrent.futures'
    }
    
    # Allowed imports (whitelist approach)
    ALLOWED_IMPORTS: Set[str] = {
        'json', 'pathlib', 'typing', 'collections', 'itertools',
        'functools', 'datetime', 'time', 'math', 'random', 'string',
        'csv', 're', 'io', 'asyncio', 'servers',  # servers.* is allowed
        'importlib', 'inspect',  # Needed for tool discovery and introspection
        'pkgutil', 'ast'  # Additional introspection modules
    }
    
    def check(self, tree: ast.AST, code: str) -> List[SecurityViolation]:
        """Check for dangerous imports."""
        violations = []
        lines = code.split('\n')
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    import_name = alias.name.split('.')[0]
                    if import_name in self.BLOCKED_IMPORTS:
                        violations.append(SecurityViolation(
                            rule_name=self.name,
                            level=self.level,
                            message=f"Dangerous import blocked: {alias.name}",
                            line_number=node.lineno if hasattr(node, 'lineno') else None,
                            code_snippet=lines[node.lineno - 1] if hasattr(node, 'lineno') and node.lineno <= len(lines) else None
                        ))
                    elif import_name not in self.ALLOWED_IMPORTS and not alias.name.startswith('servers.'):
                        # Warn on unknown imports
                        violations.append(SecurityViolation(
                            rule_name=self.name,
                            level=SecurityLevel.WARN,
                            message=f"Unknown import: {alias.name}",
                            line_number=node.lineno if hasattr(node, 'lineno') else None,
                            code_snippet=lines[node.lineno - 1] if hasattr(node, 'lineno') and node.lineno <= len(lines) else None
                        ))
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    module_base = node.module.split('.')[0]
                    if module_base in self.BLOCKED_IMPORTS:
                        violations.append(SecurityViolation(
                            rule_name=self.name,
                            level=self.level,
                            message=f"Dangerous import blocked: from {node.module}",
                            line_number=node.lineno if hasattr(node, 'lineno') else None,
                            code_snippet=lines[node.lineno - 1] if hasattr(node, 'lineno') and node.lineno <= len(lines) else None
                        ))
                    elif module_base not in self.ALLOWED_IMPORTS and not node.module.startswith('servers.'):
                        violations.append(SecurityViolation(
                            rule_name=self.name,
                            level=SecurityLevel.WARN,
                            message=f"Unknown import: from {node.module}",
                            line_number=node.lineno if hasattr(node, 'lineno') else None,
                            code_snippet=lines[node.lineno - 1] if hasattr(node, 'lineno') and node.lineno <= len(lines) else None
                        ))
        
        return violations
    
    @property
    def name(self) -> str:
        return "dangerous_import"
    
    @property
    def level(self) -> SecurityLevel:
        return SecurityLevel.BLOCK


class DangerousFunctionCallRule(SecurityRule):
    """Blocks dangerous function calls."""
    
    DANGEROUS_FUNCTIONS: Set[str] = {
        'eval', 'exec', 'compile', '__import__', 'open', 'input',
        'raw_input', 'execfile', 'reload', 'getattr', 'setattr',
        'delattr', 'hasattr', 'globals', 'locals', 'vars', 'dir'
    }
    
    DANGEROUS_ATTRIBUTES: Set[str] = {
        'os.system', 'os.popen', 'os.spawn', 'subprocess.run',
        'subprocess.call', 'subprocess.Popen', 'sys.exit', 'sys.modules'
    }
    
    def check(self, tree: ast.AST, code: str) -> List[SecurityViolation]:
        """Check for dangerous function calls."""
        violations = []
        lines = code.split('\n')
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                # Check direct function calls
                if isinstance(node.func, ast.Name):
                    if node.func.id in self.DANGEROUS_FUNCTIONS:
                        violations.append(SecurityViolation(
                            rule_name=self.name,
                            level=self.level,
                            message=f"Dangerous function call blocked: {node.func.id}()",
                            line_number=node.lineno if hasattr(node, 'lineno') else None,
                            code_snippet=lines[node.lineno - 1] if hasattr(node, 'lineno') and node.lineno <= len(lines) else None
                        ))
                
                # Check attribute access (e.g., os.system)
                elif isinstance(node.func, ast.Attribute):
                    attr_path = self._get_attribute_path(node.func)
                    if attr_path in self.DANGEROUS_ATTRIBUTES:
                        violations.append(SecurityViolation(
                            rule_name=self.name,
                            level=self.level,
                            message=f"Dangerous function call blocked: {attr_path}()",
                            line_number=node.lineno if hasattr(node, 'lineno') else None,
                            code_snippet=lines[node.lineno - 1] if hasattr(node, 'lineno') and node.lineno <= len(lines) else None
                        ))
        
        return violations
    
    def _get_attribute_path(self, node: ast.Attribute) -> str:
        """Get full attribute path (e.g., 'os.system')."""
        parts = []
        current = node
        while isinstance(current, ast.Attribute):
            parts.append(current.attr)
            current = current.value
        if isinstance(current, ast.Name):
            parts.append(current.id)
        return '.'.join(reversed(parts))
    
    @property
    def name(self) -> str:
        return "dangerous_function_call"
    
    @property
    def level(self) -> SecurityLevel:
        return SecurityLevel.BLOCK


class FileSystemAccessRule(SecurityRule):
    """Warns about file system access patterns."""
    
    RESTRICTED_PATHS: Set[str] = {
        '/etc', '/home', '/var', '/usr', '/bin', '/sbin',
        '/sys', '/proc', '/dev', '/root', '/boot', '/lib'
    }
    
    def check(self, tree: ast.AST, code: str) -> List[SecurityViolation]:
        """Check for restricted file system access."""
        violations = []
        lines = code.split('\n')
        
        # Check for string literals that look like restricted paths
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                path = node.value
                # Check if path starts with restricted directory
                for restricted in self.RESTRICTED_PATHS:
                    if path.startswith(restricted):
                        violations.append(SecurityViolation(
                            rule_name=self.name,
                            level=SecurityLevel.WARN,
                            message=f"Potential access to restricted path: {path}",
                            line_number=node.lineno if hasattr(node, 'lineno') else None,
                            code_snippet=lines[node.lineno - 1] if hasattr(node, 'lineno') and node.lineno <= len(lines) else None
                        ))
        
        return violations
    
    @property
    def name(self) -> str:
        return "filesystem_access"
    
    @property
    def level(self) -> SecurityLevel:
        return SecurityLevel.WARN


class InfiniteLoopRule(SecurityRule):
    """Detects potential infinite loops."""
    
    def check(self, tree: ast.AST, code: str) -> List[SecurityViolation]:
        """Check for infinite loops."""
        violations = []
        lines = code.split('\n')
        
        for node in ast.walk(tree):
            if isinstance(node, ast.While):
                # Check if it's 'while True:'
                if isinstance(node.test, ast.Constant) and node.test.value is True:
                    # Check if there's a break in the loop body
                    has_break = self._has_break_in_body(node.body)
                    if not has_break:
                        violations.append(SecurityViolation(
                            rule_name=self.name,
                            level=SecurityLevel.WARN,
                            message="Potential infinite loop: 'while True:' without 'break'",
                            line_number=node.lineno if hasattr(node, 'lineno') else None,
                            code_snippet=lines[node.lineno - 1] if hasattr(node, 'lineno') and node.lineno <= len(lines) else None
                        ))
        
        return violations
    
    def _has_break_in_body(self, body: List[ast.AST]) -> bool:
        """Check if body contains a break statement."""
        for node in body:
            if isinstance(node, ast.Break):
                return True
            if isinstance(node, (ast.For, ast.While, ast.If, ast.Try)):
                # Recursively check nested structures
                if isinstance(node, ast.For):
                    if self._has_break_in_body(node.body):
                        return True
                elif isinstance(node, ast.While):
                    if self._has_break_in_body(node.body):
                        return True
                elif isinstance(node, ast.If):
                    if self._has_break_in_body(node.body):
                        return True
                    if node.orelse and self._has_break_in_body(node.orelse):
                        return True
                elif isinstance(node, ast.Try):
                    if self._has_break_in_body(node.body):
                        return True
                    if node.orelse and self._has_break_in_body(node.orelse):
                        return True
        return False
    
    @property
    def name(self) -> str:
        return "infinite_loop"
    
    @property
    def level(self) -> SecurityLevel:
        return SecurityLevel.WARN


class SecurityRuleEngine:
    """Security rules engine that applies all rules to code.
    
    Follows Single Responsibility Principle: Only responsible for running rules.
    Follows Dependency Inversion: Depends on SecurityRule abstraction.
    """
    
    def __init__(self, rules: Optional[List[SecurityRule]] = None):
        """Initialize with security rules.
        
        Args:
            rules: List of security rules. If None, uses default rules.
        """
        self.rules = rules or self._get_default_rules()
    
    def _get_default_rules(self) -> List[SecurityRule]:
        """Get default security rules."""
        return [
            DangerousImportRule(),
            DangerousFunctionCallRule(),
            FileSystemAccessRule(),
            InfiniteLoopRule(),
        ]
    
    def validate(self, code: str) -> Dict[str, Any]:
        """Validate code against all security rules.
        
        Args:
            code: Python code to validate
            
        Returns:
            Dict with validation results:
            {
                "valid": bool,
                "blocked": bool,  # True if any BLOCK violations
                "violations": List[SecurityViolation],
                "blocking_violations": List[SecurityViolation],
                "warnings": List[SecurityViolation],
                "info": List[SecurityViolation]
            }
        """
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return {
                "valid": False,
                "blocked": True,
                "violations": [],
                "blocking_violations": [],
                "warnings": [],
                "info": [],
                "syntax_error": str(e)
            }
        
        all_violations = []
        
        # Run all rules
        for rule in self.rules:
            violations = rule.check(tree, code)
            all_violations.extend(violations)
        
        # Categorize violations by level
        blocking = [v for v in all_violations if v.level == SecurityLevel.BLOCK]
        warnings = [v for v in all_violations if v.level == SecurityLevel.WARN]
        info = [v for v in all_violations if v.level == SecurityLevel.INFO]
        
        return {
            "valid": len(blocking) == 0,
            "blocked": len(blocking) > 0,
            "violations": all_violations,
            "blocking_violations": blocking,
            "warnings": warnings,
            "info": info
        }


# Convenience class for backward compatibility
class SecurityRules:
    """Convenience wrapper for SecurityRuleEngine."""
    
    def __init__(self):
        self.engine = SecurityRuleEngine()
    
    def validate(self, code: str) -> Dict[str, Any]:
        """Validate code against security rules."""
        return self.engine.validate(code)

