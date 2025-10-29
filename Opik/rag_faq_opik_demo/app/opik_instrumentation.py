
# Safe Opik setup: if opik is not installed, provide no-op decorators and classes.
import os
USE_OPIK = os.getenv("USE_OPIK", "1") == "1"

class _NoOp:
    def __getattr__(self, name):
        return self
    def __call__(self, f=None, *a, **k):
        # Works as a decorator or as a function; returns input or None
        if callable(f) and not a and not k:
            return f
        return None

track = lambda f: f  # default no-op
Guardrail = None
PII = None

client = None

if USE_OPIK:
    try:
        import opik
        from opik import track  # decorator
        try:
            from opik.guardrails import Guardrail, PII
        except Exception:
            Guardrail, PII = None, None
        client = opik
        # Configuration order of precedence:
        # 1) Explicit self-host via OPIK_URL (or OPIK_BASE_URL) and OPIK_API_KEY/COMET_API_KEY
        # 2) Local lightweight mode when OPIK_USE_LOCAL=1 (default)
        # Do not call configure here; rely on env-only to use the already running Opik services.
        # Required envs should be set at process/container runtime, e.g.:
        # - OPIK_URL_OVERRIDE=http://opik-api:5173/api/
        # - (optional) OPIK_API_KEY=... for secured deployments
        pass
    except Exception as e:
        print(f"[opik] Warning: Opik not available or failed to init: {e}")
