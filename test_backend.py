#!/usr/bin/env python3
"""
Quick backend test script
Tests that the backend starts and responds to health checks
"""

import sys
import time
import requests
from subprocess import Popen, PIPE
import signal

def test_backend():
    """Test backend startup and health check"""
    
    print("🚀 Starting Navis backend...")
    
    # Start the backend process
    process = Popen(
        ["python", "navis-backend/main.py"],
        stdout=PIPE,
        stderr=PIPE,
        text=True
    )
    
    # Wait for server to start
    print("⏳ Waiting for server to start...")
    max_attempts = 15
    for attempt in range(max_attempts):
        time.sleep(1)
        try:
            response = requests.get("http://127.0.0.1:8000/", timeout=1)
            if response.status_code == 200:
                print(f"✅ Server started after {attempt + 1} seconds")
                break
        except:
            if attempt < max_attempts - 1:
                print(f"   Attempt {attempt + 1}/{max_attempts}...")
            else:
                print("❌ Server failed to start")
                process.kill()
                return False
    
    try:
        # Test health endpoint
        print("🔍 Testing health endpoint...")
        response = requests.get("http://127.0.0.1:8000/health", timeout=5)
        
        if response.status_code == 200:
            health_data = response.json()
            print("\n✅ Backend is healthy!")
            print(f"   Version: {health_data.get('version')}")
            print(f"   Status: {health_data.get('status')}")
            
            print("\n📊 Component Status:")
            components = health_data.get('components', {})
            for name, status in components.items():
                icon = "✅" if status else "⚠️"
                print(f"   {icon} {name}: {status}")
            
            # Check AWS components specifically
            aws_components = {
                'bedrock_client': components.get('bedrock_client'),
                'session_manager': components.get('session_manager'),
                'experience_storage': components.get('experience_storage'),
                'vision_fallback': components.get('vision_fallback')
            }
            
            print("\n☁️  AWS Integration Status:")
            all_aws_ready = all(aws_components.values())
            if all_aws_ready:
                print("   ✅ All AWS components ready!")
                print("   💰 Using AWS services (10-120x cost savings)")
            else:
                print("   ⚠️  AWS components not configured")
                print("   💡 Set AWS credentials to enable (see QUICK_AWS_SETUP.md)")
                for name, status in aws_components.items():
                    icon = "✅" if status else "❌"
                    print(f"      {icon} {name}")
            
            print("\n🎯 RL Statistics:")
            rl_stats = health_data.get('rl_statistics', {})
            if rl_stats:
                rl_agent_stats = rl_stats.get('rl_agent', {})
                print(f"   Total experiences: {rl_agent_stats.get('total_experiences', 0)}")
                print(f"   Exploration rate: {rl_agent_stats.get('exploration_rate', 0)}")
            
            print("\n✅ All tests passed!")
            return True
        else:
            print(f"\n❌ Health check failed with status {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("\n❌ Could not connect to backend")
        print("   Make sure the backend is running on http://127.0.0.1:8000")
        return False
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        return False
        
    finally:
        # Stop the backend
        print("\n🛑 Stopping backend...")
        process.send_signal(signal.SIGINT)
        process.wait(timeout=5)
        print("✅ Backend stopped")

if __name__ == "__main__":
    success = test_backend()
    sys.exit(0 if success else 1)
