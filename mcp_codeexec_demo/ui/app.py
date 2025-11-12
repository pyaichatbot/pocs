import streamlit as st
import requests
import pandas as pd
import os

# Backend URL - use Docker service name if in Docker, otherwise localhost
BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")
MCP_URL = os.getenv("MCP_URL", "http://127.0.0.1:8974/mcp")

# Debug: Log the backend URL being used (only in Docker)
if os.getenv("BACKEND_URL"):
    print(f"[DEBUG] Using BACKEND_URL from environment: {BACKEND_URL}")

st.set_page_config(page_title="MCP CodeExec vs PromptTools", layout="wide")

st.title("MCP: Code Execution vs Prompt-Tools — Token Demo")
st.caption("Toggle modes and observe token consumption.")

# Sidebar controls
st.sidebar.markdown("### Execution Mode")
mode = st.sidebar.toggle(
    "Filesystem-based Code Execution", 
    value=True,
    help="When ON: Agent writes Python code to interact with MCP tools via filesystem. When OFF: Direct tool calls with full data in prompt."
)
st.sidebar.markdown("**Mode:** " + ("🔧 Code Execution (Filesystem)" if mode else "📝 Direct Tool Calls"))
topic = st.sidebar.text_input("Topic", value="quarterly sales")
words = st.sidebar.slider("Transcript size (words)", 500, 8000, 3000, step=500)

if "history" not in st.session_state:
    st.session_state.history = []  # list of dicts

user_msg = st.chat_input("Ask the agent...")
if user_msg:
    payload = {
        "message": user_msg,
        "mode": "code_exec" if mode else "prompt_tools",
        "topic": topic,
        "words": words
    }
    try:
        with st.spinner("Processing request... This may take up to 2.5 minutes for LLM calls."):
            resp = requests.post(f"{BACKEND_URL}/chat", json=payload, timeout=150)  # 150s to account for backend timeout (120s) + overhead
            resp.raise_for_status()  # Raise exception for bad status codes
            data = resp.json()
        
        # Validate response structure
        if "tokens_prompt" not in data or "tokens_output" not in data:
            st.error(f"Invalid response format: missing token fields. Response: {data}")
            st.json(data)  # Show full response for debugging
        else:
            # Ensure we have valid numeric values
            prompt_tokens = int(data.get("tokens_prompt", 0)) if data.get("tokens_prompt") is not None else 0
            output_tokens = int(data.get("tokens_output", 0)) if data.get("tokens_output") is not None else 0
            total_tokens = prompt_tokens + output_tokens
            
            st.session_state.history.append({
                "mode": data.get("mode", "unknown"),
                "prompt_tokens": prompt_tokens,
                "output_tokens": output_tokens,
                "total_tokens": total_tokens,
                "reply": data.get("reply", "No reply received")
            })
            
            # Show success message with token info for THIS request
            st.success(f"✅ Response received: {prompt_tokens:,} prompt + {output_tokens:,} output = {total_tokens:,} tokens (this request)")
    except requests.exceptions.Timeout:
        st.error("⏱️ Request timed out after 2.5 minutes. The LLM call may be taking longer than expected. Try reducing the transcript size or check backend logs.")
    except requests.exceptions.RequestException as e:
        st.error(f"Backend error: {e}")
        st.info("💡 Tip: Check if the backend service is running and accessible.")
    except Exception as e:
        st.error(f"Unexpected error: {e}")
        st.exception(e)

# Chat area
for item in st.session_state.history[-10:]:
    with st.chat_message("assistant"):
        st.write(item["reply"])

# Token chart
if st.session_state.history:
    df = pd.DataFrame(st.session_state.history)
    
    # Ensure numeric types for chart
    df["prompt_tokens"] = pd.to_numeric(df["prompt_tokens"], errors='coerce').fillna(0).astype(int)
    df["output_tokens"] = pd.to_numeric(df["output_tokens"], errors='coerce').fillna(0).astype(int)
    
    # Calculate total_tokens if not already present
    if "total_tokens" not in df.columns:
        df["total_tokens"] = df["prompt_tokens"] + df["output_tokens"]
    else:
        df["total_tokens"] = pd.to_numeric(df["total_tokens"], errors='coerce').fillna(0).astype(int)
    
    # Add index for x-axis
    df["turn"] = range(1, len(df) + 1)
    
    st.subheader("Token Consumption per Turn")
    
    # Check if we have valid data
    total_sum = df[["prompt_tokens", "output_tokens", "total_tokens"]].sum().sum()
    
    if len(df) > 0 and total_sum > 0:
        # Display chart with turn numbers
        chart_data = df.set_index("turn")[["prompt_tokens", "output_tokens", "total_tokens"]]
        st.line_chart(chart_data)
        
        # Show summary stats - CUMULATIVE across all requests
        st.markdown("**Cumulative Totals (All Requests):**")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Prompt Tokens", f"{df['prompt_tokens'].sum():,}", help="Sum of all prompt tokens across all requests")
        with col2:
            st.metric("Total Output Tokens", f"{df['output_tokens'].sum():,}", help="Sum of all output tokens across all requests")
        with col3:
            st.metric("Total Tokens", f"{df['total_tokens'].sum():,}", help="Sum of all tokens (prompt + output) across all requests")
        
        # Show latest request info
        if len(df) > 0:
            latest = df.iloc[-1]
            st.markdown("**Latest Request:**")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Prompt Tokens", f"{latest['prompt_tokens']:,}", help="Prompt tokens for the most recent request")
            with col2:
                st.metric("Output Tokens", f"{latest['output_tokens']:,}", help="Output tokens for the most recent request")
            with col3:
                st.metric("Total Tokens", f"{latest['total_tokens']:,}", help="Total tokens (prompt + output) for the most recent request")
    else:
        st.warning("⚠️ No token data available to display.")
        if len(df) > 0:
            st.info("Debug: Showing raw data from history")
            st.dataframe(df[["mode", "prompt_tokens", "output_tokens", "reply"]], use_container_width=True)

st.info(f"Backend at {BACKEND_URL} • MCP server at {MCP_URL}")
