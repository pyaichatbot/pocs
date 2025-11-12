"""Main FastAPI application - Thin orchestration layer.

Single Responsibility: HTTP request handling and routing.
Business logic is delegated to services and handlers.
"""
import os
import json
import warnings
from typing import Literal, Optional, Dict, Any
from fastapi import FastAPI
from pydantic import BaseModel

# Import observability
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

# Suppress Pydantic warnings
warnings.filterwarnings("ignore", category=UserWarning, module="pydantic")

# Import services and handlers
from services.llm_service import LLMService
from services.intent_detector import IntentDetector
from handlers.prompt_tools_handler import PromptToolsHandler
from handlers.tool_query_handler import ToolQueryHandler
from handlers.generic_task_handler import GenericTaskHandler
from code_executor import CodeExecutor
from code_validator import CodeValidator
from tool_generator import generate_tool_files
from tool_client import ToolClient, set_tool_client
from providers.factory import create_tool_provider
from utils.token_estimator import estimate_tokens

# Tool provider configuration
TOOL_PROVIDER_TYPE = os.getenv("TOOL_PROVIDER", "mcp").lower()

# LLM configuration
LLM_TIMEOUT = int(os.getenv("LLM_TIMEOUT", "120"))


def detect_llm_provider() -> Optional[Literal["azure", "anthropic", "openai"]]:
    """Detect which LLM provider is available."""
    try:
        from litellm import completion
    except Exception:
        return None
    
    if os.getenv("ANTHROPIC_API_KEY"):
        return "anthropic"
    
    azure_key = os.getenv("AZURE_API_KEY") or os.getenv("OPENAI_API_KEY")
    azure_base = os.getenv("AZURE_API_BASE")
    if azure_key and azure_base:
        return "azure"
    
    if os.getenv("OPENAI_API_KEY") and not azure_base:
        return "openai"
    
    return None


def get_default_model(provider: Optional[str]) -> str:
    """Get default model based on provider."""
    model_id = os.getenv("MODEL_ID", "").strip()
    
    if provider == "anthropic":
        return model_id if model_id else "claude-sonnet-4-20250514"
    elif provider == "azure":
        if not model_id:
            model_id = "gpt-4o-mini"
        if not model_id.startswith("azure/"):
            return f"azure/{model_id}"
        return model_id
    elif provider == "openai":
        return model_id if model_id else "gpt-4o-mini"
    else:
        return "gpt-4o-mini"


# Initialize global configuration
LLM_PROVIDER = detect_llm_provider()
DEFAULT_MODEL = get_default_model(LLM_PROVIDER)

# Global service instances (initialized on startup)
llm_service: Optional[LLMService] = None
intent_detector: Optional[IntentDetector] = None
prompt_tools_handler: Optional[PromptToolsHandler] = None
tool_query_handler: Optional[ToolQueryHandler] = None
generic_task_handler: Optional[GenericTaskHandler] = None

app = FastAPI(title="MCP CodeExec vs PromptTools Demo")


@app.on_event("startup")
async def startup_event():
    """Initialize services and generate tool files on startup."""
    global llm_service, intent_detector, prompt_tools_handler, tool_query_handler, generic_task_handler
    
    # Log LLM configuration
    if LLM_PROVIDER:
        print(f"✅ LLM Provider: {LLM_PROVIDER}")
        print(f"✅ Model: {DEFAULT_MODEL}")
        if LLM_PROVIDER == "azure":
            print(f"✅ Azure API Base: {os.getenv('AZURE_API_BASE', 'Not set')}")
    else:
        print("⚠️  No LLM provider detected - using stubbed responses")
        print("   Set ANTHROPIC_API_KEY (for Anthropic) or AZURE_API_KEY + AZURE_API_BASE (for Azure OpenAI)")
    
    # Initialize tool provider
    try:
        print(f"🔧 Initializing tool provider: {TOOL_PROVIDER_TYPE}")
        provider = create_tool_provider()
        provider_config = provider.get_provider_config()
        print(f"✅ Tool Provider: {provider.get_provider_name()}")
        print(f"   Config: {json.dumps(provider_config, indent=2)}")
        
        # Initialize tool client
        tool_client = ToolClient(provider)
        set_tool_client(tool_client)
        print("✅ Tool client initialized")
    except Exception as e:
        import traceback
        print(f"❌ Failed to initialize tool provider: {e}")
        print(f"   Traceback: {traceback.format_exc()}")
        raise
    
    # Generate tool files
    try:
        print("🔧 Generating filesystem-based tool files...")
        tool_info = await generate_tool_files(provider)
        print(f"✅ Generated {tool_info['total_tools']} tools across {tool_info['server_count']} server(s)")
        print(f"📁 Workspace directory: {tool_info['workspace_dir']}")
        print(f"📁 Servers directory: {tool_info['servers_dir']}")
        
        # Verify tool generation
        all_verified = True
        for server_name, info in tool_info['servers'].items():
            if info['tool_count'] > 0:
                verification = info.get('verification', {})
                if verification.get('all_files_exist', False):
                    print(f"   ✅ Server '{server_name}': {info['tool_count']} tools ({', '.join(info['tools'])})")
                    print(f"      📄 Generated {len(verification.get('file_paths', []))} files")
                else:
                    all_verified = False
                    print(f"   ⚠️  Server '{server_name}': {info['tool_count']} tools - VERIFICATION FAILED")
                    if verification.get('missing_files'):
                        print(f"      ❌ Missing files: {', '.join(verification['missing_files'])}")
                    if verification.get('errors'):
                        print(f"      ❌ Errors: {', '.join(verification['errors'])}")
        
        if not all_verified:
            print("⚠️  Tool generation verification failed - code execution mode may not work properly")
        else:
            print("✅ All tool files verified successfully")
    except Exception as e:
        import traceback
        print(f"❌ Failed to generate tool files: {e}")
        print(f"   Traceback: {traceback.format_exc()}")
    
    # Initialize services
    llm_service = LLMService(
        provider=LLM_PROVIDER,
        model=DEFAULT_MODEL,
        timeout=LLM_TIMEOUT
    )
    
    intent_detector = IntentDetector(llm_service=llm_service)
    
    # Initialize handlers
    prompt_tools_handler = PromptToolsHandler(llm_service=llm_service)
    
    executor = CodeExecutor()
    validator = CodeValidator()
    tool_query_handler = ToolQueryHandler(executor, validator, llm_service)
    generic_task_handler = GenericTaskHandler(executor, validator, llm_service)


class ChatRequest(BaseModel):
    message: str
    mode: Literal["prompt_tools", "code_exec"]
    topic: Optional[str] = None
    words: Optional[int] = None


class ChatResponse(BaseModel):
    reply: str
    tokens_prompt: int
    tokens_output: int
    mode: str
    debug: Dict[str, Any]
    provider: Optional[str] = None
    model: Optional[str] = None


@app.post("/chat", response_model=ChatResponse)
@log_execution(log_level=LogLevel.INFO if OBSERVABILITY_AVAILABLE and LogLevel else None, log_parameters=True, log_results=True)
async def chat(req: ChatRequest):
    """Handle chat requests - delegates to appropriate handler."""
    if req.mode == "prompt_tools":
        # Delegate to prompt tools handler
        result = await prompt_tools_handler.handle(
            message=req.message,
            topic=req.topic,
            words=req.words,
            model=DEFAULT_MODEL
        )
        
        return ChatResponse(
            reply=result["reply"],
            tokens_prompt=result["tokens_prompt"],
            tokens_output=result["tokens_output"],
            mode=req.mode,
            provider=LLM_PROVIDER,
            model=DEFAULT_MODEL,
            debug=result["debug"]
        )
    
    else:
        # code_exec mode
        # Detect intent
        is_tool_query = await intent_detector.is_tool_query(req.message)
        
        if is_tool_query:
            # Delegate to tool query handler
            result = await tool_query_handler.handle()
            
            # Calculate tokens from actual prompt and generated code
            prompt = result.get("prompt", "")
            generated_code = result.get("generated_code", "")
            tokens_prompt = estimate_tokens(prompt, model=DEFAULT_MODEL)
            tokens_output = estimate_tokens(generated_code, model=DEFAULT_MODEL)
            
            return ChatResponse(
                reply=result["reply"],
                tokens_prompt=tokens_prompt,
                tokens_output=tokens_output,
                mode=req.mode,
                provider=LLM_PROVIDER,
                model=DEFAULT_MODEL,
                debug={
                    "strategy": "code_exec_tool_discovery",
                    "code_executed": result.get("code_executed", False),
                    "exec_success": result.get("exec_success", False),
                    "generated_code": result.get("code_snippet", ""),
                    "available_tools": result.get("available_tools", {}),
                    "tool_errors": result.get("tool_errors", []),
                    "live_llm": llm_service.live_llm if llm_service else False
                }
            )
        else:
            # Delegate to generic task handler
            result = await generic_task_handler.handle(
                task_description=req.message,
                topic=req.topic,
                words=req.words
            )
            
            # Calculate tokens from actual prompt and generated code
            prompt = result.get("prompt", "")
            generated_code = result.get("generated_code", "")
            tokens_prompt = estimate_tokens(prompt, model=DEFAULT_MODEL)
            tokens_output = estimate_tokens(generated_code, model=DEFAULT_MODEL)
            
            # Get debug info
            available_tools_info = result.get("available_tools", {})
            tool_errors = result.get("tool_errors", [])
            
            return ChatResponse(
                reply=result["reply"],
                tokens_prompt=tokens_prompt,
                tokens_output=tokens_output,
                mode=req.mode,
                provider=LLM_PROVIDER,
                model=DEFAULT_MODEL,
                debug={
                    "strategy": "code_exec_filesystem" if result.get("code_executed") else "code_exec_fallback",
                    "generated_code": result.get("code_snippet", ""),
                    "execution_success": result.get("exec_success", False),
                    "available_servers": list(available_tools_info.keys()) if isinstance(available_tools_info, dict) else [],
                    "live_llm": llm_service.live_llm if llm_service else False,
                    "tool_errors": tool_errors
                }
            )
