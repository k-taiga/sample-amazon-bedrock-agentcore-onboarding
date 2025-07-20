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
- **Comprehensive Analysis**: Considers multiple AWS services and regions
- **Detailed Logging**: Includes debug logging for monitoring and troubleshooting

## Prerequisites

- AWS account with Bedrock access
- AWS credentials configured
- Python 3.12+
- Required dependencies (see pyproject.toml)

## Usage

```bash
# Run the cost estimation agent
uv run python 01-code-interpreter/cost_estimator_agent.py
```

## Testing

Run the simple test to see the agent in action:

```bash
uv run 01-code-interpreter/simple_test.py
```

### What the Test Does

The test demonstrates the core functionality step by step:

1. **Initialize Agent** - Sets up AgentCore Code Interpreter, MCP Server, and Strands Agent
2. **Test Code Interpreter** - Runs a simple EC2 cost calculation to verify the sandbox works
3. **Test Cost Estimation** - Analyzes a simple web app architecture and provides detailed cost breakdown
4. **Clean Up** - Properly stops all resources

### Expected Output

You should see:
- ✅ Agent initialization success
- ✅ Code Interpreter working with EC2 calculation ($33.41/month)
- ✅ Complete cost estimation with:
  - Monthly cost: ~$13.46
  - Yearly cost: ~$161.47
  - Service breakdown (EC2, S3, CloudFront)
  - Cost optimization recommendations

### Test Architecture

Simple web application with:
- EC2 t3.micro instance (always running)
- 20GB S3 storage
- CloudFront distribution
- 1,000 page views per day

This demonstrates how the agent can analyze real architectures and provide actionable cost insights.

## Architecture

The agent demonstrates the core AgentCore principle: **AgentCore works locally without deployment**. The Code Interpreter provides a secure sandbox environment that protects your local system while enabling powerful computational capabilities.

## Implementation Highlights

- Uses Strands Agents framework for clean, maintainable code
- Integrates AWS Pricing MCP Server for accurate pricing data
- Leverages AgentCore Code Interpreter for complex calculations
- Includes comprehensive error handling and logging
- Follows the project's "simple and sophisticated" principle
