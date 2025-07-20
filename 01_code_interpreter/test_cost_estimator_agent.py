#!/usr/bin/env python3
"""Simple test for AWS Cost Estimation Agent"""

from cost_estimator_agent import AWSCostEstimatorAgent

def main():
    print("Testing AWS Cost Agent...")
    agent = AWSCostEstimatorAgent()
    
    # Simple test case
    architecture = "One EC2 t3.micro instance running 24/7"
    
    result = agent.estimate_costs(architecture)
    print(f"Result: {result[:100]}...")
    print("✅ Test completed!")

if __name__ == "__main__":
    main()
