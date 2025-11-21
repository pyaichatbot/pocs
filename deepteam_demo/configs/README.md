# YAML Configuration Files

This directory contains YAML configuration files for running DeepTeam red teaming using the official CLI pattern: `deepteam run config.yaml`

## Available Configurations

### 1. `simple_model_config.yaml`
Tests a foundational model directly without custom application logic.

**Usage:**
```bash
deepteam run configs/simple_model_config.yaml
```

**Features:**
- Simple model specification (gpt-3.5-turbo)
- Basic vulnerabilities (Bias, Toxicity)
- Single attack method (Prompt Injection)

### 2. `custom_callback_config.yaml`
Tests LLM applications using custom model callbacks (RAG system).

**Usage:**
```bash
deepteam run configs/custom_callback_config.yaml
```

**Features:**
- Custom callback from `test_callbacks.py`
- RAG-specific vulnerabilities (PII Leakage, Prompt Leakage)
- Multiple attack methods

### 3. `azure_openai_config.yaml`
Tests using Azure OpenAI models.

**Usage:**
```bash
# First, set Azure OpenAI credentials:
export AZURE_OPENAI_API_KEY="your-key"
export AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com"
export AZURE_OPENAI_DEPLOYMENT_NAME="your-deployment"

# Then run:
deepteam run configs/azure_openai_config.yaml
```

**Note:** Update the placeholder values in the YAML file with your actual Azure OpenAI credentials, or use environment variables with DeepTeam's global config.

### 4. `comprehensive_config.yaml`
Comprehensive test with multiple vulnerabilities and attacks.

**Usage:**
```bash
deepteam run configs/comprehensive_config.yaml
```

**Features:**
- Multiple vulnerability types
- Custom vulnerabilities
- Multiple attack methods
- Custom callback

## Running Configurations

### Using DeepTeam CLI Directly

```bash
# Basic usage
deepteam run configs/simple_model_config.yaml

# With CLI overrides
deepteam run configs/simple_model_config.yaml -c 3 -a 2 -o results

# Options:
#   -c, --max-concurrent: Maximum concurrent operations
#   -a, --attacks-per-vuln: Number of attacks per vulnerability type
#   -o, --output-folder: Path to output folder
```

### Using Demo Suite Wrapper

```bash
# List available configs
python run_yaml_config.py list

# Run a config
python run_yaml_config.py run configs/simple_model_config.yaml

# With options
python run_yaml_config.py run configs/simple_model_config.yaml -c 3 -a 2
```

## Configuration Structure

All YAML configs follow this structure:

```yaml
# Red teaming models (separate from target)
models:
  simulator: gpt-3.5-turbo-0125
  evaluation: gpt-4o

# Target system configuration
target:
  purpose: "Description of your LLM application"
  model: gpt-3.5-turbo  # OR callback: {file: "...", function: "..."}

# System configuration
system_config:
  max_concurrent: 3
  attacks_per_vulnerability_type: 2
  run_async: true
  ignore_errors: true
  output_folder: "results"

# Vulnerabilities to test
default_vulnerabilities:
  - name: "Bias"
    types: ["race", "gender"]

# Custom vulnerabilities (optional)
custom_vulnerabilities:
  - name: "CustomVulnerability"
    criteria: "Evaluation criteria"
    types: ["type1", "type2"]

# Attack methods
attacks:
  - name: "Prompt Injection"
```

## Custom Callbacks

Custom callbacks are defined in `test_callbacks.py` and can be referenced in YAML:

```yaml
target:
  callback:
    file: "test_callbacks.py"
    function: "rag_model_callback"  # Optional, defaults to "model_callback"
```

Available callbacks:
- `simple_model_callback`: Simple foundational model
- `rag_model_callback`: RAG system
- `chatbot_model_callback`: Conversational chatbot
- `agent_model_callback`: AI agent with tools
- `comprehensive_model_callback`: Complex application

## Testing

Run tests to verify YAML configs:

```bash
# Run YAML config tests
pytest tests/test_yaml_configs.py -v

# Test specific config
pytest tests/test_yaml_configs.py::TestYAMLConfigs::test_simple_model_config_exists -v
```

## Notes

- YAML configs use DeepTeam's official CLI interface
- Environment variables are automatically applied via `deepteam.cli.config.apply_env()`
- Custom callbacks must be async functions: `async def callback(input: str, turns=None) -> str`
- Results are saved to the `output_folder` specified in `system_config` or CLI `-o` option

