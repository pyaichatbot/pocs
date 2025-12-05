#!/usr/bin/env python3
"""Entry point for running VulnBoard application."""

import uvicorn
from app.config import HOST, PORT

if __name__ == "__main__":
    print("=" * 60)
    print("VulnBoard - Intentionally Vulnerable AI Application")
    print("WARNING: This application contains intentional vulnerabilities")
    print("for security training purposes only. DO NOT USE IN PRODUCTION.")
    print("=" * 60)
    print(f"\nStarting server on http://{HOST}:{PORT}")
    print("Press Ctrl+C to stop\n")
    
    # Use import string format for reload to work properly
    uvicorn.run("app.main:app", host=HOST, port=PORT, reload=True)

