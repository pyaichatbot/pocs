# DeepTeam  Demo Suite

A comprehensive demonstration suite showcasing DeepTeam's full capabilities for LLM red teaming. This suite provides production-grade examples of how to use DeepTeam to test LLM applications for vulnerabilities, attacks, and compliance with industry frameworks.

## Features

- **40+ Vulnerabilities**: Comprehensive testing across all vulnerability categories
- **10+ Attack Methods**: Single-turn and multi-turn adversarial attacks
- **Custom Vulnerabilities**: Create domain-specific security tests
- **Framework Support**: OWASP Top 10 for LLMs and NIST AI RMF compliance testing
- **Multiple LLM Applications**: Simple models, RAG systems, chatbots, and AI agents
- **Rich Visualizations**: Beautiful console output with tables and summaries
- **Comprehensive Reporting**: JSON and Markdown reports with detailed analysis
- **OpenTelemetry Logging**: Structured logging for observability (no telemetry export)

## Architecture

The demo suite follows SOLID principles with clean separation of concerns:

```
deepteam_demo/
├── apps/              # LLM application implementations
├── demos/             # Demo orchestration
├── services/          # Business logic (red teaming, visualization, reporting)
├── config/            # Configuration and logging setup
├── utils/             # Cross-cutting utilities
└── results/           # Generated reports (gitignored)
```

## Prerequisites

- Python 3.9 or higher
- API keys for LLM providers:
  - **Anthropic**: `ANTHROPIC_API_KEY`
  - **Azure OpenAI**: `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_API_VERSION`, `AZURE_OPENAI_DEPLOYMENT_NAME`

## Installation

1. **Clone or navigate to the demo directory:**
   ```bash
   cd deepteam_demo
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables:**
   
   Create a `.env` file or export environment variables:
   
   ```bash
   # For Anthropic
   export ANTHROPIC_API_KEY="sk-ant-..."
   
   # For Azure OpenAI
   export AZURE_OPENAI_API_KEY="your-key"
   export AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com"
   export AZURE_OPENAI_API_VERSION="2024-02-15-preview"
   export AZURE_OPENAI_DEPLOYMENT_NAME="your-deployment"
   
   # Optional: Override defaults
   export TARGET_MODEL="claude-sonnet-4-20250514"
   export LLM_PROVIDER="anthropic"  # or "azure_openai"
   # Reduced to 3 to avoid Anthropic rate limits (429 errors)
   export MAX_CONCURRENT="3"
   export ATTACKS_PER_VULN="3"
   export OUTPUT_FOLDER="results"
   export LOG_LEVEL="INFO"
   ```

## Usage

### Interactive Mode

Run the main script to access the interactive menu:

```bash
python main.py
```

Or use the CLI directly:

```bash
# Run a specific demo
python main.py run --demo vulnerability
python main.py run --demo attack
python main.py run --demo custom
python main.py run --demo framework
python main.py run --demo comprehensive

# Run all demos
python main.py run --demo all

# Show configuration
python main.py config

# List available demos
python main.py list-demos
```


### YAML Configuration Files (Official DeepTeam Pattern)

The demo suite includes YAML configuration files that follow the official DeepTeam CLI pattern. These can be run using the official `deepteam` CLI:

```bash
# List available YAML configs
ls configs/

# Run a YAML config using official DeepTeam CLI
deepteam run configs/simple_model_config.yaml

# With CLI overrides
deepteam run configs/simple_model_config.yaml -c 3 -a 2 -o results

# Available configs:
#   - simple_model_config.yaml: Tests foundational models
#   - custom_callback_config.yaml: Tests LLM applications with custom callbacks
#   - azure_openai_config.yaml: Tests Azure OpenAI models
#   - comprehensive_config.yaml: Comprehensive test with multiple vulnerabilities
```

See `configs/README.md` for detailed documentation on YAML configurations.

### Available Demos

1. **Vulnerability Demo**: Showcases all 40+ vulnerabilities across all categories
   - Responsible AI (Bias, Toxicity)
   - Data Privacy (PII Leakage, Prompt Leakage)
   - Security (BFLA, BOLA, RBAC, SSRF, SQL Injection, etc.)
   - Safety (Illegal Activity, Graphic Content, Personal Safety, Child Protection)
   - Business (Misinformation, Intellectual Property, Competition)
   - Agentic (Goal Theft, Recursive Hijacking, Excessive Agency, Robustness)

2. **Attack Demo**: Demonstrates all attack methods
   - Single-turn: Prompt Injection, Leetspeak, ROT13, Base64, Math Problem, Multilingual, Roleplay, etc.
   - Multi-turn: Linear Jailbreaking, Tree Jailbreaking, Crescendo Jailbreaking, Sequential Jailbreak, Bad Likert Judge

3. **Custom Vulnerability Demo**: Shows how to create custom vulnerabilities
   - Business Logic vulnerabilities
   - API Security vulnerabilities
   - Data Integrity vulnerabilities

4. **Framework Demo**: Tests using industry-standard frameworks
   - OWASP Top 10 for LLMs
   - NIST AI Risk Management Framework

5. **Comprehensive Demo**: Full feature showcase combining all capabilities

### Demo Applications

The suite includes four types of LLM applications:

1. **SimpleModelApp**: Foundational model wrapper (Anthropic Claude or Azure OpenAI GPT)
2. **RAGApp**: RAG system with mock vector store (demonstrates PII/prompt leakage)
3. **ChatbotApp**: Conversational chatbot with memory (demonstrates robustness/hijacking)
4. **AgentApp**: AI agent with tool calling (demonstrates excessive agency, goal theft)

## Configuration

Configuration is managed through environment variables and the `Settings` class. Key settings:

- **LLM Providers**: Anthropic or Azure OpenAI
- **Models**: Configurable target, simulator, and evaluation models
- **Concurrency**: `MAX_CONCURRENT` (default: 3, reduced to avoid Anthropic rate limits)
- **Attacks**: `ATTACKS_PER_VULN` (default: 3)
- **Output**: `OUTPUT_FOLDER` (default: "results")
- **Logging**: `LOG_LEVEL` (default: "INFO")

## Output

Results are saved in the `results/` directory:

- **JSON Reports**: Detailed risk assessment data (using DeepTeam's native format)
- **Markdown Reports**: Human-readable reports with summaries and failed test cases
- **Console Output**: Rich formatted tables and visualizations

## Observability

The suite uses OpenTelemetry SDK for structured logging:

- **No Telemetry Export**: Logging only, no data is exported
- **Structured Logs**: Context-aware logging with span support
- **Log Levels**: Configurable (DEBUG, INFO, WARNING, ERROR, CRITICAL)

## Code Quality

- **SOLID Principles**: Single Responsibility, Open/Closed, Liskov Substitution, Interface Segregation, Dependency Inversion
- **Type Hints**: Full type annotations throughout
- **Error Handling**: Comprehensive error handling with graceful degradation
- **Documentation**: Docstrings for all classes and methods

## Examples

### Running a Specific Demo

```python
from config.settings import Settings
from demos.vulnerability_demo import VulnerabilityDemo

settings = Settings.from_env()
demo = VulnerabilityDemo(settings=settings)
results = demo.run()
```

### Creating a Custom Vulnerability

```python
from deepteam.vulnerabilities.custom import CustomVulnerability

custom_vuln = CustomVulnerability(
    name="Business Logic",
    criteria="The system should not allow unauthorized access control bypass",
    types=["access_control", "privilege_escalation"],
)
```

### Using Frameworks

```python
from deepteam.frameworks import OWASPTop10, NIST

# OWASP Top 10
owasp = OWASPTop10(num_attacks=5)

# NIST AI RMF
nist = NIST(categories=["measure_1", "measure_2"])
```

## Troubleshooting

### API Key Issues

Ensure your API keys are set correctly:
```bash
echo $ANTHROPIC_API_KEY  # Should show your key
echo $AZURE_OPENAI_API_KEY  # Should show your key
```

### Import Errors

Make sure you're running from the `deepteam_demo` directory:
```bash
cd deepteam_demo
python main.py
```

### Model Errors

Check that your model names are correct:
- Anthropic: `claude-3-5-sonnet-20241022`, `claude-3-opus-20240229`, etc.
- Azure OpenAI: Use your deployment name

## Requirements

See `requirements.txt` for full dependency list. Key dependencies:

- `deepteam>=1.0.3`: DeepTeam framework
- `deepeval>=3.6.2`: DeepEval (model wrappers)
- `anthropic>=0.71.0`: Anthropic SDK
- `openai>=1.76.2`: OpenAI SDK (for Azure)
- `opentelemetry-api>=1.24.0`: OpenTelemetry (logging)
- `rich>=13.0.0`: Rich console output
- `typer>=0.9.0`: CLI framework

## License

This demo suite is provided as-is for demonstration purposes. Refer to DeepTeam's license for framework usage.

## Support

For issues or questions:
- DeepTeam Documentation: https://www.trydeepteam.com
- DeepTeam GitHub: https://github.com/confident-ai/deepteam

