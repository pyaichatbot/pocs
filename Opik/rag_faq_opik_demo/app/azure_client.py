
import os
from typing import List, Dict

# Optional Azure OpenAI client. If not configured, we fallback to LocalLLM.
def _get_azure_client():
    try:
        from openai import AzureOpenAI
        key = os.getenv("AZURE_OPENAI_KEY")
        endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
        if not key or not endpoint:
            return None
        client = AzureOpenAI(api_key=key, azure_endpoint=endpoint, api_version=api_version)
        return client
    except Exception as e:
        print(f"[azure] Warning: Azure client not available: {e}")
        return None

class LocalLLM:
    def chat(self, messages: List[Dict]):
        # Extremely simple: echo with context-awareness
        user = " ".join([m.get("content","") for m in messages if m.get("role")=="user"])
        context = "\n".join([m.get("content","") for m in messages if m.get("role")=="system"])
        return f"[LOCAL-LLM] Based on the docs: {context[:120]} ... Answering: The gist is: {user[:160]}"

def _get_anthropic_client():
    try:
        from anthropic import Anthropic
        key = os.getenv("ANTHROPIC_API_KEY")
        if not key:
            return None
        client = Anthropic(api_key=key)
        # Wrap with Opik integration if available
        try:
            from opik.integrations.anthropic import track_anthropic
            client = track_anthropic(client)
        except Exception:
            pass
        return client
    except Exception as e:
        print(f"[anthropic] Warning: Anthropic client not available: {e}")
        return None

def get_model():
    # Prefer Anthropic when configured
    anthropic_client = _get_anthropic_client()
    if anthropic_client:
        model = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")
        max_tokens = int(os.getenv("ANTHROPIC_MAX_TOKENS", "512"))
        def _call(messages: List[Dict]):
            system = "\n".join([m.get("content", "") for m in messages if m.get("role") == "system"]) or None
            user_content = "\n".join([m.get("content", "") for m in messages if m.get("role") == "user"]).strip()
            try:
                resp = anthropic_client.messages.create(
                    model=model,
                    max_tokens=max_tokens,
                    system=system,
                    messages=[{"role": "user", "content": user_content}]
                )
                try:
                    return resp.content[0].text
                except Exception:
                    return str(resp)
            except Exception as e:
                # Graceful fallback: do not fail the API; use LocalLLM output
                llm = LocalLLM()
                return llm.chat([
                    {"role": "system", "content": system or ""},
                    {"role": "user", "content": user_content}
                ])
        return _call

    # Then Azure OpenAI if configured
    azure = _get_azure_client()
    deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini")
    if azure:
        def _call(messages):
            resp = azure.chat.completions.create(model=deployment, messages=messages)
            return resp.choices[0].message.content
        return _call

    # Fallback to local stub
    llm = LocalLLM()
    return lambda messages: llm.chat(messages)
