# Strix Demo Instructions

Complete guide for running the VulnBoard security assessment demo with Strix.

## Prerequisites

1. **Python 3.12+** installed (required for Strix installation)
   - Note: The VulnBoard app itself can run on Python 3.11+, but Strix requires Python 3.12+
   - Check your Python version: `python3.12 --version` or `python --version`
   
2. **pipx** installed (for Strix):
   ```bash
   # macOS (recommended):
   brew install pipx
   
   # Linux/other:
   pip install --user pipx
   
   # Then ensure PATH is set:
   pipx ensurepath
   ```
   
3. **Strix Agent** installed:
   ```bash
   pipx install strix-agent
   ```
   
   **Verify installation:**
   ```bash
   strix --help
   ```
   
   If `strix` command is not found, ensure `~/.local/bin` is in your PATH:
   ```bash
   export PATH="$HOME/.local/bin:$PATH"
   ```
4. **Docker Desktop** installed and running
   - Strix requires Docker to run security tests in isolated containers
   - On macOS, ensure Docker Desktop is running
   - The scripts automatically configure the Docker socket path

5. **Environment Variables** set:
   ```bash
   export STRIX_LLM="openai/gpt-4"  # or anthropic/claude-3, etc.
   export LLM_API_KEY="your-api-key-here"
   ```
   
   **Note:** On macOS, if Docker connection fails, you may need to set:
   ```bash
   export DOCKER_HOST="unix://$HOME/.docker/run/docker.sock"
   ```
   (The scripts should handle this automatically, but you can set it manually if needed)

## Demo Flow

### 1. Intro (1 minute)

Explain that VulnBoard is an intentionally vulnerable application (either AI-powered or built with AI assistance) designed to demonstrate how AI-based applications can contain both traditional and AI-specific vulnerabilities. Emphasize the importance of security testing during development, not just in production.

### 2. Local Development Setup (2 minutes)

1. **Set up the application:**
   ```bash
   cd vulnboard
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Start the application:**
   ```bash
   python app.py
   ```
   The app should be running at http://localhost:8000

3. **Explore the app manually:**
   - Navigate to http://localhost:8000
   - Login with credentials: `admin` / `admin123`
   - Browse the profile page, search, and AI chat features
   - Note the intentionally vulnerable behaviors

### 3. Developer Workflow: Run Strix Locally (3-5 minutes)

**Scenario:** A developer writes code (potentially AI-assisted) that introduces vulnerabilities.

1. **Run Strix against the codebase (static analysis):**
   ```bash
   ./scripts/run_strix_local.sh
   ```
   This scans the code for security vulnerabilities without running the app.

2. **Start the application** (if not already running):
   ```bash
   python app.py
   ```

3. **Run Strix against the running application (runtime testing):**
   ```bash
   ./scripts/run_strix_http.sh
   ```
   This tests the application over HTTP for runtime vulnerabilities.

4. **Review findings:**
   - Strix findings are saved in `agent_runs/<run-name>/`
   - Show how developers can catch issues before committing code

### 4. CI/CD Integration (2-3 minutes)

1. **Show the CI workflow:**
   - Display `.github/workflows/strix-ci.yml`
   - Explain how Strix runs automatically on every PR
   - Show how CI fails when critical vulnerabilities are detected

2. **Demonstrate blocking behavior:**
   - Explain that when a PR contains vulnerable code, Strix will:
     - Scan the code
     - Generate findings
     - Upload artifacts
     - Optionally fail the build (if `--fail-on-critical` is used)

3. **Show how developers can fix issues:**
   - Developer sees Strix findings in CI
   - Fixes vulnerabilities locally
   - Re-runs Strix to verify fixes
   - Pushes updated code

### 5. Review Findings (5 minutes)

1. **Examine Strix output:**
   - Open one vulnerability finding (e.g., prompt injection or SQL injection)
   - Review the PoC exploit that Strix generated
   - Show remediation guidance provided by Strix

2. **Map findings to code:**
   - Map the Strix PoC back to the relevant route and service file
   - Example: SQL injection finding → `app/routes/search_routes.py` → `app/services/search_service.py`
   - Show how the vulnerability was introduced (e.g., unsanitized user input, missing authorization check)

3. **Discuss secure patterns:**
   - **SOLID principles**: How consistent authorization layer, query builder abstraction, input validation service could prevent issues
   - **AI-specific mitigations**: Prompt sanitization, secure API key management, data filtering
   - **Traditional mitigations**: Parameterized queries, input validation, output encoding

### 6. Next Steps (1-2 minutes)

1. **Development workflow integration:**
   - Emphasize running Strix locally as part of the development workflow
   - Show how CI integration provides a safety net for the team

2. **Follow-up exercises:**
   - Refactor the app to fix vulnerabilities and compare Strix results before/after
   - Add Strix to pre-commit hooks for immediate feedback
   - Integrate Strix findings into security review processes

## Expected Strix Findings

Strix should identify at least:

1. **IDOR** - `/users/{id}` endpoint allows unauthorized access
2. **SQL Injection** - Search endpoint uses unsafe query building
3. **Reflected XSS** - Search query reflected without sanitization
4. **Prompt Injection** - AI chat passes user input directly to LLM
5. **Insecure AI Usage** - Hardcoded API keys, exposed configuration endpoint

## Troubleshooting

### Strix not found
```bash
pipx install strix-agent
# Or
pip install strix-agent
```

### Application not running
```bash
# Check if port 8000 is in use
lsof -i :8000

# Or change port in .env
PORT=8001 python app.py
```

### Strix API key issues
- Ensure `LLM_API_KEY` is set correctly
- Check that the LLM provider (OpenAI, Anthropic, etc.) is accessible
- Verify API key has sufficient credits/permissions

## Time Estimates

- **Total demo time**: 10-15 minutes
- **Setup**: 2 minutes
- **Local Strix run**: 3-5 minutes
- **CI integration**: 2-3 minutes
- **Findings review**: 5 minutes

## Additional Resources

- Strix documentation: [strix-agent documentation]
- OWASP Top 10: https://owasp.org/www-project-top-ten/
- OWASP AI Security: https://owasp.org/www-project-top-10-for-large-language-model-applications/

