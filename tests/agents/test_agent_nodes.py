"""Unit tests for Agent Node Implementations.

Tests individual agent nodes for reasoning, decision making, and task execution.
"""

import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime
from typing import Dict, Any

from src.interfaces.agent_interface import (
    AgentExecutionState, AgentContext, AgentState, AgentNodeInterface,
    ToolResult, ToolInterface
)
from src.agents.agent_nodes import ReasoningNode, DecisionNode, ActionNode


pytestmark = pytest.mark.asyncio


class TestReasoningNode:
    """Test reasoning node implementation."""
    
    async def test_reasoning_node_initialization(self):
        """Test reasoning node initialization."""
        node = ReasoningNode()
        config = {
            "model": "gpt-4",
            "temperature": 0.7,
            "max_tokens": 1000,
            "reasoning_prompt_template": "Think step by step about: {input}"
        }
        
        await node.initialize(config)
        
        assert node._initialized is True
        assert node._config == config
        assert node._model == "gpt-4"
        assert node._temperature == 0.7
        assert node._max_tokens == 1000
    
    async def test_reasoning_node_initialization_with_defaults(self):
        """Test reasoning node initialization with default values."""
        node = ReasoningNode()
        config = {}
        
        await node.initialize(config)
        
        assert node._initialized is True
        assert node._config == config
        assert node._model == "default"
        assert node._temperature == 0.5
        assert node._max_tokens == 500
    
    async def test_reasoning_node_execute_success(self):
        """Test successful reasoning node execution."""
        node = ReasoningNode()
        await node.initialize({"model": "test-model"})
        
        context = AgentContext(session_id="test_session")
        state = AgentState(
            state=AgentExecutionState.IDLE,
            context=context,
            data={"query": "What is the capital of France?"}
        )
        
        result_state = await node.execute(state, context)
        
        assert result_state.state == AgentExecutionState.COMPLETED
        assert "reasoning" in result_state.data
        assert "answer" in result_state.data
        assert len(result_state.history) > 0
        assert result_state.current_step == "reasoning_complete"
    
    async def test_reasoning_node_execute_with_complex_query(self):
        """Test reasoning node with complex multi-step query."""
        node = ReasoningNode()
        await node.initialize({"model": "test-model"})
        
        context = AgentContext(session_id="test_session")
        state = AgentState(
            state=AgentExecutionState.IDLE,
            context=context,
            data={
                "query": "If a train travels 120 km in 2 hours, what is its average speed?",
                "steps": ["calculate_speed", "verify_result"]
            }
        )
        
        result_state = await node.execute(state, context)
        
        assert result_state.state == AgentExecutionState.COMPLETED
        assert "reasoning" in result_state.data
        assert "steps_completed" in result_state.data
        assert result_state.data["steps_completed"] == ["calculate_speed", "verify_result"]
    
    async def test_reasoning_node_execute_not_initialized(self):
        """Test reasoning node execution when not initialized raises error."""
        node = ReasoningNode()
        
        context = AgentContext(session_id="test_session")
        state = AgentState(state=AgentExecutionState.IDLE, context=context)
        
        with pytest.raises(RuntimeError, match="Reasoning node not initialized"):
            await node.execute(state, context)
    
    async def test_reasoning_node_execute_with_error(self):
        """Test reasoning node execution with error handling."""
        node = ReasoningNode()
        await node.initialize({"model": "test-model"})
        
        context = AgentContext(session_id="test_session")
        state = AgentState(
            state=AgentExecutionState.IDLE,
            context=context,
            data={"query": "invalid_query_that_causes_error"}
        )
        
        # Mock the reasoning to fail
        node._mock_reasoning_failure = True
        
        result_state = await node.execute(state, context)
        
        assert result_state.state == AgentExecutionState.FAILED
        assert "error" in result_state.data
        assert "reasoning_failed" in result_state.error
    
    async def test_reasoning_node_health_check(self):
        """Test reasoning node health check."""
        node = ReasoningNode()
        await node.initialize({"model": "test-model"})
        
        health = await node.health_check()
        assert health is True
    
    async def test_reasoning_node_health_check_not_initialized(self):
        """Test health check when not initialized returns False."""
        node = ReasoningNode()
        
        health = await node.health_check()
        assert health is False
    
    async def test_reasoning_node_get_info(self):
        """Test getting reasoning node information."""
        node = ReasoningNode()
        await node.initialize({"model": "gpt-4", "temperature": 0.7})
        
        info = node.get_node_info()
        
        assert "type" in info
        assert info["type"] == "ReasoningNode"
        assert "model" in info
        assert info["model"] == "gpt-4"
        assert "temperature" in info
        assert info["temperature"] == 0.7
        assert "initialized" in info
        assert info["initialized"] is True
    
    async def test_reasoning_node_get_schemas(self):
        """Test getting input and output schemas."""
        node = ReasoningNode()
        await node.initialize({})
        
        input_schema = node.get_input_schema()
        output_schema = node.get_output_schema()
        
        assert "query" in input_schema["properties"]
        assert "reasoning" in output_schema["properties"]
        assert "answer" in output_schema["properties"]


class TestDecisionNode:
    """Test decision node implementation."""
    
    async def test_decision_node_initialization(self):
        """Test decision node initialization."""
        node = DecisionNode()
        config = {
            "decision_criteria": ["relevance", "confidence", "completeness"],
            "threshold": 0.8,
            "fallback_action": "request_clarification"
        }
        
        await node.initialize(config)
        
        assert node._initialized is True
        assert node._config == config
        assert node._decision_criteria == ["relevance", "confidence", "completeness"]
        assert node._threshold == 0.8
        assert node._fallback_action == "request_clarification"
    
    async def test_decision_node_execute_approve_decision(self):
        """Test decision node with approved decision."""
        node = DecisionNode()
        await node.initialize({"threshold": 0.7})
        
        context = AgentContext(session_id="test_session")
        state = AgentState(
            state=AgentExecutionState.IDLE,
            context=context,
            data={
                "proposal": "Implement feature X",
                "confidence": 0.9,
                "relevance": 0.8
            }
        )
        
        result_state = await node.execute(state, context)
        
        assert result_state.state == AgentExecutionState.COMPLETED
        assert "decision" in result_state.data
        assert result_state.data["decision"] == "approved"
        assert "confidence_score" in result_state.data
        assert result_state.data["confidence_score"] > 0.7
    
    async def test_decision_node_execute_reject_decision(self):
        """Test decision node with rejected decision."""
        node = DecisionNode()
        await node.initialize({"threshold": 0.9})
        
        context = AgentContext(session_id="test_session")
        state = AgentState(
            state=AgentExecutionState.IDLE,
            context=context,
            data={
                "proposal": "Implement feature Y",
                "confidence": 0.6,
                "relevance": 0.5
            }
        )
        
        result_state = await node.execute(state, context)
        
        assert result_state.state == AgentExecutionState.COMPLETED
        assert "decision" in result_state.data
        assert result_state.data["decision"] == "rejected"
        assert "confidence_score" in result_state.data
        assert result_state.data["confidence_score"] < 0.9
    
    async def test_decision_node_execute_with_fallback(self):
        """Test decision node with fallback action."""
        node = DecisionNode()
        await node.initialize({
            "threshold": 0.8,
            "fallback_action": "request_clarification"
        })
        
        context = AgentContext(session_id="test_session")
        state = AgentState(
            state=AgentExecutionState.IDLE,
            context=context,
            data={
                "proposal": "Unclear proposal",
                "confidence": 0.5
            }
        )
        
        result_state = await node.execute(state, context)
        
        assert result_state.state == AgentExecutionState.WAITING
        assert "action" in result_state.data
        assert result_state.data["action"] == "request_clarification"
        assert "reason" in result_state.data
    
    async def test_decision_node_health_check(self):
        """Test decision node health check."""
        node = DecisionNode()
        await node.initialize({"threshold": 0.8})
        
        health = await node.health_check()
        assert health is True
    
    async def test_decision_node_get_info(self):
        """Test getting decision node information."""
        node = DecisionNode()
        await node.initialize({
            "threshold": 0.8,
            "decision_criteria": ["relevance", "confidence"]
        })
        
        info = node.get_node_info()
        
        assert "type" in info
        assert info["type"] == "DecisionNode"
        assert "threshold" in info
        assert info["threshold"] == 0.8
        assert "criteria" in info
        assert info["criteria"] == ["relevance", "confidence"]


class TestActionNode:
    """Test action node implementation."""
    
    async def test_action_node_initialization(self):
        """Test action node initialization."""
        node = ActionNode()
        config = {
            "available_actions": ["search", "calculate", "format"],
            "timeout": 30.0,
            "retry_count": 3
        }
        
        await node.initialize(config)
        
        assert node._initialized is True
        assert node._config == config
        assert node._available_actions == ["search", "calculate", "format"]
        assert node._timeout == 30.0
        assert node._retry_count == 3
    
    async def test_action_node_execute_search_action(self):
        """Test action node with search action."""
        node = ActionNode()
        await node.initialize({"available_actions": ["search", "calculate"]})
        
        context = AgentContext(session_id="test_session")
        state = AgentState(
            state=AgentExecutionState.IDLE,
            context=context,
            data={
                "action": "search",
                "query": "Python programming best practices"
            }
        )
        
        result_state = await node.execute(state, context)
        
        assert result_state.state == AgentExecutionState.COMPLETED
        assert "action_result" in result_state.data
        assert "search_results" in result_state.data["action_result"]
        assert "execution_time" in result_state.data
    
    async def test_action_node_execute_calculate_action(self):
        """Test action node with calculate action."""
        node = ActionNode()
        await node.initialize({"available_actions": ["search", "calculate"]})
        
        context = AgentContext(session_id="test_session")
        state = AgentState(
            state=AgentExecutionState.IDLE,
            context=context,
            data={
                "action": "calculate",
                "expression": "2 + 2 * 3"
            }
        )
        
        result_state = await node.execute(state, context)
        
        assert result_state.state == AgentExecutionState.COMPLETED
        assert "action_result" in result_state.data
        assert "result" in result_state.data["action_result"]
        assert result_state.data["action_result"]["result"] == 8
    
    async def test_action_node_execute_invalid_action(self):
        """Test action node with invalid action."""
        node = ActionNode()
        await node.initialize({"available_actions": ["search", "calculate"]})
        
        context = AgentContext(session_id="test_session")
        state = AgentState(
            state=AgentExecutionState.IDLE,
            context=context,
            data={
                "action": "invalid_action",
                "query": "test"
            }
        )
        
        result_state = await node.execute(state, context)
        
        assert result_state.state == AgentExecutionState.FAILED
        assert "error" in result_state.data
        assert "invalid_action" in result_state.data["error"]
    
    async def test_action_node_execute_with_timeout(self):
        """Test action node with timeout handling."""
        node = ActionNode()
        await node.initialize({
            "available_actions": ["slow_action"],
            "timeout": 0.1
        })
        
        context = AgentContext(session_id="test_session")
        state = AgentState(
            state=AgentExecutionState.IDLE,
            context=context,
            data={
                "action": "slow_action",
                "delay": 1.0  # Longer than timeout
            }
        )
        
        result_state = await node.execute(state, context)
        
        assert result_state.state == AgentExecutionState.FAILED
        assert "error" in result_state.data
        assert "timeout" in result_state.data["error"]
    
    async def test_action_node_execute_with_retry(self):
        """Test action node with retry mechanism."""
        node = ActionNode()
        await node.initialize({
            "available_actions": ["flaky_action"],
            "retry_count": 2
        })
        
        context = AgentContext(session_id="test_session")
        state = AgentState(
            state=AgentExecutionState.IDLE,
            context=context,
            data={
                "action": "flaky_action",
                "fail_count": 1  # Will fail once then succeed
            }
        )
        
        result_state = await node.execute(state, context)
        
        assert result_state.state == AgentExecutionState.COMPLETED
        assert "retry_count" in result_state.data
        assert result_state.data["retry_count"] == 1
    
    async def test_action_node_health_check(self):
        """Test action node health check."""
        node = ActionNode()
        await node.initialize({"available_actions": ["test"]})
        
        health = await node.health_check()
        assert health is True
    
    async def test_action_node_get_info(self):
        """Test getting action node information."""
        node = ActionNode()
        await node.initialize({
            "available_actions": ["search", "calculate"],
            "timeout": 30.0
        })
        
        info = node.get_node_info()
        
        assert "type" in info
        assert info["type"] == "ActionNode"
        assert "available_actions" in info
        assert info["available_actions"] == ["search", "calculate"]
        assert "timeout" in info
        assert info["timeout"] == 30.0


class TestAgentNodeIntegration:
    """Test integration between different agent nodes."""
    
    async def test_reasoning_to_decision_flow(self):
        """Test flow from reasoning node to decision node."""
        reasoning_node = ReasoningNode()
        decision_node = DecisionNode()
        
        await reasoning_node.initialize({"model": "test-model"})
        await decision_node.initialize({"threshold": 0.7})
        
        context = AgentContext(session_id="test_session")
        initial_state = AgentState(
            state=AgentExecutionState.IDLE,
            context=context,
            data={"query": "Should we implement feature X?"}
        )
        
        # Execute reasoning first
        reasoning_state = await reasoning_node.execute(initial_state, context)
        assert reasoning_state.state == AgentExecutionState.COMPLETED
        assert "reasoning" in reasoning_state.data
        
        # Then make decision based on reasoning
        decision_state = await decision_node.execute(reasoning_state, context)
        assert decision_state.state == AgentExecutionState.COMPLETED
        assert "decision" in decision_state.data
    
    async def test_decision_to_action_flow(self):
        """Test flow from decision node to action node."""
        decision_node = DecisionNode()
        action_node = ActionNode()
        
        await decision_node.initialize({"threshold": 0.7})
        await action_node.initialize({"available_actions": ["search", "calculate"]})
        
        context = AgentContext(session_id="test_session")
        initial_state = AgentState(
            state=AgentExecutionState.IDLE,
            context=context,
            data={
                "proposal": "Search for information about AI",
                "confidence": 0.9
            }
        )
        
        # Make decision
        decision_state = await decision_node.execute(initial_state, context)
        assert decision_state.state == AgentExecutionState.COMPLETED
        
        # Execute action if approved
        if decision_state.data["decision"] == "approved":
            action_state = await action_node.execute(decision_state, context)
            assert action_state.state == AgentExecutionState.COMPLETED
            assert "action_result" in action_state.data 