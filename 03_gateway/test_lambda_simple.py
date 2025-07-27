#!/usr/bin/env python3
"""
Simple test script for AgentCore Gateway Lambda function

This script tests the Lambda function logic directly without Docker,
simulating the context that would be provided by AgentCore Gateway.
"""

import json
import os
import sys
from types import SimpleNamespace

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Set environment variables
os.environ['AGENTCORE_RUNTIME_ARN'] = 'arn:aws:bedrock-agentcore:us-east-1:872515288562:runtime/cost_estimator_agent-t3yYLdGyXu'
os.environ['LOG_LEVEL'] = 'INFO'

from app import lambda_handler

def create_mock_context():
    """Create mock Lambda context with AgentCore Gateway metadata"""
    custom_data = {
        'bedrockAgentCoreGatewayId': 'awscostestimationgateway-77oerlypcf',
        'bedrockAgentCoreTargetId': 'RIGZDWGIW4', 
        'bedrockAgentCoreMessageVersion': '1.0',
        'bedrockAgentCoreToolName': 'AWSCostEstimationLambdaTarget___aws_cost_estimation',
        'bedrockAgentCoreSessionId': 'test-session-123'
    }
    
    client_context = SimpleNamespace()
    client_context.custom = custom_data
    
    context = SimpleNamespace()
    context.client_context = client_context
    
    return context

def main():
    print("Testing AgentCore Gateway Lambda Function")
    print("=" * 50)
    
    # Load test event
    event = {
        "architecture_description": "A simple web application with an Application Load Balancer, 2 EC2 t3.medium instances, and an RDS MySQL database in us-east-1"
    }
    
    context = create_mock_context()
    
    print(f"Event: {json.dumps(event, indent=2)}")
    print(f"Tool Name: {context.client_context.custom['bedrockAgentCoreToolName']}")
    print("\nInvoking Lambda function...")
    
    try:
        result = lambda_handler(event, context)
        print(f"\nResult: {json.dumps(result, indent=2)}")
        
        if result['statusCode'] == 200:
            print("\n✅ SUCCESS: Lambda function executed successfully!")
        else:
            print(f"\n❌ ERROR: {result['body']}")
            
    except Exception as e:
        print(f"\n💥 EXCEPTION: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
