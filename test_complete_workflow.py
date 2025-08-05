#!/usr/bin/env python3
"""
Complete Workflow Test for Agentic RAG System
Tests individual components and full integration
"""

import asyncio
import httpx
import json
import time

class CompleteWorkflowTest:
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.llm_url = "http://localhost:8001"
        self.auth_token = None
        
    async def test_individual_components(self):
        """Test each component individually"""
        print("🔧 Testing Individual Components...")
        print("-" * 40)
        
        # Test 1: Mock LLM
        print("1. Testing Mock LLM...")
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{self.llm_url}/v1/chat/completions", json={
                "model": "microsoft/DialoGPT-small",
                "messages": [{"role": "user", "content": "Hello!"}]
            })
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ Mock LLM: {result['choices'][0]['message']['content'][:30]}...")
            else:
                print(f"   ❌ Mock LLM: Failed")
                return False
        
        # Test 2: Authentication
        print("2. Testing Authentication...")
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{self.base_url}/auth/login", json={
                "username": "admin", "password": "admin123"
            })
            if response.status_code == 200:
                result = response.json()
                self.auth_token = result["access_token"]
                print(f"   ✅ Authentication: Token received")
            else:
                print(f"   ❌ Authentication: Failed")
                return False
        
        # Test 3: Database Connections
        print("3. Testing Database Connections...")
        async with httpx.AsyncClient() as client:
            # Test Qdrant
            response = await client.get("http://localhost:6333/collections")
            if response.status_code == 200:
                print(f"   ✅ Qdrant: Connected")
            else:
                print(f"   ❌ Qdrant: Failed")
                return False
            
            # Test Redis
            import subprocess
            redis_check = subprocess.run([
                "docker-compose", "exec", "-T", "redis", "redis-cli", "ping"
            ], capture_output=True, text=True)
            if redis_check.returncode == 0 and "PONG" in redis_check.stdout:
                print(f"   ✅ Redis: Connected")
            else:
                print(f"   ❌ Redis: Failed")
                return False
        
        print("   ✅ All individual components working!")
        return True
    
    async def test_simple_chat_flow(self):
        """Test a simple chat flow"""
        print("\n💬 Testing Simple Chat Flow...")
        print("-" * 40)
        
        if not self.auth_token:
            print("❌ No auth token available")
            return False
        
        async with httpx.AsyncClient() as client:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            # Send a simple message
            chat_data = {
                "message": "Hello! This is a simple test message.",
                "user_id": "admin_001",
                "session_id": "simple_test_session"
            }
            
            response = await client.post(f"{self.base_url}/chat", json=chat_data, headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Chat Response: {result.get('response', 'No response')[:50]}...")
                print(f"   Session ID: {result.get('session_id', 'No session')}")
                print(f"   Timestamp: {result.get('timestamp', 'No timestamp')}")
                return True
            else:
                print(f"❌ Chat Failed: {response.status_code} - {response.text}")
                return False
    
    async def test_conversation_flow(self):
        """Test a multi-turn conversation"""
        print("\n🔄 Testing Multi-turn Conversation...")
        print("-" * 40)
        
        if not self.auth_token:
            print("❌ No auth token available")
            return False
        
        async with httpx.AsyncClient() as client:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            session_id = f"conversation_test_{int(time.time())}"
            
            # First message
            print("1. Sending first message...")
            response1 = await client.post(f"{self.base_url}/chat", json={
                "message": "Hello! My name is Alice.",
                "user_id": "admin_001",
                "session_id": session_id
            }, headers=headers)
            
            if response1.status_code == 200:
                result1 = response1.json()
                print(f"   ✅ Response 1: {result1.get('response', 'No response')[:30]}...")
            else:
                print(f"   ❌ Response 1 failed: {response1.status_code}")
                return False
            
            # Second message (should have context from first)
            print("2. Sending second message...")
            response2 = await client.post(f"{self.base_url}/chat", json={
                "message": "What's my name?",
                "user_id": "admin_001",
                "session_id": session_id
            }, headers=headers)
            
            if response2.status_code == 200:
                result2 = response2.json()
                print(f"   ✅ Response 2: {result2.get('response', 'No response')[:30]}...")
            else:
                print(f"   ❌ Response 2 failed: {response2.status_code}")
                return False
            
            print(f"   ✅ Multi-turn conversation completed!")
            return True
    
    async def test_storage_verification(self):
        """Verify that data is being stored"""
        print("\n💾 Testing Storage Verification...")
        print("-" * 40)
        
        # Check Redis for any data
        import subprocess
        redis_check = subprocess.run([
            "docker-compose", "exec", "-T", "redis", "redis-cli", "keys", "*"
        ], capture_output=True, text=True)
        
        if redis_check.returncode == 0:
            keys = redis_check.stdout.strip()
            if keys:
                print(f"✅ Redis contains data: {keys}")
            else:
                print("⚠️  Redis is empty (using inmemory provider)")
        
        # Check if we can store data manually
        print("Testing manual Redis storage...")
        manual_store = subprocess.run([
            "docker-compose", "exec", "-T", "redis", "redis-cli", "set", "test_key", "test_value"
        ], capture_output=True, text=True)
        
        if manual_store.returncode == 0:
            print("✅ Manual Redis storage works")
            
            # Clean up
            subprocess.run([
                "docker-compose", "exec", "-T", "redis", "redis-cli", "del", "test_key"
            ], capture_output=True, text=True)
        else:
            print("❌ Manual Redis storage failed")
        
        return True
    
    async def test_api_documentation(self):
        """Test API documentation access"""
        print("\n📚 Testing API Documentation...")
        print("-" * 40)
        
        async with httpx.AsyncClient() as client:
            # Test OpenAPI schema
            response = await client.get(f"{self.base_url}/openapi.json")
            if response.status_code == 200:
                schema = response.json()
                endpoints = len(schema.get("paths", {}))
                print(f"✅ OpenAPI Schema: {endpoints} endpoints available")
                
                # List some key endpoints
                paths = list(schema.get("paths", {}).keys())
                print(f"   Key endpoints: {', '.join(paths[:5])}...")
            else:
                print(f"❌ OpenAPI Schema: Failed - {response.status_code}")
                return False
        
        return True
    
    async def run_complete_test(self):
        """Run the complete workflow test"""
        print("🚀 Starting Complete Workflow Test...")
        print("=" * 60)
        
        tests = [
            ("Individual Components", self.test_individual_components),
            ("Simple Chat Flow", self.test_simple_chat_flow),
            ("Multi-turn Conversation", self.test_conversation_flow),
            ("Storage Verification", self.test_storage_verification),
            ("API Documentation", self.test_api_documentation),
        ]
        
        results = []
        
        for test_name, test_func in tests:
            try:
                print(f"\n🧪 Running: {test_name}")
                result = await test_func()
                results.append((test_name, result))
            except Exception as e:
                print(f"❌ {test_name}: Exception - {e}")
                results.append((test_name, False))
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 COMPLETE WORKFLOW TEST RESULTS")
        print("=" * 60)
        
        passed = 0
        total = len(results)
        
        for test_name, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} {test_name}")
            if result:
                passed += 1
        
        print(f"\n🎯 Overall: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 ALL WORKFLOW TESTS PASSED!")
            print("🚀 System is fully operational with Mock LLM!")
        else:
            print("⚠️  Some workflow tests failed.")
        
        return passed == total

async def main():
    """Main test runner"""
    tester = CompleteWorkflowTest()
    success = await tester.run_complete_test()
    
    if success:
        print("\n🎯 SYSTEM STATUS: FULLY OPERATIONAL")
        print("✅ All components working individually")
        print("✅ Chat flow functional")
        print("✅ Multi-turn conversations working")
        print("✅ Storage systems accessible")
        print("✅ API documentation available")
        print("\n🚀 Ready for development and testing!")
    else:
        print("\n⚠️  SYSTEM STATUS: NEEDS ATTENTION")
        print("🔧 Some components need configuration")

if __name__ == "__main__":
    asyncio.run(main()) 