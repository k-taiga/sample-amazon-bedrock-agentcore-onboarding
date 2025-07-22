# AgentCore Runtime - Agent Deployment Tool

## Overview

This module provides `register_agent.py`, a simple yet comprehensive tool for deploying AI agents to Amazon Bedrock AgentCore Runtime. Following our "simple and sophisticated" principle, all functionality is contained in a single file that handles the complete deployment lifecycle.

## Features

### 1. `prepare` - Deployment Preparation
- Create deployment directory with annotated agent script
- Generate `requirements.txt`
- Create IAM role following [runtime permissions documentation](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-permissions.html)

### 2. `deploy` - Agent Deployment
- Use `bedrock_agentcore_starter_toolkit` for containerization
- Deploy to AgentCore Runtime
- Store deployment metadata

### 3. `invoke` - Agent Invocation
- Test deployed agent with messages
- Handle session management
- Display responses

### 4. `status` - Deployment Status
- Check endpoint availability
- Show deployment information

### 5. `delete` - Resource Cleanup
- Remove from AgentCore Runtime
- Clean up resources
- Optional IAM role deletion

## Usage

```bash
# Prepare agent for deployment
uv run register_agent.py prepare --source-dir ../01_code_interpreter/cost_estimator_agent

# Deploy to AgentCore Runtime
uv run register_agent.py deploy ./deployment

# Test the deployed agent
uv run register_agent.py invoke <agent_arn> "Estimate costs for a web application"

# Clean up resources
uv run register_agent.py delete cost_estimator_agent
```

## Implementation Design

### Single File Architecture

All functionality is contained in `register_agent.py` with clear separation of concerns:

```python
# Core components in single file
class AgentPreparer:
    """Handles preparation of agent for deployment"""
    
class AgentDeployer:
    """Handles deployment to AgentCore Runtime"""
    
class AgentInvoker:
    """Handles interaction with deployed agents"""
    
class ResourceManager:
    """Handles resource lifecycle management"""

# CLI interface
@click.group()
def cli():
    """AgentCore Runtime deployment tool"""
    
@cli.command()
def prepare(source_dir):
    """Prepare agent for deployment"""
    
@cli.command()
def deploy(deployment_dir):
    """Deploy agent to runtime"""
    
# ... other commands
```

### IAM Policy Requirements

Based on [runtime permissions documentation](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-permissions.html):

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock-agentcore:*",
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents",
        "ecr:GetAuthorizationToken",
        "ecr:BatchCheckLayerAvailability",
        "ecr:GetDownloadUrlForLayer",
        "ecr:BatchGetImage"
      ],
      "Resource": "*"
    }
  ]
}
```

### Deployment Metadata

Simple JSON file to track deployments:

```json
{
  "deployment_id": "agent-cost-estimator-20250120",
  "agent_name": "cost_estimator_agent",
  "source_script": "cost_estimator_agent.py",
  "deployment_dir": "./deployments/cost_estimator_agent",
  "iam_role_arn": "arn:aws:iam::123456789012:role/AgentCoreRole",
  "created_at": "2025-01-20T10:00:00Z",
  "status": "ACTIVE"
}
```

## File Structure

```
02_runtime/
 README.md               # This documentation
 register_agent.py       # Single file implementation
 test_register_agent.py  # Test file
```

## Error Handling

- Clear error messages with troubleshooting hints
- Automatic retry with exponential backoff
- Comprehensive logging for debugging
- Graceful cleanup on failures

## Testing

### How to Run Tests

The `test_register_agent.py` provides a comprehensive testing framework with multiple commands:

**Please execute command after `cd 02_runtime`**

### Test Commands Explained

- **`full_demo`**: Runs the complete workflow (prepare → deploy → test → status → optional cleanup)
- **`deploy`**: Prepares and deploys the cost estimator agent to AgentCore Runtime
- **`test`**: Invokes the deployed agent with a sample web application architecture
- **`cleanup`**: Removes the deployed agent and optionally deletes the IAM role

### Prerequisites for Testing

Before running tests, ensure you have:

1. **AWS Credentials**: Configured with permissions for:
   - IAM role creation/deletion
   - Bedrock AgentCore access
   - ECR access for container operations

2. **Required Files**: The test expects `01_code_interpreter/cost_estimator_agent.py` to exist

3. **Dependencies**: Install via `uv sync` in the project root
