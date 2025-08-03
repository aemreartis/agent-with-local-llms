#!/usr/bin/env python3
"""
Simple test runner for orchestration tests.
"""

import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

async def run_search_orchestrator_tests():
    """Run Search Orchestrator tests."""
    try:
        # Import test modules
        from tests.orchestration.test_search_orchestrator import TestSearchOrchestrator
        
        # Create test instance
        test_instance = TestSearchOrchestrator()
        
        # Run basic tests
        print("🧪 Running Search Orchestrator Tests...")
        
        # Test 1: Interface implementation
        print("  ✅ Testing interface implementation...")
        await test_instance.test_search_orchestrator_implements_interface()
        
        # Test 2: Service info
        print("  ✅ Testing service info...")
        test_instance.test_get_service_info()
        
        # Test 3: Result normalization
        print("  ✅ Testing result normalization...")
        await test_instance.test_result_normalization(
            test_instance.mock_provider_registry(),
            test_instance.search_orchestrator_config()
        )
        
        # Test 4: RRF fusion
        print("  ✅ Testing RRF fusion...")
        await test_instance.test_reciprocal_rank_fusion(
            test_instance.mock_provider_registry(),
            test_instance.search_orchestrator_config()
        )
        
        # Test 5: Fusion strategies
        print("  ✅ Testing fusion strategies...")
        await test_instance.test_fusion_strategies(
            test_instance.mock_provider_registry(),
            test_instance.search_orchestrator_config()
        )
        
        print("🎉 All basic tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(run_search_orchestrator_tests())
    sys.exit(0 if success else 1) 