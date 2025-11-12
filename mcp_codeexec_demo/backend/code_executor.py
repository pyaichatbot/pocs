"""
Code Executor - Sandboxed Python execution environment for agent-generated code.

This implements the code execution pattern from:
https://www.anthropic.com/engineering/code-execution-with-mcp

Phase 1: Enhanced with network and filesystem policy enforcement.
"""
import os
import sys
import subprocess
import tempfile
import resource
import signal
from pathlib import Path
from typing import Dict, Any, Optional
import json
import asyncio
import time

# Import Phase 1 security policies
try:
    from security.network_policy import NetworkPolicy, NetworkPolicyViolation
    from security.filesystem_policy import FileSystemPolicy, FileSystemViolation
except ImportError:
    # Fallback if security module not available
    NetworkPolicy = None
    NetworkPolicyViolation = None
    FileSystemPolicy = None
    FileSystemViolation = None

# Import Phase 1 observability
try:
    from observability.logging_decorator import log_execution, LogLevel
    OBSERVABILITY_AVAILABLE = True
except ImportError:
    OBSERVABILITY_AVAILABLE = False
    LogLevel = None
    
    def log_execution(*args, **kwargs):
        def decorator(func):
            return func
        return decorator

# Use absolute path for consistent working directory
# Get backend directory (where this file is located)
BACKEND_DIR = Path(__file__).parent.absolute()
WORKSPACE_DIR = BACKEND_DIR / "workspace"
WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)
SERVERS_DIR = WORKSPACE_DIR / "servers"
SKILLS_DIR = WORKSPACE_DIR / "skills"
SKILLS_DIR.mkdir(parents=True, exist_ok=True)
# Create __init__.py to make skills a proper Python package
(SKILLS_DIR / "__init__.py").touch(exist_ok=True)


class CodeExecutor:
    """Sandboxed Python code executor for agent-generated code.
    
    Phase 1: Enhanced with network and filesystem policy enforcement.
    
    Includes enhanced security sandboxing:
    - Resource limits (CPU, memory)
    - Timeout protection
    - Process isolation
    - Network egress controls
    - File system restrictions
    """
    
    def __init__(
        self, 
        workspace_dir: Path = WORKSPACE_DIR, 
        timeout: int = 30,
        max_memory_mb: int = 512,
        max_cpu_seconds: int = 30,
        enforce_network_policy: bool = True,
        enforce_filesystem_policy: bool = True
    ):
        """Initialize code executor with security policies.
        
        Args:
            workspace_dir: Workspace directory for code execution
            timeout: Execution timeout in seconds
            max_memory_mb: Maximum memory in MB
            max_cpu_seconds: Maximum CPU time in seconds
            enforce_network_policy: Whether to enforce network egress controls
            enforce_filesystem_policy: Whether to enforce filesystem restrictions
        """
        self.workspace = workspace_dir
        self.timeout = timeout
        self.max_memory_mb = max_memory_mb
        self.max_cpu_seconds = max_cpu_seconds
        self.workspace.mkdir(parents=True, exist_ok=True)
        
        # Add workspace to Python path for imports
        self.python_path = str(self.workspace.absolute())
        
        # Phase 1: Initialize security policies
        self.enforce_network_policy = enforce_network_policy and NetworkPolicy is not None
        self.enforce_filesystem_policy = enforce_filesystem_policy and FileSystemPolicy is not None
        
        if self.enforce_network_policy:
            self.network_policy = NetworkPolicy()
        
        if self.enforce_filesystem_policy:
            self.filesystem_policy = FileSystemPolicy(workspace_dir, allow_writes=True)
    
    @log_execution(log_level=LogLevel.INFO if OBSERVABILITY_AVAILABLE and LogLevel else None, log_parameters=False, log_results=True)  # Don't log code (may be large)
    async def execute(
        self, 
        code: str, 
        capture_output: bool = True
    ) -> Dict[str, Any]:
        """Execute Python code in a sandboxed environment.
        
        Phase 1: Enhanced with network and filesystem policy enforcement.
        Phase 1: Instrumented with logging decorator for observability.
        
        Args:
            code: Python code to execute (can import from servers/ directory)
            capture_output: Whether to capture stdout/stderr
            
        Returns:
            Dict with 'stdout', 'stderr', 'result', 'error'
        """
        # Create temporary file for code
        with tempfile.NamedTemporaryFile(
            mode='w', 
            suffix='.py', 
            delete=False,
            dir=self.workspace
        ) as f:
            script_path = Path(f.name)
            
            # Wrap code to capture result
            # Enable filesystem access for progressive disclosure (blog post pattern)
            backend_path = Path(__file__).parent.absolute()
            workspace_abs = self.workspace.absolute()
            
            # Phase 1: Add network and filesystem policy enforcement code
            network_policy_code = ""
            filesystem_policy_code = ""
            
            if self.enforce_network_policy:
                allowed_endpoints = self.network_policy.get_allowed_endpoints()
                network_policy_code = f'''
# Phase 1: Network egress controls
import socket
_original_socket = socket.socket
_allowed_endpoints = {allowed_endpoints}
_localhost_addresses = ['127.0.0.1', 'localhost', '::1', '0.0.0.0']

def _patched_socket(*args, **kwargs):
    sock = _original_socket(*args, **kwargs)
    original_connect = sock.connect
    
    def _patched_connect(address):
        host, port = address[0], address[1] if len(address) > 1 else None
        
        # Always allow localhost connections (needed for asyncio event loop)
        if host in _localhost_addresses:
            return original_connect(address)
        
        # Check if endpoint is allowed
        allowed = False
        for endpoint in _allowed_endpoints:
            if ':' in endpoint:
                endpoint_host, endpoint_port = endpoint.split(':', 1)
                if host == endpoint_host and (port is None or str(port) == endpoint_port):
                    allowed = True
                    break
            elif host == endpoint:
                allowed = True
                break
        
        if not allowed:
            raise Exception(f"Network access to {{host}}:{{port}} is blocked by security policy. Only allowed endpoints: {{', '.join(_allowed_endpoints)}}")
        
        return original_connect(address)
    
    # Try to patch connect, but handle read-only attributes gracefully
    # Some sockets (e.g., from socketpair for asyncio) have read-only attributes
    try:
        sock.connect = _patched_connect
    except (AttributeError, TypeError):
        # Socket has read-only attributes - this is likely an asyncio internal socket
        # Allow it to proceed without patching (asyncio uses localhost anyway)
        pass
    
    return sock

socket.socket = _patched_socket
'''
            
            if self.enforce_filesystem_policy:
                workspace_str = str(workspace_abs)
                filesystem_policy_code = f'''
# Phase 1: File system restrictions
import builtins
_original_open = builtins.open
_workspace_dir = r"{workspace_str}"
_restricted_dirs = ['/etc', '/home', '/var', '/usr', '/bin', '/sbin', '/sys', '/proc', '/dev', '/root', '/boot', '/lib']

def _patched_open(file, mode='r', *args, **kwargs):
    from pathlib import Path
    resolved_path = Path(file).resolve()
    
    # Block restricted system directories
    for restricted in _restricted_dirs:
        if str(resolved_path).startswith(restricted):
            raise Exception(f"File access to '{{file}}' is blocked - restricted system directory")
    
    # Ensure path is within workspace
    try:
        resolved_path.relative_to(_workspace_dir)
    except ValueError:
        raise Exception(f"File access to '{{file}}' is blocked - outside workspace directory")
    
    return _original_open(file, mode, *args, **kwargs)

builtins.open = _patched_open
'''
            
            wrapped_code = f'''import sys
import json
import asyncio
import os
import resource
from pathlib import Path

# Set resource limits for security sandboxing
try:
    # Memory limit (in bytes)
    memory_limit = {self.max_memory_mb * 1024 * 1024}
    resource.setrlimit(resource.RLIMIT_AS, (memory_limit, memory_limit))
    
    # CPU time limit (in seconds)
    cpu_limit = {self.max_cpu_seconds}
    resource.setrlimit(resource.RLIMIT_CPU, (cpu_limit, cpu_limit))
except (OSError, ValueError):
    # Resource limits may not be available on all systems
    pass

{network_policy_code}

{filesystem_policy_code}

# Add workspace, servers, skills, and backend to path for imports
# Note: workspace is added so 'servers' and 'skills' can be imported as packages
sys.path.insert(0, r"{self.python_path}")
sys.path.insert(0, r"{str(SERVERS_DIR.absolute())}")
sys.path.insert(0, r"{str(backend_path)}")

# Change to workspace directory for filesystem operations
os.chdir(r"{str(workspace_abs)}")

# Import backend modules
from tool_client import get_tool_client
from providers.base import ToolResult

async def _main():
    # Initialize result variables to None
    # These will be set by the agent's code if it assigns to _result or result
    _result = None
    result = None
    
    try:
        # User code - executed in this scope, so _result will be accessible
        # The code is inserted here, so any assignment to _result or result will modify these variables
{self._indent_code(code)}
        
        # Capture any return value
        # Since we're in the same function scope, variables set by the code are directly accessible
        # Check _result first (preferred), then result (fallback)
        final_result = _result if _result is not None else (result if result is not None else None)
        
        return {{
            "success": True,
            "result": final_result,
            "stdout": "",
            "stderr": ""
        }}
    except Exception as e:
        import traceback
        return {{
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__,
            "traceback": traceback.format_exc(),
            "stdout": "",
            "stderr": str(e)
        }}

if __name__ == "__main__":
    result = asyncio.run(_main())
    print(json.dumps(result))
'''
            f.write(wrapped_code)
        
        try:
            # Execute in subprocess with timeout
            # Set working directory to workspace for filesystem operations
            process = await asyncio.create_subprocess_exec(
                sys.executable,
                str(script_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(self.workspace.absolute()),
                env={**os.environ, "PYTHONPATH": f"{self.python_path}:{str(SERVERS_DIR.absolute())}"}
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=self.timeout
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return {
                    "success": False,
                    "error": f"Execution timeout after {self.timeout}s",
                    "stdout": "",
                    "stderr": ""
                }
            
            stdout_str = stdout.decode('utf-8', errors='replace')
            stderr_str = stderr.decode('utf-8', errors='replace')
            
            # Try to parse JSON result
            try:
                result = json.loads(stdout_str.strip().split('\n')[-1])
                return result
            except (json.JSONDecodeError, IndexError):
                # Fallback if no JSON output
                return {
                    "success": True,
                    "result": None,
                    "stdout": stdout_str,
                    "stderr": stderr_str
                }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__,
                "stdout": "",
                "stderr": str(e)
            }
        finally:
            # Clean up temp file
            try:
                script_path.unlink()
            except Exception:
                pass
    
    def _indent_code(self, code: str) -> str:
        """Indent code block for insertion into function."""
        lines = code.split('\n')
        if not lines:
            return ""
        # Check if first line needs indentation
        if lines[0].strip() and not lines[0].startswith(' '):
            return '\n'.join('        ' + line if line.strip() else line for line in lines)
        return code
    
    def list_available_tools(self) -> Dict[str, Any]:
        """List available tools by exploring filesystem.
        
        Returns:
            Dict with server names and their tools, including error information
        """
        tools_info = {
            "servers": {},
            "errors": [],
            "servers_dir": str(SERVERS_DIR),
            "workspace_dir": str(WORKSPACE_DIR)
        }
        
        if not SERVERS_DIR.exists():
            tools_info["errors"].append(
                f"Servers directory does not exist: {SERVERS_DIR}. "
                f"Tools may not have been generated. Check backend startup logs."
            )
            return tools_info
        
        if not any(SERVERS_DIR.iterdir()):
            tools_info["errors"].append(
                f"Servers directory is empty: {SERVERS_DIR}. "
                f"No MCP servers found. Check MCP server connection and tool generation."
            )
            return tools_info
        
        for server_dir in SERVERS_DIR.iterdir():
            if not server_dir.is_dir():
                continue
                
            server_name = server_dir.name
            init_file = server_dir / "__init__.py"
            
            if not init_file.exists():
                tools_info["errors"].append(
                    f"Server '{server_name}' missing __init__.py at {init_file}. "
                    f"Tool generation may have failed for this server."
                )
                continue
            
            tool_files = [
                f.stem for f in server_dir.glob("*.py") 
                if f.name != "__init__.py"
            ]
            
            if not tool_files:
                tools_info["errors"].append(
                    f"Server '{server_name}' has no tool files (only __init__.py). "
                    f"Expected tool files in {server_dir}"
                )
            
            tools_info["servers"][server_name] = {
                "tools": tool_files,
                "path": str(server_dir.relative_to(WORKSPACE_DIR)),
                "absolute_path": str(server_dir),
                "tool_count": len(tool_files)
            }
        
        return tools_info
    
    def verify_tool_exists(self, server_name: str, tool_name: str) -> Dict[str, Any]:
        """Verify that a specific tool exists in the filesystem.
        
        Args:
            server_name: Name of the server
            tool_name: Name of the tool (Python-safe name)
            
        Returns:
            Dict with verification result and helpful error messages
        """
        result = {
            "exists": False,
            "server_dir": None,
            "tool_file": None,
            "errors": [],
            "suggestions": []
        }
        
        if not SERVERS_DIR.exists():
            result["errors"].append(
                f"Servers directory does not exist: {SERVERS_DIR}. "
                f"Tools may not have been generated during backend startup."
            )
            result["suggestions"].append("Check backend startup logs for tool generation errors")
            return result
        
        server_dir = SERVERS_DIR / server_name
        if not server_dir.exists():
            available_servers = [d.name for d in SERVERS_DIR.iterdir() if d.is_dir()]
            result["errors"].append(
                f"Server '{server_name}' not found in {SERVERS_DIR}. "
                f"Available servers: {', '.join(available_servers) if available_servers else 'none'}"
            )
            if available_servers:
                result["suggestions"].append(f"Did you mean one of: {', '.join(available_servers)}?")
            return result
        
        result["server_dir"] = str(server_dir)
        
        # Try different possible tool file names
        possible_names = [
            tool_name,
            tool_name.replace("-", "_"),
            tool_name.replace(".", "_")
        ]
        
        tool_file = None
        for name in possible_names:
            candidate = server_dir / f"{name}.py"
            if candidate.exists():
                tool_file = candidate
                break
        
        if not tool_file:
            # List available tools in this server
            available_tools = [
                f.stem for f in server_dir.glob("*.py") 
                if f.name != "__init__.py"
            ]
            result["errors"].append(
                f"Tool '{tool_name}' not found in server '{server_name}'. "
                f"Available tools: {', '.join(available_tools) if available_tools else 'none'}"
            )
            if available_tools:
                result["suggestions"].append(
                    f"Did you mean one of: {', '.join(available_tools)}? "
                    f"Or check the tool name spelling (use underscores, not hyphens)"
                )
            return result
        
        result["tool_file"] = str(tool_file)
        result["exists"] = True
        return result

