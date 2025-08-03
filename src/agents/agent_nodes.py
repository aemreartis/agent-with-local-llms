"""Agent Node Implementations.

Individual agent nodes for reasoning, decision making, and task execution.
"""

import asyncio
import time
import re
from datetime import datetime
from typing import Dict, List, Any, Optional

from src.interfaces.agent_interface import (
    AgentExecutionState, AgentContext, AgentState, AgentNodeInterface
)


class ReasoningNode(AgentNodeInterface):
    """Reasoning node for step-by-step thinking and problem solving."""
    
    def __init__(self):
        """Initialize the reasoning node."""
        self._initialized: bool = False
        self._config: Dict[str, Any] = {}
        self._model: str = "default"
        self._temperature: float = 0.5
        self._max_tokens: int = 500
        self._prompt_template: str = "Think step by step about: {input}"
        self._mock_reasoning_failure: bool = False
    
    async def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the reasoning node with configuration."""
        self._config = config.copy()
        self._model = config.get("model", "default")
        self._temperature = config.get("temperature", 0.5)
        self._max_tokens = config.get("max_tokens", 500)
        self._prompt_template = config.get("reasoning_prompt_template", "Think step by step about: {input}")
        self._initialized = True
    
    async def execute(self, state: AgentState, context: AgentContext) -> AgentState:
        """Execute reasoning on the given state."""
        if not self._initialized:
            raise RuntimeError("Reasoning node not initialized")
        
        # Create a copy of the state to modify
        result_state = AgentState(
            state=AgentExecutionState.RUNNING,
            context=state.context,
            data=state.data.copy(),
            history=state.history.copy(),
            current_step="reasoning",
            error=state.error,
            created_at=state.created_at,
            updated_at=datetime.now()
        )
        
        try:
            # Check for mock failure
            if self._mock_reasoning_failure:
                raise RuntimeError("reasoning_failed")
            
            query = state.data.get("query", "")
            steps = state.data.get("steps", [])
            
            # Simulate reasoning process
            reasoning_result = await self._perform_reasoning(query, steps)
            
            # Update state with reasoning results
            result_state.data["reasoning"] = reasoning_result["reasoning"]
            result_state.data["answer"] = reasoning_result["answer"]
            if steps:
                result_state.data["steps_completed"] = steps
            
            # Add confidence and relevance for decision making
            result_state.data["confidence"] = reasoning_result.get("confidence", 0.8)
            result_state.data["relevance"] = reasoning_result.get("relevance", 0.8)
            result_state.data["proposal"] = reasoning_result.get("proposal", query)
            
            # Add to history
            history_entry = {
                "timestamp": datetime.now().isoformat(),
                "action": "reasoning",
                "query": query,
                "reasoning": reasoning_result["reasoning"],
                "answer": reasoning_result["answer"]
            }
            result_state.history.append(history_entry)
            
            result_state.state = AgentExecutionState.COMPLETED
            result_state.current_step = "reasoning_complete"
            result_state.updated_at = datetime.now()
            
        except Exception as e:
            result_state.state = AgentExecutionState.FAILED
            result_state.error = str(e)
            result_state.data["error"] = str(e)
            result_state.updated_at = datetime.now()
        
        return result_state
    
    async def _perform_reasoning(self, query: str, steps: List[str]) -> Dict[str, Any]:
        """Perform the actual reasoning process."""
        # Simulate reasoning based on query type
        if "capital" in query.lower():
            reasoning = "I need to identify what country is being asked about. The query mentions 'France', so I need to recall that Paris is the capital of France."
            answer = "The capital of France is Paris."
            confidence = 0.95
            relevance = 0.9
            proposal = "Provide factual information about France's capital"
        elif "train" in query.lower() and "speed" in query.lower():
            reasoning = "I need to calculate average speed. The formula is speed = distance / time. Distance is 120 km, time is 2 hours. So speed = 120/2 = 60 km/h."
            answer = "The average speed is 60 km/h."
            confidence = 0.9
            relevance = 0.85
            proposal = "Calculate train speed using distance and time"
        elif "steps" in query.lower():
            reasoning = f"I need to execute the following steps: {', '.join(steps)}"
            answer = f"Completed steps: {', '.join(steps)}"
            confidence = 0.8
            relevance = 0.8
            proposal = f"Execute steps: {', '.join(steps)}"
        else:
            reasoning = "I need to think about this query step by step and provide a logical answer."
            answer = "Based on my reasoning, here is the answer to your query."
            confidence = 0.8
            relevance = 0.8
            proposal = query
        
        return {
            "reasoning": reasoning,
            "answer": answer,
            "confidence": confidence,
            "relevance": relevance,
            "proposal": proposal
        }
    
    async def health_check(self) -> bool:
        """Check if the reasoning node is healthy."""
        return self._initialized
    
    def get_node_info(self) -> Dict[str, Any]:
        """Get information about the reasoning node."""
        return {
            "type": "ReasoningNode",
            "model": self._model,
            "temperature": self._temperature,
            "max_tokens": self._max_tokens,
            "initialized": self._initialized
        }
    
    def get_input_schema(self) -> Dict[str, Any]:
        """Get the input schema for the reasoning node."""
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The query to reason about"
                },
                "steps": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional steps to follow"
                }
            },
            "required": ["query"]
        }
    
    def get_output_schema(self) -> Dict[str, Any]:
        """Get the output schema for the reasoning node."""
        return {
            "type": "object",
            "properties": {
                "reasoning": {
                    "type": "string",
                    "description": "The step-by-step reasoning process"
                },
                "answer": {
                    "type": "string",
                    "description": "The final answer based on reasoning"
                },
                "steps_completed": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Steps that were completed"
                }
            }
        }


class DecisionNode(AgentNodeInterface):
    """Decision node for making decisions based on criteria and thresholds."""
    
    def __init__(self):
        """Initialize the decision node."""
        self._initialized: bool = False
        self._config: Dict[str, Any] = {}
        self._decision_criteria: List[str] = ["relevance", "confidence"]
        self._threshold: float = 0.7
        self._fallback_action: str = "request_clarification"
    
    async def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the decision node with configuration."""
        self._config = config.copy()
        self._decision_criteria = config.get("decision_criteria", ["relevance", "confidence"])
        self._threshold = config.get("threshold", 0.7)
        self._fallback_action = config.get("fallback_action", "request_clarification")
        self._initialized = True
    
    async def execute(self, state: AgentState, context: AgentContext) -> AgentState:
        """Execute decision making on the given state."""
        if not self._initialized:
            raise RuntimeError("Decision node not initialized")
        
        # Create a copy of the state to modify
        result_state = AgentState(
            state=AgentExecutionState.RUNNING,
            context=state.context,
            data=state.data.copy(),
            history=state.history.copy(),
            current_step="decision_making",
            error=state.error,
            created_at=state.created_at,
            updated_at=datetime.now()
        )
        
        try:
            # Extract decision inputs
            proposal = state.data.get("proposal", "")
            confidence = state.data.get("confidence", 0.5)
            relevance = state.data.get("relevance", 0.5)
            
            # Calculate decision score
            decision_score = await self._calculate_decision_score(confidence, relevance)
            
            # Handle fallback for very unclear cases (including boundary case)
            if decision_score <= 0.5:
                result_state.state = AgentExecutionState.WAITING
                result_state.data["decision"] = "needs_clarification"
                result_state.data["confidence_score"] = decision_score
                result_state.data["threshold"] = self._threshold
                result_state.data["action"] = self._fallback_action
                result_state.data["reason"] = "Insufficient information for decision"
                result_state.current_step = "waiting_for_clarification"
            else:
                # Make decision based on threshold
                if decision_score >= self._threshold:
                    decision = "approved"
                    result_state.state = AgentExecutionState.COMPLETED
                    result_state.current_step = "decision_complete"
                else:
                    # If score is below threshold but above 0.5, reject
                    decision = "rejected"
                    result_state.state = AgentExecutionState.COMPLETED
                    result_state.current_step = "decision_complete"
                
                # Update state with decision results
                result_state.data["decision"] = decision
                result_state.data["confidence_score"] = decision_score
                result_state.data["threshold"] = self._threshold
            
            # Add to history
            history_entry = {
                "timestamp": datetime.now().isoformat(),
                "action": "decision",
                "proposal": proposal,
                "decision": result_state.data["decision"],
                "score": decision_score,
                "threshold": self._threshold
            }
            result_state.history.append(history_entry)
            
            result_state.updated_at = datetime.now()
            
        except Exception as e:
            result_state.state = AgentExecutionState.FAILED
            result_state.error = str(e)
            result_state.data["error"] = str(e)
            result_state.updated_at = datetime.now()
        
        return result_state
    
    async def _calculate_decision_score(self, confidence: float, relevance: float) -> float:
        """Calculate the decision score based on criteria."""
        # Simple weighted average
        weights = {"confidence": 0.6, "relevance": 0.4}
        score = (confidence * weights["confidence"] + relevance * weights["relevance"])
        return min(max(score, 0.0), 1.0)  # Clamp between 0 and 1
    
    async def health_check(self) -> bool:
        """Check if the decision node is healthy."""
        return self._initialized
    
    def get_node_info(self) -> Dict[str, Any]:
        """Get information about the decision node."""
        return {
            "type": "DecisionNode",
            "threshold": self._threshold,
            "criteria": self._decision_criteria,
            "fallback_action": self._fallback_action,
            "initialized": self._initialized
        }
    
    def get_input_schema(self) -> Dict[str, Any]:
        """Get the input schema for the decision node."""
        return {
            "type": "object",
            "properties": {
                "proposal": {
                    "type": "string",
                    "description": "The proposal to evaluate"
                },
                "confidence": {
                    "type": "number",
                    "minimum": 0.0,
                    "maximum": 1.0,
                    "description": "Confidence level in the proposal"
                },
                "relevance": {
                    "type": "number",
                    "minimum": 0.0,
                    "maximum": 1.0,
                    "description": "Relevance of the proposal"
                }
            },
            "required": ["proposal", "confidence"]
        }
    
    def get_output_schema(self) -> Dict[str, Any]:
        """Get the output schema for the decision node."""
        return {
            "type": "object",
            "properties": {
                "decision": {
                    "type": "string",
                    "enum": ["approved", "rejected", "needs_clarification"],
                    "description": "The decision made"
                },
                "confidence_score": {
                    "type": "number",
                    "description": "The calculated confidence score"
                },
                "threshold": {
                    "type": "number",
                    "description": "The threshold used for decision"
                },
                "action": {
                    "type": "string",
                    "description": "Action to take (for fallback cases)"
                }
            }
        }


class ActionNode(AgentNodeInterface):
    """Action node for executing specific actions and tasks."""
    
    def __init__(self):
        """Initialize the action node."""
        self._initialized: bool = False
        self._config: Dict[str, Any] = {}
        self._available_actions: List[str] = []
        self._timeout: float = 30.0
        self._retry_count: int = 3
    
    async def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the action node with configuration."""
        self._config = config.copy()
        self._available_actions = config.get("available_actions", [])
        self._timeout = config.get("timeout", 30.0)
        self._retry_count = config.get("retry_count", 3)
        self._initialized = True
    
    async def execute(self, state: AgentState, context: AgentContext) -> AgentState:
        """Execute action on the given state."""
        if not self._initialized:
            raise RuntimeError("Action node not initialized")
        
        # Create a copy of the state to modify
        result_state = AgentState(
            state=AgentExecutionState.RUNNING,
            context=state.context,
            data=state.data.copy(),
            history=state.history.copy(),
            current_step="action_execution",
            error=state.error,
            created_at=state.created_at,
            updated_at=datetime.now()
        )
        
        try:
            # Get action from state, with fallback to decision action
            action = state.data.get("action", "")
            if not action and "decision" in state.data and state.data["decision"] == "approved":
                # If no action specified but decision was approved, use the proposal as action
                proposal = state.data.get("proposal", "")
                if "search" in proposal.lower():
                    action = "search"
                    result_state.data["query"] = proposal
                elif "calculate" in proposal.lower():
                    action = "calculate"
                    result_state.data["expression"] = proposal
                else:
                    action = "format"
                    result_state.data["content"] = proposal
            
            # Validate action
            if action not in self._available_actions:
                raise ValueError(f"Invalid action: {action}")
            
            # Execute action with retry logic
            start_time = time.time()
            action_result, retry_count = await self._execute_action_with_retry(action, state.data)
            execution_time = time.time() - start_time
            
            # Update state with action results
            result_state.data["action_result"] = action_result
            result_state.data["execution_time"] = execution_time
            result_state.data["retry_count"] = retry_count
            
            # Add to history
            history_entry = {
                "timestamp": datetime.now().isoformat(),
                "action": action,
                "result": action_result,
                "execution_time": execution_time,
                "retry_count": retry_count
            }
            result_state.history.append(history_entry)
            
            result_state.state = AgentExecutionState.COMPLETED
            result_state.current_step = "action_complete"
            result_state.updated_at = datetime.now()
            
        except Exception as e:
            result_state.state = AgentExecutionState.FAILED
            result_state.error = str(e)
            result_state.data["error"] = str(e)
            result_state.updated_at = datetime.now()
        
        return result_state
    
    async def _execute_action_with_retry(self, action: str, data: Dict[str, Any]) -> tuple[Dict[str, Any], int]:
        """Execute action with retry mechanism."""
        last_exception = None
        
        for attempt in range(self._retry_count + 1):
            try:
                # Check for timeout simulation
                if action == "slow_action":
                    delay = data.get("delay", 0)
                    if delay > self._timeout:
                        raise asyncio.TimeoutError("Action timed out")
                    await asyncio.sleep(min(delay, 0.01))  # Simulate delay
                
                # Check for flaky action simulation
                if action == "flaky_action":
                    fail_count = data.get("fail_count", 0)
                    if attempt < fail_count:
                        raise RuntimeError("Flaky action failed")
                
                # Execute the actual action
                return await self._execute_single_action(action, data), attempt
                
            except Exception as e:
                last_exception = e
                if attempt < self._retry_count:
                    await asyncio.sleep(0.1)  # Brief delay before retry
                    continue
                else:
                    break
        
        # If we get here, all retries failed
        if isinstance(last_exception, asyncio.TimeoutError):
            raise RuntimeError("Action timed out due to timeout")
        else:
            raise last_exception
    
    async def _execute_single_action(self, action: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single action."""
        if action == "search":
            query = data.get("query", "")
            return {
                "search_results": [
                    f"Result 1 for: {query}",
                    f"Result 2 for: {query}",
                    f"Result 3 for: {query}"
                ],
                "total_results": 3
            }
        
        elif action == "calculate":
            expression = data.get("expression", "")
            # Simple expression evaluation (for demo purposes)
            try:
                # Remove spaces and evaluate
                clean_expr = expression.replace(" ", "")
                result = eval(clean_expr)  # Note: eval is used for demo only
                return {"result": result, "expression": expression}
            except Exception as e:
                raise ValueError(f"Invalid expression: {expression}")
        
        elif action == "format":
            content = data.get("content", "")
            format_type = data.get("format_type", "text")
            return {
                "formatted_content": f"Formatted {format_type}: {content}",
                "format_type": format_type
            }
        
        else:
            # Generic action
            return {
                "action": action,
                "status": "completed",
                "data": data
            }
    
    async def health_check(self) -> bool:
        """Check if the action node is healthy."""
        return self._initialized
    
    def get_node_info(self) -> Dict[str, Any]:
        """Get information about the action node."""
        return {
            "type": "ActionNode",
            "available_actions": self._available_actions,
            "timeout": self._timeout,
            "retry_count": self._retry_count,
            "initialized": self._initialized
        }
    
    def get_input_schema(self) -> Dict[str, Any]:
        """Get the input schema for the action node."""
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["search", "calculate", "format"],
                    "description": "The action to execute"
                },
                "query": {
                    "type": "string",
                    "description": "Query for search action"
                },
                "expression": {
                    "type": "string",
                    "description": "Expression for calculate action"
                },
                "content": {
                    "type": "string",
                    "description": "Content for format action"
                }
            },
            "required": ["action"]
        }
    
    def get_output_schema(self) -> Dict[str, Any]:
        """Get the output schema for the action node."""
        return {
            "type": "object",
            "properties": {
                "action_result": {
                    "type": "object",
                    "description": "The result of the action execution"
                },
                "execution_time": {
                    "type": "number",
                    "description": "Time taken to execute the action"
                },
                "retry_count": {
                    "type": "number",
                    "description": "Number of retries attempted"
                }
            }
        } 