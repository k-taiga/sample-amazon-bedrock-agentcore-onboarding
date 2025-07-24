# 01_code_interpreter: AWS Cost Estimation Agent

This example demonstrates how to create an AI agent that estimates AWS costs using:

- **AWS Pricing MCP Server** for retrieving pricing data
- **Amazon Bedrock AgentCore Code Interpreter** for secure calculations
- **Strands Agents** framework for agent implementation

## What This Agent Does

The agent takes a description of a system architecture and:

1. 📋 Analyzes the architecture to identify required AWS services
2. 💰 Retrieves current pricing data using AWS Pricing MCP Server
3. 🧮 Performs cost calculations using AgentCore Code Interpreter
4. 📊 Provides detailed cost estimates with breakdowns

## Key Features

- **Secure Code Execution**: Uses AgentCore Code Interpreter sandbox for safe calculations
- **Real-time Pricing**: Fetches current AWS pricing data via MCP
- **Streaming Support**: Provides real-time streaming responses with proper delta handling
- **Comprehensive Analysis**: Considers multiple AWS services and regions
- **Detailed Logging**: Includes debug logging for monitoring and troubleshooting
- **Command-line Interface**: Flexible testing with customizable architecture descriptions

## Prerequisites

- AWS account with Bedrock access
- AWS credentials configured
- Python 3.12+
- Required dependencies (see pyproject.toml)

## Usage

```bash
# Test with default architecture
uv run 01_code_interpreter/test_cost_estimator_agent.py

# Test with custom architecture  
uv run 01_code_interpreter/test_cost_estimator_agent.py --architecture "Two EC2 m5.large instances"

# Test only streaming
uv run 01_code_interpreter/test_cost_estimator_agent.py --tests streaming
```

### Available Test Types

- **`regular`**: Non-streaming cost estimation
- **`streaming`**: Streaming cost estimation with delta processing

### Streaming API Usage

```python
# Streaming response (recommended)
async for event in agent.estimate_costs_stream("One EC2 t3.micro instance running 24/7"):
    if "data" in event:
        print(event["data"], end="", flush=True)
```
