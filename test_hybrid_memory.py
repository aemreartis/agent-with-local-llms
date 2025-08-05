#!/usr/bin/env python3
"""
Test Hybrid Memory System
Demonstrates Redis (short-term) + PostgreSQL (long-term) memory strategy
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from src.providers.memory.hybrid_provider import HybridMemoryProvider

async def test_hybrid_memory_system():
    """Test the hybrid memory system with Redis and PostgreSQL."""
    print("🚀 Testing Hybrid Memory System (Redis + PostgreSQL)")
    print("=" * 70)
    
    # Initialize hybrid provider
    config = {
        "redis_ttl": 10,  # 10 seconds for testing
        "migration_enabled": True,
        "migration_batch_size": 100,
        "redis": {
            "host": "localhost",
            "port": 6380,
            "db": 0,
            "password": None,
            "prefix": "agentic_rag:",
            "default_ttl": 10
        },
        "postgresql": {
            "host": "localhost",
            "port": 5433,
            "database": "agentic_rag",
            "username": "rag_user",
            "password": "rag_password",
            "table_name": "conversation_memory",
            "max_connections": 10
        }
    }
    
    hybrid_provider = HybridMemoryProvider()
    
    try:
        # Initialize the provider
        print("🔧 Initializing Hybrid Memory Provider...")
        await hybrid_provider.initialize(config)
        print("✅ Hybrid provider initialized successfully")
        
        # Test 1: Store data in both Redis and PostgreSQL
        print("\n📝 Test 1: Storing Data in Both Systems")
        print("-" * 50)
        
        conversation_id = "hybrid_test_conv_001"
        test_message = {
            "role": "user",
            "content": "Hello! This is a test of the hybrid memory system.",
            "timestamp": datetime.now().isoformat(),
            "user_id": "test_user_001"
        }
        
        # Store the message
        store_success = await hybrid_provider.store(conversation_id, test_message)
        print(f"✅ Store operation: {'Success' if store_success else 'Failed'}")
        
        # Test 2: Retrieve from Redis (fast access)
        print("\n⚡ Test 2: Fast Retrieval from Redis")
        print("-" * 50)
        
        start_time = time.time()
        redis_data = await hybrid_provider.retrieve(conversation_id)
        redis_time = time.time() - start_time
        
        if redis_data:
            print(f"✅ Retrieved from Redis in {redis_time:.4f}s")
            print(f"   Message: {redis_data[0].get('content', 'No content')[:50]}...")
        else:
            print("❌ No data retrieved from Redis")
        
        # Test 3: Wait for Redis TTL to expire
        print(f"\n⏰ Test 3: Waiting for Redis TTL to expire ({config['redis_ttl']}s)...")
        print("-" * 50)
        
        print("   Waiting...", end="", flush=True)
        for i in range(config['redis_ttl'] + 2):
            await asyncio.sleep(1)
            print(".", end="", flush=True)
        print()
        
        # Test 4: Retrieve from PostgreSQL (fallback)
        print("\n🗄️ Test 4: Fallback Retrieval from PostgreSQL")
        print("-" * 50)
        
        start_time = time.time()
        postgresql_data = await hybrid_provider.retrieve(conversation_id)
        postgresql_time = time.time() - start_time
        
        if postgresql_data:
            print(f"✅ Retrieved from PostgreSQL in {postgresql_time:.4f}s")
            print(f"   Message: {postgresql_data[0].get('content', 'No content')[:50]}...")
            print(f"   ⚡ Redis was {redis_time/postgresql_time:.1f}x faster than PostgreSQL")
        else:
            print("❌ No data retrieved from PostgreSQL")
        
        # Test 5: Test conversation flow simulation
        print("\n💬 Test 5: Simulating Conversation Flow")
        print("-" * 50)
        
        conversation_messages = [
            {"role": "user", "content": "What is artificial intelligence?", "timestamp": datetime.now().isoformat()},
            {"role": "assistant", "content": "AI is a branch of computer science...", "timestamp": datetime.now().isoformat()},
            {"role": "user", "content": "Can you give me examples?", "timestamp": datetime.now().isoformat()},
            {"role": "assistant", "content": "Examples include machine learning, NLP...", "timestamp": datetime.now().isoformat()}
        ]
        
        conv_id = "conversation_flow_test"
        for i, message in enumerate(conversation_messages):
            key = f"{conv_id}_{i}"
            success = await hybrid_provider.store(key, message)
            print(f"   Message {i+1}: {'✅ Stored' if success else '❌ Failed'}")
        
        # Retrieve conversation history
        print("\n📖 Retrieving Conversation History:")
        for i in range(len(conversation_messages)):
            key = f"{conv_id}_{i}"
            data = await hybrid_provider.retrieve(key)
            if data:
                role = data[0].get('role', 'unknown')
                content = data[0].get('content', '')[:40] + "..." if len(data[0].get('content', '')) > 40 else data[0].get('content', '')
                print(f"   {role.upper()}: {content}")
        
        # Test 6: Provider statistics
        print("\n📊 Test 6: Provider Statistics")
        print("-" * 50)
        
        stats = await hybrid_provider.get_conversation_stats()
        print("Hybrid Memory Provider Statistics:")
        print(f"   Redis TTL: {stats.get('hybrid_config', {}).get('redis_ttl', 'N/A')}s")
        print(f"   Migration Enabled: {stats.get('hybrid_config', {}).get('migration_enabled', 'N/A')}")
        print(f"   Redis Info: {stats.get('redis_stats', {}).get('provider_type', 'N/A')}")
        print(f"   PostgreSQL Info: {stats.get('postgresql_stats', {}).get('provider_type', 'N/A')}")
        
        # Test 7: Health check
        print("\n🏥 Test 7: Health Check")
        print("-" * 50)
        
        health_status = await hybrid_provider.health_check()
        print(f"   Overall Health: {'✅ Healthy' if health_status else '❌ Unhealthy'}")
        
        # Test 8: Clear data
        print("\n🧹 Test 8: Clearing Data")
        print("-" * 50)
        
        clear_success = await hybrid_provider.clear(conversation_id)
        print(f"   Clear operation: {'✅ Success' if clear_success else '❌ Failed'}")
        
        # Verify data is cleared
        cleared_data = await hybrid_provider.retrieve(conversation_id)
        print(f"   Data after clear: {'✅ Cleared' if not cleared_data else '❌ Still exists'}")
        
        print("\n🎉 Hybrid Memory System Test Complete!")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

async def demonstrate_memory_strategies():
    """Demonstrate different memory strategies."""
    print("\n🎯 Memory Strategy Demonstrations")
    print("=" * 70)
    
    strategies = [
        {
            "name": "Redis Only (Fast Cache)",
            "description": "Ultra-fast access, data expires",
            "use_case": "Active conversations, session data",
            "pros": ["⚡ Very fast", "🔄 Automatic cleanup", "💾 Memory efficient"],
            "cons": ["❌ Data loss on restart", "⏰ TTL expiration", "📊 Limited storage"]
        },
        {
            "name": "PostgreSQL Only (Persistent)",
            "description": "Permanent storage, slower access",
            "use_case": "Long-term conversation history, analytics",
            "pros": ["💾 Permanent storage", "🔍 Full SQL queries", "📊 Unlimited storage"],
            "cons": ["🐌 Slower access", "💾 Higher storage cost", "🔧 Complex queries"]
        },
        {
            "name": "Hybrid (Best of Both)",
            "description": "Redis cache + PostgreSQL persistence",
            "use_case": "Production systems, optimal performance",
            "pros": ["⚡ Fast active access", "💾 Permanent storage", "🔄 Automatic migration"],
            "cons": ["🔧 More complex", "💰 Higher infrastructure cost", "⚙️ More configuration"]
        }
    ]
    
    for strategy in strategies:
        print(f"\n📋 {strategy['name']}")
        print(f"   Description: {strategy['description']}")
        print(f"   Use Case: {strategy['use_case']}")
        print(f"   Pros: {' '.join(strategy['pros'])}")
        print(f"   Cons: {' '.join(strategy['cons'])}")

def show_configuration_examples():
    """Show configuration examples for different memory strategies."""
    print("\n⚙️ Configuration Examples")
    print("=" * 70)
    
    configs = {
        "redis_only": {
            "default": "redis",
            "description": "Fast cache for active conversations",
            "config": {
                "host": "localhost",
                "port": 6380,
                "default_ttl": 3600,  # 1 hour
                "prefix": "agentic_rag:"
            }
        },
        "postgresql_only": {
            "default": "postgresql", 
            "description": "Permanent storage for all conversations",
            "config": {
                "host": "localhost",
                "port": 5433,
                "database": "agentic_rag",
                "table_name": "conversation_memory"
            }
        },
        "hybrid": {
            "default": "hybrid",
            "description": "Redis cache + PostgreSQL persistence",
            "config": {
                "redis_ttl": 3600,  # 1 hour in Redis
                "migration_enabled": True,
                "redis": {"host": "localhost", "port": 6380, "default_ttl": 3600},
                "postgresql": {"host": "localhost", "port": 5433, "database": "agentic_rag"}
            }
        }
    }
    
    for name, config in configs.items():
        print(f"\n🔧 {name.upper()} Configuration:")
        print(f"   Purpose: {config['description']}")
        print(f"   Default: {config['default']}")
        print(f"   Key Settings: {json.dumps(config['config'], indent=2)}")

async def main():
    """Main test function."""
    print("🚀 Hybrid Memory System Demonstration")
    print("=" * 70)
    
    # Run the hybrid memory test
    await test_hybrid_memory_system()
    
    # Show strategy demonstrations
    await demonstrate_memory_strategies()
    
    # Show configuration examples
    show_configuration_examples()
    
    print("\n💡 Usage Tips:")
    print("   • Use Redis TTL based on conversation activity patterns")
    print("   • Enable migration for seamless data persistence")
    print("   • Monitor both Redis and PostgreSQL health")
    print("   • Consider backup strategies for PostgreSQL data")
    print("   • Use Redis for session data, PostgreSQL for history")

if __name__ == "__main__":
    asyncio.run(main()) 