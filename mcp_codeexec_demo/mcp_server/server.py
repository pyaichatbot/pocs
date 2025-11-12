import os
import random
from mcp.server.fastmcp import FastMCP
from mcp.types import TextContent, CallToolResult

PORT = int(os.getenv("MCP_PORT", "8974"))
HOST = os.getenv("MCP_HOST", "0.0.0.0")  # Use 0.0.0.0 for Docker

mcp = FastMCP("demo-mcp", host=HOST, port=PORT)

LOREM_WORDS = (
    "alpha beta gamma delta epsilon zeta eta theta iota kappa lambda mu nu xi omicron "
    "pi rho sigma tau upsilon phi chi psi omega "
    "market revenue pipeline churn upsell roadmap velocity stakeholder KPI synergy "
    "payment rails ledger settlement interchange risk KYC AML compliance acquirer issuer"
).split()

def generate_text(topic: str, words: int) -> str:
    header = f"Transcript for {topic}. "
    body = " ".join(random.choice(LOREM_WORDS) for _ in range(max(50, words)))
    return header + body

@mcp.tool()
def get_transcript(topic: str, words: int = 3000) -> CallToolResult:
    """Return a long, synthetic transcript on the topic."""
    text = generate_text(topic, words)
    return CallToolResult(
        content=[TextContent(type="text", text=text)],
        isError=False,
        _meta={"size_words": words}
    )

@mcp.tool()
def update_crm(record_id: str, note: str) -> CallToolResult:
    """Pretend to update a CRM record with an executive note."""
    msg = f"Updated record {record_id} with note length={len(note)}"
    return CallToolResult(content=[TextContent(type="text", text=msg)], isError=False)

@mcp.tool()
def search_tools(query: str, detail_level: str = "name") -> CallToolResult:
    """
    Search for tools matching a query.
    
    This implements the search_tools pattern from the blog post, allowing
    agents to find relevant tool definitions with configurable detail levels.
    
    Args:
        query: Search query (e.g., "transcript", "crm", "update")
        detail_level: Level of detail - "name" | "description" | "full"
    
    Returns:
        Matching tools with requested detail level
    """
    # Get all available tools
    all_tools = [
        {
            "name": "get_transcript",
            "description": "Return a long, synthetic transcript on the topic.",
            "parameters": {
                "topic": {"type": "string", "description": "Topic to generate transcript for"},
                "words": {"type": "integer", "description": "Number of words", "default": 3000}
            }
        },
        {
            "name": "update_crm",
            "description": "Pretend to update a CRM record with an executive note.",
            "parameters": {
                "record_id": {"type": "string", "description": "CRM record ID"},
                "note": {"type": "string", "description": "Note to add to record"}
            }
        }
    ]
    
    # Search for matching tools
    query_lower = query.lower()
    matches = []
    for tool in all_tools:
        if (query_lower in tool["name"].lower() or 
            query_lower in tool["description"].lower()):
            match = {"name": tool["name"]}
            
            if detail_level in ["description", "full"]:
                match["description"] = tool["description"]
            
            if detail_level == "full":
                match["parameters"] = tool["parameters"]
            
            matches.append(match)
    
    result_text = f"Found {len(matches)} matching tools:\n"
    for match in matches:
        result_text += f"\n- {match['name']}"
        if "description" in match:
            result_text += f": {match['description']}"
        if "parameters" in match:
            result_text += f"\n  Parameters: {', '.join(match['parameters'].keys())}"
    
    return CallToolResult(
        content=[TextContent(type="text", text=result_text)],
        isError=False
    )

if __name__ == "__main__":
    # Expose Streamable HTTP for easy local calls
    # FastMCP.run() uses settings.host and settings.port configured in __init__
    import asyncio
    asyncio.run(mcp.run_streamable_http_async())
