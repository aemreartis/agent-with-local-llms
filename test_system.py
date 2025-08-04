#!/usr/bin/env python3
"""
Simple test script to demonstrate the Agentic RAG system functionality
"""

import asyncio
import httpx
import json

async def test_system():
    """Test the basic functionality of the system"""
    
    print("🧪 Testing Agentic RAG System...")
    print("=" * 50)
    
    # Test health endpoint
    print("1. Testing Health Check...")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8000/health")
            if response.status_code == 200:
                health_data = response.json()
                print(f"✅ Health Check: {health_data['status']}")
                print(f"   Services: {list(health_data['services'].keys())}")
            else:
                print(f"❌ Health Check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Health Check error: {e}")
    
    print("\n2. Testing API Documentation...")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8000/openapi.json")
            if response.status_code == 200:
                api_spec = response.json()
                endpoints = list(api_spec['paths'].keys())
                print(f"✅ API Documentation: {len(endpoints)} endpoints available")
                print(f"   Available endpoints: {endpoints[:5]}...")
            else:
                print(f"❌ API Documentation failed: {response.status_code}")
    except Exception as e:
        print(f"❌ API Documentation error: {e}")
    
    print("\n3. Testing Chat Endpoint...")
    try:
        async with httpx.AsyncClient() as client:
            chat_data = {
                "message": "Hello! Can you tell me about artificial intelligence?",
                "user_id": "test_user_123"
            }
            response = await client.post("http://localhost:8000/chat", json=chat_data)
            if response.status_code == 200:
                chat_response = response.json()
                print(f"✅ Chat Response: {chat_response.get('response', 'No response')[:100]}...")
            else:
                print(f"❌ Chat failed: {response.status_code}")
                print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Chat error: {e}")
    
    print("\n4. Testing Document Upload...")
    try:
        async with httpx.AsyncClient() as client:
            # Create a simple text file for testing
            test_content = "This is a test document about machine learning and artificial intelligence."
            files = {"file": ("test.txt", test_content, "text/plain")}
            data = {"metadata": json.dumps({"title": "Test Document", "category": "test"})}
            
            response = await client.post("http://localhost:8000/documents/upload", files=files, data=data)
            if response.status_code == 200:
                upload_response = response.json()
                print(f"✅ Document Upload: {upload_response.get('message', 'Uploaded')}")
            else:
                print(f"❌ Document Upload failed: {response.status_code}")
                print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Document Upload error: {e}")
    
    print("\n5. Testing Search...")
    try:
        async with httpx.AsyncClient() as client:
            search_data = {
                "query": "machine learning",
                "top_k": 5
            }
            response = await client.post("http://localhost:8000/search", json=search_data)
            if response.status_code == 200:
                search_response = response.json()
                print(f"✅ Search: Found {len(search_response.get('results', []))} results")
            else:
                print(f"❌ Search failed: {response.status_code}")
                print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Search error: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 System Test Complete!")
    print("\n📊 System Status:")
    print("   - FastAPI App: http://localhost:8000")
    print("   - API Docs: http://localhost:8000/docs")
    print("   - PostgreSQL: localhost:5433")
    print("   - Redis: localhost:6380")
    print("   - Qdrant: localhost:6333")

if __name__ == "__main__":
    asyncio.run(test_system()) 