# AgentCore Runtime - Agent Preparation Tool

## Overview

This module provides `prepare_agent.py`, a helper tool that prepares your AI agents for deployment to Amazon Bedrock AgentCore Runtime. It automates the initial setup steps and seamlessly integrates with the `agentcore` CLI tools from [bedrock-agentcore-starter-toolkit](https://github.com/aws/bedrock-agentcore-starter-toolkit).

## What This Tool Does

The `prepare` command handles two critical setup tasks:

1. **Deployment Directory Setup**: Copies your agent source files to a deployment directory
2. **IAM Role Creation**: Creates an IAM role with all necessary AgentCore permissions following [runtime permissions documentation](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-permissions.html)

## Usage

**Please execute command after `cd 02_runtime`**

### Step 1: Prepare Your Agent

```bash
# From the 02_runtime directory
uv run prepare_agent.py prepare --source-dir ../01_code_interpreter/cost_estimator_agent
```

### Step 2: Use AgentCore CLI Tools

After preparation, the tool provides you with ready-to-use `agentcore` commands:

```
✓ Agent preparation completed successfully!

Agent Name: cost_estimator_agent
Deployment Directory: ./deployment
Region: us-east-1

📋 Next Steps:

1. Configure the agent runtime:
   agentcore configure --entrypoint ./deployment/cost_estimator_agent.py --agent-name cost_estimator_agent --execution-role arn:aws:iam::123456789012:role/AgentCoreRole-cost_estimator_agent --requirements-file ./deployment/requirements.txt --disable-otel --region us-east-1

2. Launch the agent:
   agentcore launch

3. Test your agent:
   agentcore invoke '{"prompt": "Tell me an interesting fact"}'

💡 Tip: You can copy and paste the commands above directly into your terminal.
```

## Integration with AgentCore Starter Toolkit

This tool is designed to work seamlessly with the official [bedrock-agentcore-starter-toolkit](https://github.com/aws/bedrock-agentcore-starter-toolkit). After using our `prepare` command, you'll use the toolkit's `agentcore` CLI for:

- **`agentcore configure`**: Build and configure your agent runtime
- **`agentcore launch`**: Deploy your agent to Amazon Bedrock
- **`agentcore invoke`**: Test your deployed agent
- **`agentcore status`**: Check deployment status
- **`agentcore delete`**: Clean up resources when done

For detailed documentation on these commands, refer to the [official AgentCore documentation](https://github.com/aws/bedrock-agentcore-starter-toolkit).
