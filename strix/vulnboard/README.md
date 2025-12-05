# VulnBoard - Intentionally Vulnerable AI Application

**WARNING: This application contains intentional security vulnerabilities for training purposes only. DO NOT USE IN PRODUCTION.**

## Overview

VulnBoard is a deliberately vulnerable web application designed to demonstrate:
- Security vulnerabilities in AI-powered applications
- How AI-generated code can introduce security issues
- Using Strix for automated security testing during development
- Integrating security testing into CI/CD pipelines

## Vulnerabilities

This application intentionally contains the following vulnerabilities:

### Traditional Vulnerabilities
- **IDOR (Insecure Direct Object Reference)**: Users can access any profile by changing the user ID
- **SQL Injection**: Search endpoint uses unsafe string concatenation in SQL queries
- **Reflected XSS**: User input reflected in HTML without sanitization

### AI-Specific Vulnerabilities
- **Prompt Injection**: User input passed directly to LLM without sanitization
- **Insecure AI Usage**: Hardcoded API keys, no rate limiting, exposed configuration
- **Data Leakage**: Sensitive user data (PII, credentials) sent to external AI APIs

## Quick Start

### Prerequisites
- **Python 3.12+** (required for Strix installation; the app itself can run on Python 3.11+)
- **pipx** (for installing Strix agent - see "Installing Strix Agent" section below)
- **pip** (for installing application dependencies)

### Installation

1. Clone or navigate to this directory:
```bash
cd vulnboard
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the application:
```bash
python app.py
```

5. Open your browser:
```
http://localhost:8000
```

### Demo Credentials
- Username: `admin` / Password: `admin123`
- Username: `user` / Password: `user123`

## Installing Strix Agent

**Important:** Strix is not included in `requirements.txt` because it requires Python 3.12+ and is installed separately as a CLI tool.

### Install Strix

1. **Install pipx** (if not already installed):
   ```bash
   brew install pipx  # macOS
   # or: pip install --user pipx  # Linux/other
   pipx ensurepath
   ```

2. **Install strix-agent**:
   ```bash
   pipx install strix-agent
   ```

3. **Verify installation**:
   ```bash
   strix --help
   ```

**Note:** 
- Strix requires Python 3.12+ to install. If you're using Python 3.11 or earlier, you'll need to upgrade or use a Python 3.12+ environment.
- **Docker Desktop must be running** - Strix uses Docker to run security tests in isolated containers.
- On macOS, the scripts automatically detect and configure the Docker socket path (`~/.docker/run/docker.sock`).

## Running Strix Security Scans

### Prerequisites

Before running Strix, set your LLM provider environment variables:
```bash
export STRIX_LLM="openai/gpt-4"  # or anthropic/claude-3, etc.
export LLM_API_KEY="your-api-key"
```

### Local Code Analysis

Run Strix against the codebase:
```bash
./scripts/run_strix_local.sh
```

### Runtime Testing

1. Start the application:
```bash
python app.py
```

2. In another terminal, run Strix against the running app:
```bash
./scripts/run_strix_http.sh
```

**Note:** Make sure `strix` is in your PATH. If installed via pipx, ensure `~/.local/bin` is in your PATH (run `pipx ensurepath` if needed).

## CI/CD Integration

See `.github/workflows/strix-ci.yml` for GitHub Actions integration example.

## Project Structure

```
vulnboard/
├── app/
│   ├── core/           # Database, security, AI client (with vulnerabilities)
│   ├── models/         # Data models
│   ├── routes/         # Route handlers (with vulnerabilities)
│   ├── services/       # Business logic (with vulnerabilities)
│   ├── templates/      # HTML templates (with XSS vulnerabilities)
│   └── static/         # CSS and JS files
├── scripts/            # Strix execution scripts
├── .github/workflows/  # CI/CD workflows
└── security/           # Security documentation
```

## Documentation

- [STRIX_DEMO_INSTRUCTIONS.md](STRIX_DEMO_INSTRUCTIONS.md) - Complete demo guide
- [security/STRIX_RUN_NOTES.md](security/STRIX_RUN_NOTES.md) - Sample Strix findings

## Learning Objectives

After completing this demo, you should understand:
1. How AI applications can contain both traditional and AI-specific vulnerabilities
2. How to use Strix for automated security testing
3. How to integrate security testing into development workflows
4. How to identify and remediate common security issues

## Security Notes

All vulnerabilities in this application are:
- **Intentional** - Designed for educational purposes
- **Documented** - Each vulnerability is clearly marked in code
- **Isolated** - Located in specific modules for easy identification
- **Not for Production** - This application should never be deployed

## License

This is a training application. Use at your own risk.

