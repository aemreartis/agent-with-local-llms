#!/usr/bin/env python3
"""
RAG Pipeline Test Script

Demonstrates the complete flow: User Input → RAG → Rerank → LLM → Agent Response
"""

import asyncio
import json
from datetime import datetime

# Mock components for demonstration
from unittest.mock import Mock, AsyncMock

def create_mock_components():
    """Create mock components for testing the RAG pipeline"""
    
    # Mock search orchestrator
    mock_search = Mock()
    mock_search.search = AsyncMock(return_value={
        "results": [
            {
                "id": "doc1",
                "content": "Artificial Intelligence (AI) is a branch of computer science that aims to create intelligent machines that work and react like humans.",
                "metadata": {"source": "ai_textbook", "title": "Introduction to AI"},
                "score": 0.95
            },
            {
                "id": "doc2",
                "content": "Machine Learning is a subset of AI that enables computers to learn and make decisions without being explicitly programmed.",
                "metadata": {"source": "ml_guide", "title": "Machine Learning Basics"},
                "score": 0.88
            },
            {
                "id": "doc3",
                "content": "Neural networks are computational models inspired by biological neural networks in human brains.",
                "metadata": {"source": "neural_networks", "title": "Neural Networks Explained"},
                "score": 0.82
            }
        ],
        "total": 3
    })
    mock_search.health_check = AsyncMock(return_value={"status": "healthy"})
    
    # Mock reranker
    mock_reranker = Mock()
    mock_reranker.rerank = AsyncMock(return_value=[
        {
            "id": "doc1",
            "content": "Artificial Intelligence (AI) is a branch of computer science that aims to create intelligent machines that work and react like humans.",
            "metadata": {"source": "ai_textbook", "title": "Introduction to AI"},
            "score": 0.98
        },
        {
            "id": "doc2",
            "content": "Machine Learning is a subset of AI that enables computers to learn and make decisions without being explicitly programmed.",
            "metadata": {"source": "ml_guide", "title": "Machine Learning Basics"},
            "score": 0.92
        }
    ])
    mock_reranker.health_check = AsyncMock(return_value={"status": "healthy"})
    
    # Mock LLM provider
    mock_llm = Mock()
    mock_llm.generate = AsyncMock(return_value="""Based on the information provided, Artificial Intelligence (AI) is a branch of computer science focused on creating intelligent machines that can work and react like humans. Machine Learning is a specific subset of AI that enables computers to learn and make decisions without being explicitly programmed for every task.

Key points:
- AI aims to create intelligent machines that mimic human behavior
- Machine Learning is a subset of AI that focuses on learning from data
- Neural networks are computational models inspired by biological brains
- These technologies work together to create increasingly sophisticated AI systems""")
    mock_llm.health_check = AsyncMock(return_value={"status": "healthy"})
    
    # Mock memory provider
    mock_memory = Mock()
    mock_memory.retrieve = AsyncMock(return_value=[])
    mock_memory.store = AsyncMock(return_value=True)
    mock_memory.clear = AsyncMock(return_value=True)
    mock_memory.health_check = AsyncMock(return_value={"status": "healthy"})
    
    return {
        "search_orchestrator": mock_search,
        "reranker": mock_reranker,
        "llm_provider": mock_llm,
        "memory_provider": mock_memory
    }

async def test_rag_pipeline():
    """Test the RAG pipeline with mock components"""
    
    print("🚀 RAG Pipeline Test")
    print("=" * 50)
    print("Flow: User Input → RAG → Rerank → LLM → Agent Response")
    print("=" * 50)
    
    # Create mock components
    components = create_mock_components()
    
    # Import and create RAG pipeline
    from src.orchestration.rag_pipeline import RAGPipelineOrchestrator
    
    # Configuration
    config = {
        "search_top_k": 5,
        "rerank_top_k": 3,
        "max_context_length": 2000,
        "enable_memory": True,
        "max_tokens": 500,
        "temperature": 0.7
    }
    
    # Create RAG pipeline
    rag_pipeline = RAGPipelineOrchestrator(
        search_orchestrator=components["search_orchestrator"],
        reranker=components["reranker"],
        llm_provider=components["llm_provider"],
        memory_provider=components["memory_provider"],
        config=config
    )
    
    # Test queries
    test_queries = [
        "What is artificial intelligence?",
        "How does machine learning relate to AI?",
        "Explain neural networks in simple terms"
    ]
    
    user_id = "test_user_123"
    conversation_id = "test_conversation_456"
    
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
            print(f"🤖 Agent Response:")
            print(f"   {response['agent_response']}")
            
            # Display metrics
            metrics = response['pipeline_metrics']
            print(f"\n📊 Pipeline Metrics:")
            print(f"   - Search Duration: {metrics['search_duration']:.3f}s")
            print(f"   - Rerank Duration: {metrics['rerank_duration']:.3f}s")
            print(f"   - LLM Duration: {metrics['llm_duration']:.3f}s")
            print(f"   - Search Results: {metrics['search_results_count']}")
            print(f"   - Reranked Results: {metrics['reranked_results_count']}")
            print(f"   - Context Length: {metrics['context_length']} chars")
            
            # Display search results
            print(f"\n🔍 Search Results:")
            for j, result in enumerate(response['search_results'][:2], 1):
                print(f"   {j}. {result['content'][:100]}...")
                print(f"      Score: {result['score']:.2f}")
            
            # Display reranked results
            print(f"\n📈 Reranked Results:")
            for j, result in enumerate(response['reranked_results'][:2], 1):
                print(f"   {j}. {result['content'][:100]}...")
                print(f"      Score: {result['score']:.2f}")
        else:
            print(f"❌ Error: {response.get('error', 'Unknown error')}")
        
        print("\n" + "-" * 50)
    
    # Test health check
    print("\n🏥 Health Check:")
    health_status = await rag_pipeline.health_check()
    print(f"Overall Status: {health_status['status']}")
    
    for component, status in health_status['components'].items():
        print(f"  - {component}: {status['status']}")
    
    print("\n✅ RAG Pipeline Test Complete!")

async def test_conversation_memory():
    """Test conversation memory functionality"""
    
    print("\n🧠 Conversation Memory Test")
    print("=" * 50)
    
    # Create mock components
    components = create_mock_components()
    
    # Import and create RAG pipeline
    from src.orchestration.rag_pipeline import RAGPipelineOrchestrator
    
    # Configuration with memory enabled
    config = {
        "search_top_k": 5,
        "rerank_top_k": 3,
        "enable_memory": True
    }
    
    # Create RAG pipeline
    rag_pipeline = RAGPipelineOrchestrator(
        search_orchestrator=components["search_orchestrator"],
        reranker=components["reranker"],
        llm_provider=components["llm_provider"],
        memory_provider=components["memory_provider"],
        config=config
    )
    
    user_id = "memory_test_user"
    conversation_id = "memory_test_conv"
    
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
    
    print("\n✅ Conversation Memory Test Complete!")

async def test_pipeline_components():
    """Test individual pipeline components"""
    
    print("\n🔧 Pipeline Components Test")
    print("=" * 50)
    
    # Create mock components
    components = create_mock_components()
    
    # Test search orchestrator
    print("\n🔍 Testing Search Orchestrator:")
    search_results = await components["search_orchestrator"].search(
        query="What is AI?",
        top_k=3
    )
    print(f"Search Results: {len(search_results['results'])} documents found")
    for i, result in enumerate(search_results['results'], 1):
        print(f"  {i}. {result['content'][:80]}... (Score: {result['score']:.2f})")
    
    # Test reranker
    print("\n📈 Testing Reranker:")
    documents = [
        {"id": "doc1", "content": "AI is artificial intelligence", "score": 0.8},
        {"id": "doc2", "content": "Machine learning is part of AI", "score": 0.7}
    ]
    reranked = await components["reranker"].rerank(
        query="What is AI?",
        documents=documents,
        top_k=2
    )
    print(f"Reranked Results: {len(reranked)} documents")
    for i, doc in enumerate(reranked, 1):
        print(f"  {i}. {doc['content']} (Score: {doc['score']:.2f})")
    
    # Test LLM provider
    print("\n🤖 Testing LLM Provider:")
    response = await components["llm_provider"].generate(
        prompt="Explain AI in one sentence:"
    )
    print(f"LLM Response: {response}")
    
    # Test memory provider
    print("\n🧠 Testing Memory Provider:")
    await components["memory_provider"].store("test_key", {"data": "test_value"})
    retrieved = await components["memory_provider"].retrieve("test_key")
    print(f"Stored and retrieved: {retrieved}")
    
    print("\n✅ Pipeline Components Test Complete!")

async def main():
    """Main function to run all tests"""
    
    print("🎯 RAG Pipeline Complete Test Suite")
    print("=" * 60)
    print("This test demonstrates the complete flow:")
    print("User Input → RAG → Rerank → LLM → Agent Response")
    print("=" * 60)
    
    try:
        # Test main pipeline
        await test_rag_pipeline()
        
        # Test conversation memory
        await test_conversation_memory()
        
        # Test individual components
        await test_pipeline_components()
        
        print("\n🎉 All tests completed successfully!")
        print("\n📚 Next Steps:")
        print("1. Replace mock components with real implementations")
        print("2. Add your documents to the vector store")
        print("3. Configure your LLM provider (vLLM, OpenAI, etc.)")
        print("4. Deploy the pipeline to production!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Run the tests
    asyncio.run(main()) 