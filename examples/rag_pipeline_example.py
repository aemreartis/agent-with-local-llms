#!/usr/bin/env python3
"""
RAG Pipeline Example

Demonstrates the complete flow: User Input → RAG → Rerank → LLM → Agent Response
"""

import asyncio
import json
from datetime import datetime

# Import the RAG pipeline
from src.orchestration.rag_pipeline import RAGPipelineOrchestrator

# Import providers (you'll need to initialize these with your config)
from src.providers.llm.vllm_provider import VLLMProvider
from src.providers.memory.redis_provider import RedisMemoryProvider
from src.providers.rerankers.bge_provider import BGERerankerProvider
from src.orchestration.search_orchestrator import SearchOrchestrator


async def setup_rag_pipeline():
    """Setup the complete RAG pipeline with all components"""
    
    print("🔧 Setting up RAG Pipeline...")
    
    # Configuration
    config = {
        "search_top_k": 10,
        "rerank_top_k": 5,
        "max_context_length": 4000,
        "enable_memory": True,
        "max_tokens": 1000,
        "temperature": 0.7,
        "stop_tokens": []
    }
    
    # Initialize providers (you'll need to adjust these based on your setup)
    try:
        # LLM Provider
        llm_provider = VLLMProvider()
        await llm_provider.initialize({
            "base_url": "http://localhost:8001",
            "model": "llama-2-7b",
            "temperature": 0.7,
            "max_tokens": 1000
        })
        
        # Memory Provider
        memory_provider = RedisMemoryProvider()
        await memory_provider.initialize({
            "host": "localhost",
            "port": 6380,
            "db": 0,
            "prefix": "rag_pipeline:"
        })
        
        # Reranker Provider
        reranker = BGERerankerProvider()
        await reranker.initialize({
            "model_name": "BAAI/bge-reranker-base",
            "device": "cpu"
        })
        
        # Search Orchestrator (you'll need to initialize this with your vector store)
        search_orchestrator = SearchOrchestrator()
        # Note: You'll need to initialize this with your actual search configuration
        
        print("✅ All providers initialized successfully")
        
    except Exception as e:
        print(f"❌ Error initializing providers: {e}")
        print("Using mock providers for demonstration...")
        
        # Use mock providers for demonstration
        from unittest.mock import Mock, AsyncMock
        
        llm_provider = Mock()
        llm_provider.generate = AsyncMock(return_value="This is a mock response from the LLM provider.")
        llm_provider.health_check = AsyncMock(return_value={"status": "healthy"})
        
        memory_provider = Mock()
        memory_provider.retrieve = AsyncMock(return_value=[])
        memory_provider.store = AsyncMock(return_value=True)
        memory_provider.health_check = AsyncMock(return_value={"status": "healthy"})
        
        reranker = Mock()
        reranker.rerank = AsyncMock(return_value=[])
        reranker.health_check = AsyncMock(return_value={"status": "healthy"})
        
        search_orchestrator = Mock()
        search_orchestrator.search = AsyncMock(return_value={"results": []})
        search_orchestrator.health_check = AsyncMock(return_value={"status": "healthy"})
    
    # Create RAG Pipeline
    rag_pipeline = RAGPipelineOrchestrator(
        search_orchestrator=search_orchestrator,
        reranker=reranker,
        llm_provider=llm_provider,
        memory_provider=memory_provider,
        config=config
    )
    
    return rag_pipeline


async def run_rag_pipeline_example():
    """Run the RAG pipeline example"""
    
    print("🚀 RAG Pipeline Example")
    print("=" * 50)
    
    # Setup pipeline
    rag_pipeline = await setup_rag_pipeline()
    
    # Test queries
    test_queries = [
        "What is artificial intelligence?",
        "How does machine learning work?",
        "Explain neural networks in simple terms",
        "What are the applications of AI in healthcare?"
    ]
    
    user_id = "example_user_123"
    conversation_id = "example_conversation_456"
    
    print(f"\n👤 User ID: {user_id}")
    print(f"💬 Conversation ID: {conversation_id}")
    print("\n" + "=" * 50)
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n🔍 Query {i}: {query}")
        print("-" * 30)
        
        # Process query through pipeline
        start_time = datetime.now()
        
        response = await rag_pipeline.process_query(
            user_input=query,
            user_id=user_id,
            conversation_id=conversation_id
        )
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Display results
        print(f"✅ Status: {response['status']}")
        print(f"⏱️  Total Duration: {duration:.2f}s")
        
        if response['status'] == 'success':
            print(f"🤖 Agent Response: {response['agent_response'][:200]}...")
            
            # Display metrics
            metrics = response['pipeline_metrics']
            print(f"📊 Pipeline Metrics:")
            print(f"   - Search Duration: {metrics['search_duration']:.3f}s")
            print(f"   - Rerank Duration: {metrics['rerank_duration']:.3f}s")
            print(f"   - LLM Duration: {metrics['llm_duration']:.3f}s")
            print(f"   - Search Results: {metrics['search_results_count']}")
            print(f"   - Reranked Results: {metrics['reranked_results_count']}")
            print(f"   - Context Length: {metrics['context_length']} chars")
        else:
            print(f"❌ Error: {response.get('error', 'Unknown error')}")
        
        print("\n" + "-" * 50)
    
    # Test health check
    print("\n🏥 Health Check:")
    health_status = await rag_pipeline.health_check()
    print(f"Overall Status: {health_status['status']}")
    
    for component, status in health_status['components'].items():
        print(f"  - {component}: {status['status']}")
    
    print("\n✅ RAG Pipeline Example Complete!")


async def demonstrate_conversation_memory():
    """Demonstrate conversation memory functionality"""
    
    print("\n🧠 Conversation Memory Demonstration")
    print("=" * 50)
    
    # Setup pipeline
    rag_pipeline = await setup_rag_pipeline()
    
    user_id = "memory_demo_user"
    conversation_id = "memory_demo_conv"
    
    # First query
    print("\n1️⃣ First Query:")
    response1 = await rag_pipeline.process_query(
        user_input="What is artificial intelligence?",
        user_id=user_id,
        conversation_id=conversation_id
    )
    print(f"Response: {response1['agent_response'][:100]}...")
    
    # Second query (should have context from first)
    print("\n2️⃣ Second Query (with context):")
    response2 = await rag_pipeline.process_query(
        user_input="How does it relate to machine learning?",
        user_id=user_id,
        conversation_id=conversation_id
    )
    print(f"Response: {response2['agent_response'][:100]}...")
    
    # Third query (should have context from both previous)
    print("\n3️⃣ Third Query (with full context):")
    response3 = await rag_pipeline.process_query(
        user_input="What are some real-world applications?",
        user_id=user_id,
        conversation_id=conversation_id
    )
    print(f"Response: {response3['agent_response'][:100]}...")
    
    print("\n✅ Conversation Memory Demo Complete!")


async def demonstrate_error_handling():
    """Demonstrate error handling in the pipeline"""
    
    print("\n🛡️ Error Handling Demonstration")
    print("=" * 50)
    
    # Setup pipeline with problematic components
    from unittest.mock import Mock, AsyncMock
    
    # Create components that will fail
    failing_search = Mock()
    failing_search.search = AsyncMock(side_effect=Exception("Search service unavailable"))
    failing_search.health_check = AsyncMock(return_value={"status": "unhealthy"})
    
    failing_llm = Mock()
    failing_llm.generate = AsyncMock(side_effect=Exception("LLM service unavailable"))
    failing_llm.health_check = AsyncMock(return_value={"status": "unhealthy"})
    
    # Use working components for others
    from unittest.mock import Mock, AsyncMock
    
    memory_provider = Mock()
    memory_provider.retrieve = AsyncMock(return_value=[])
    memory_provider.store = AsyncMock(return_value=True)
    memory_provider.health_check = AsyncMock(return_value={"status": "healthy"})
    
    reranker = Mock()
    reranker.rerank = AsyncMock(return_value=[])
    reranker.health_check = AsyncMock(return_value={"status": "healthy"})
    
    # Create pipeline with failing components
    config = {
        "search_top_k": 5,
        "rerank_top_k": 3,
        "enable_memory": True
    }
    
    rag_pipeline = RAGPipelineOrchestrator(
        search_orchestrator=failing_search,
        reranker=reranker,
        llm_provider=failing_llm,
        memory_provider=memory_provider,
        config=config
    )
    
    # Test error handling
    print("\n🔍 Testing with failing search service:")
    response = await rag_pipeline.process_query(
        user_input="What is AI?",
        user_id="error_test_user"
    )
    
    print(f"Status: {response['status']}")
    print(f"Error: {response.get('error', 'No error')}")
    print(f"Response: {response['agent_response']}")
    
    print("\n✅ Error Handling Demo Complete!")


async def main():
    """Main function to run all examples"""
    
    print("🎯 RAG Pipeline Complete Example")
    print("=" * 60)
    print("This example demonstrates the complete flow:")
    print("User Input → RAG → Rerank → LLM → Agent Response")
    print("=" * 60)
    
    try:
        # Run main example
        await run_rag_pipeline_example()
        
        # Run conversation memory demo
        await demonstrate_conversation_memory()
        
        # Run error handling demo
        await demonstrate_error_handling()
        
        print("\n🎉 All examples completed successfully!")
        print("\n📚 Next Steps:")
        print("1. Configure your actual providers (LLM, Vector Store, etc.)")
        print("2. Add your documents to the vector store")
        print("3. Customize the pipeline configuration")
        print("4. Deploy to production!")
        
    except Exception as e:
        print(f"\n❌ Example failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Run the example
    asyncio.run(main()) 