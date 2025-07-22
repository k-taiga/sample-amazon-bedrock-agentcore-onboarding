#!/usr/bin/env python3
"""Simple test for AWS Cost Estimation Agent"""

import asyncio
from cost_estimator_agent.cost_estimator_agent import AWSCostEstimatorAgent

async def test_streaming():
    """Test streaming cost estimation"""
    print("\n🔄 Testing streaming cost estimation...")
    agent = AWSCostEstimatorAgent()
    
    # Simple test case
    architecture = "One EC2 t3.micro instance running 24/7"
    
    try:
        stream_content = []
        async for event in agent.estimate_costs_stream(architecture):
            if "data" in event:
                print(event["data"], end="", flush=True)
                stream_content.append(str(event["data"]))
            elif "error" in event:
                print(f"\n❌ Streaming error: {event['data']}")
                return False
        
        full_response = "".join(stream_content)
        print(f"\n📊 Full streaming response length: {len(full_response)} characters")
        return len(full_response) > 0
        
    except Exception as e:
        print(f"❌ Streaming test failed: {e}")
        return False


def test_regular():
    """Test regular (non-streaming) cost estimation"""
    print("📄 Testing regular cost estimation...")
    agent = AWSCostEstimatorAgent()
    
    # Simple test case
    architecture = "One EC2 t3.micro instance running 24/7"
    
    try:
        result = agent.estimate_costs(architecture)
        print(f"📊 Regular response length: {len(result)} characters")
        print(f"Result preview: {result[:150]}...")
        return len(result) > 0
    except Exception as e:
        print(f"❌ Regular test failed: {e}")
        return False

async def main():
    print("🚀 Testing AWS Cost Agent - Both Implementations")
    
    # Test regular implementation
    regular_success = test_regular()
    
    # Test streaming implementation  
    streaming_success = await test_streaming()
    
    print(f"\n📋 Test Results:")
    print(f"   Regular implementation: {'✅ PASS' if regular_success else '❌ FAIL'}")
    print(f"   Streaming implementation: {'✅ PASS' if streaming_success else '❌ FAIL'}")
    
    if regular_success and streaming_success:
        print("🎉 All tests completed successfully!")
    else:
        print("⚠️ Some tests failed - check logs above")

if __name__ == "__main__":
    asyncio.run(main())
