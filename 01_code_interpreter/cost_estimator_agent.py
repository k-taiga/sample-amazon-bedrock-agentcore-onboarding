"""
AWS Cost Estimation Agent using Amazon Bedrock AgentCore Code Interpreter

This agent demonstrates how to:
1. Use AWS Pricing MCP Server to retrieve pricing data
2. Use AgentCore Code Interpreter for secure calculations
3. Provide comprehensive cost estimates for AWS architectures

Key Features:
- Secure code execution in AgentCore sandbox
- Real-time AWS pricing data
- Comprehensive logging and error handling
- Progressive complexity building
"""

import os
import logging
from strands import Agent, tool
from strands.tools.mcp import MCPClient
from mcp import stdio_client, StdioServerParameters
from bedrock_agentcore.tools.code_interpreter_client import CodeInterpreter
from config import (
    SYSTEM_PROMPT,
    COST_ESTIMATION_PROMPT,
    DEFAULT_MODEL,
    DEFAULT_REGION,
    LOG_FORMAT
)

# Configure comprehensive logging for debugging and monitoring
logging.basicConfig(
    level=logging.INFO,
    format=LOG_FORMAT,
    handlers=[logging.StreamHandler()]
)

# Enable Strands debug logging for detailed agent behavior
logging.getLogger("strands").setLevel(logging.DEBUG)

logger = logging.getLogger(__name__)


class AWSCostEstimatorAgent:
    """
    AWS Cost Estimation Agent using AgentCore Code Interpreter
    
    This agent combines:
    - MCP pricing tools (automatically available) for real-time pricing data
    - AgentCore Code Interpreter for secure calculations
    - Strands Agents framework for clean implementation
    """
    
    def __init__(self, region: str = DEFAULT_REGION):
        """
        Initialize the cost estimation agent
        
        Args:
            region: AWS region for AgentCore Code Interpreter
        """
        self.region = region
        self.code_interpreter = None
        
        logger.info(f"Initializing AWS Cost Estimator Agent in region: {region}")
        
    def _setup_code_interpreter(self) -> None:
        """Setup AgentCore Code Interpreter for secure calculations"""
        try:
            logger.info("Setting up AgentCore Code Interpreter...")
            self.code_interpreter = CodeInterpreter(self.region)
            self.code_interpreter.start()
            logger.info("✅ AgentCore Code Interpreter session started successfully")
        except Exception as e:
            logger.error(f"❌ Failed to setup Code Interpreter: {e}")
            raise
    
    def _setup_aws_pricing_client(self) -> MCPClient:
        """Setup AWS Pricing MCP Client following Strands best practices"""
        try:
            logger.info("Setting up AWS Pricing MCP Client...")
            aws_profile = os.environ.get("AWS_PROFILE", "default")
            logger.info(f"Using AWS profile: {aws_profile}")
            
            aws_pricing_client = MCPClient(
                lambda: stdio_client(StdioServerParameters(
                    command="uvx", 
                    args=["awslabs.aws-pricing-mcp-server@latest"],
                    env={
                        "FASTMCP_LOG_LEVEL": "ERROR",
                        "AWS_PROFILE": aws_profile,
                        "AWS_REGION": self.region
                    }
                ))
            )
            logger.info("✅ AWS Pricing MCP Client setup successfully")
            return aws_pricing_client
        except Exception as e:
            logger.error(f"❌ Failed to setup AWS Pricing MCP Client: {e}")
            raise
    
    
    @tool
    def execute_cost_calculation(self, calculation_code: str, description: str = "") -> str:
        """
        Execute cost calculations using AgentCore Code Interpreter
        
        Args:
            calculation_code: Python code for cost calculations
            description: Description of what the calculation does
            
        Returns:
            Calculation results as string
        """
        if not self.code_interpreter:
            return "❌ Code Interpreter not initialized"
            
        try:
            logger.info(f"🧮 Executing calculation: {description}")
            logger.debug(f"Code to execute:\n{calculation_code}")
            
            # Execute code in secure AgentCore sandbox
            response = self.code_interpreter.invoke("executeCode", {
                "language": "python",
                "code": calculation_code
            })
            
            # Extract results from response stream
            results = []
            for event in response.get("stream", []):
                if "result" in event:
                    result = event["result"]
                    if "content" in result:
                        for content_item in result["content"]:
                            if content_item.get("type") == "text":
                                results.append(content_item["text"])
            
            result_text = "\n".join(results)
            logger.info("✅ Calculation completed successfully")
            logger.debug(f"Calculation result: {result_text}")
            
            return result_text
            
        except Exception as e:
            error_msg = f"❌ Calculation failed: {e}"
            logger.error(error_msg)
            return error_msg

    def estimate_costs(self, architecture_description: str) -> str:
        """
        Estimate costs for a given architecture description
        
        Args:
            architecture_description: Description of the system to estimate
            
        Returns:
            Cost estimation results
        """
        logger.info("🚀 Initializing AWS Cost Estimation Agent...")
        logger.info("📊 Starting cost estimation...")
        logger.info(f"Architecture: {architecture_description}")
        
        try:
            # Setup components in order
            self._setup_code_interpreter()
            aws_pricing_client = self._setup_aws_pricing_client()

            # Create agent with persistent MCP context for this request
            with aws_pricing_client:
                pricing_tools = aws_pricing_client.list_tools_sync()
                logger.info(f"Found {len(pricing_tools)} AWS pricing tools")
                
                # Create agent with both execute_cost_calculation and MCP pricing tools
                all_tools = [self.execute_cost_calculation] + pricing_tools
                agent = Agent(
                    model=DEFAULT_MODEL,
                    tools=all_tools,
                    system_prompt=SYSTEM_PROMPT
                )
                
                # Use the agent to process the cost estimation request
                prompt = COST_ESTIMATION_PROMPT.format(
                    architecture_description=architecture_description
                )
                result = agent(prompt)
                
                logger.info("✅ Cost estimation completed")
                return result.message["content"] if result.message else "No estimation result."

        except Exception as e:
            error_msg = f"❌ Cost estimation failed: {e}"
            logger.error(error_msg)
            return error_msg
        finally:
            # Clean up resources
            self.cleanup()
    
    def cleanup(self) -> None:
        """Clean up resources"""
        logger.info("🧹 Cleaning up resources...")
        
        if self.code_interpreter:
            try:
                self.code_interpreter.stop()
                logger.info("✅ Code Interpreter session stopped")
            except Exception as e:
                logger.warning(f"⚠️ Error stopping Code Interpreter: {e}")
            finally:
                self.code_interpreter = None
