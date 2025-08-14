"""LangGraph-native Agent Workflows.

Native LangGraph workflow implementations that replace custom workflow definitions.
"""

from typing import Dict, Any, List, Optional, Annotated
from datetime import datetime

from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.tools import BaseTool

from src.interfaces.agent_interface import (
    AgentState, AgentContext, AgentExecutionState, ToolResult
)
from src.agents.langchain_nodes import (
    LangChainToolRegistry, LangChainReasoningTool, LangChainDecisionTool, LangChainActionTool
)
from src.agents.tool_registry import ToolRegistry


class LangGraphState(Dict):
    """LangGraph state that extends our AgentState."""
    messages: Annotated[List[BaseMessage], add_messages]
    agent_state: AgentState
    context: AgentContext
    tools_used: List[str]
    reasoning_steps: List[Dict[str, Any]]
    final_answer: Optional[str]


class LangGraphRAGWorkflow:
    """LangGraph implementation of RAG workflow."""
    
    def __init__(self, tools: Optional[List[BaseTool]] = None):
        self.tools = tools or []
        self.graph: Optional[StateGraph] = None
        self._initialized = False
    
    def create_workflow(self) -> StateGraph:
        """Create the LangGraph workflow."""
        # Define the state schema
        workflow = StateGraph(LangGraphState)
        
        # Add nodes
        workflow.add_node("analyze_query", self._analyze_query)
        workflow.add_node("search_documents", self._search_documents)
        workflow.add_node("rerank_results", self._rerank_results)
        workflow.add_node("generate_answer", self._generate_answer)
        workflow.add_node("validate_answer", self._validate_answer)
        
        # Define the flow
        workflow.set_entry_point("analyze_query")
        workflow.add_edge("analyze_query", "search_documents")
        workflow.add_edge("search_documents", "rerank_results")
        workflow.add_edge("rerank_results", "generate_answer")
        workflow.add_edge("generate_answer", "validate_answer")
        workflow.add_edge("validate_answer", END)
        
        self.graph = workflow
        return workflow
    
    async def _analyze_query(self, state: LangGraphState) -> LangGraphState:
        """Analyze the user query to understand intent."""
        messages = state.get("messages", [])
        last_message = messages[-1] if messages else None
        
        if last_message:
            query = last_message.content
            state["agent_state"].data["analyzed_query"] = {
                "original": query,
                "intent": "search",  # Simple intent detection
                "entities": [],  # Could extract entities here
                "complexity": "medium"
            }
            
            state["reasoning_steps"].append({
                "step": "analyze_query",
                "timestamp": datetime.now().isoformat(),
                "data": state["agent_state"].data["analyzed_query"]
            })
        
        return state
    
    async def _search_documents(self, state: LangGraphState) -> LangGraphState:
        """Search for relevant documents."""
        analyzed_query = state["agent_state"].data.get("analyzed_query", {})
        query = analyzed_query.get("original", "")
        
        # Mock document search - in real implementation, this would use vector search
        search_results = [
            {"content": "Document 1 about the query", "score": 0.9, "source": "doc1.txt"},
            {"content": "Document 2 related to the topic", "score": 0.8, "source": "doc2.txt"},
            {"content": "Document 3 with relevant information", "score": 0.7, "source": "doc3.txt"}
        ]
        
        state["agent_state"].data["search_results"] = search_results
        state["tools_used"].append("document_search")
        
        state["reasoning_steps"].append({
            "step": "search_documents",
            "timestamp": datetime.now().isoformat(),
            "data": {"results_count": len(search_results), "query": query}
        })
        
        return state
    
    async def _rerank_results(self, state: LangGraphState) -> LangGraphState:
        """Rerank search results for better relevance."""
        search_results = state["agent_state"].data.get("search_results", [])
        
        # Mock reranking - sort by score (already sorted in this case)
        reranked_results = sorted(search_results, key=lambda x: x["score"], reverse=True)
        
        state["agent_state"].data["reranked_results"] = reranked_results
        state["tools_used"].append("reranker")
        
        state["reasoning_steps"].append({
            "step": "rerank_results",
            "timestamp": datetime.now().isoformat(),
            "data": {"reranked_count": len(reranked_results)}
        })
        
        return state
    
    async def _generate_answer(self, state: LangGraphState) -> LangGraphState:
        """Generate answer based on retrieved documents."""
        reranked_results = state["agent_state"].data.get("reranked_results", [])
        analyzed_query = state["agent_state"].data.get("analyzed_query", {})
        query = analyzed_query.get("original", "")
        
        # Create context from top documents
        context = "\n\n".join([doc["content"] for doc in reranked_results[:3]])
        
        # Mock answer generation - in real implementation, this would use LLM
        answer = f"Based on the retrieved documents, here's the answer to '{query}': {context[:200]}..."
        
        state["agent_state"].data["generated_answer"] = answer
        state["final_answer"] = answer
        state["tools_used"].append("llm_generator")
        
        # Add AI message to conversation
        state["messages"].append(AIMessage(content=answer))
        
        state["reasoning_steps"].append({
            "step": "generate_answer",
            "timestamp": datetime.now().isoformat(),
            "data": {"answer_length": len(answer), "context_docs": len(reranked_results[:3])}
        })
        
        return state
    
    async def _validate_answer(self, state: LangGraphState) -> LangGraphState:
        """Validate the generated answer quality."""
        answer = state.get("final_answer", "")
        
        # Simple validation - check if answer is not empty and has reasonable length
        is_valid = len(answer) > 10 and "error" not in answer.lower()
        
        state["agent_state"].data["answer_validation"] = {
            "is_valid": is_valid,
            "confidence": 0.8 if is_valid else 0.2,
            "validation_criteria": ["length_check", "error_check"]
        }
        
        state["reasoning_steps"].append({
            "step": "validate_answer",
            "timestamp": datetime.now().isoformat(),
            "data": state["agent_state"].data["answer_validation"]
        })
        
        return state
    
    def compile(self):
        """Compile the workflow."""
        if not self.graph:
            self.create_workflow()
        return self.graph.compile()


class LangGraphToolUsageWorkflow:
    """LangGraph implementation of tool usage workflow."""
    
    def __init__(self, tools: List[BaseTool]):
        self.tools = tools
        self.graph: Optional[StateGraph] = None
    
    def create_workflow(self) -> StateGraph:
        """Create the LangGraph workflow for tool usage."""
        workflow = StateGraph(LangGraphState)
        
        # Add nodes
        workflow.add_node("analyze_request", self._analyze_request)
        workflow.add_node("select_tools", self._select_tools)
        workflow.add_node("execute_tools", self._execute_tools)
        workflow.add_node("process_results", self._process_results)
        workflow.add_node("format_response", self._format_response)
        
        # Define the flow
        workflow.set_entry_point("analyze_request")
        workflow.add_edge("analyze_request", "select_tools")
        workflow.add_edge("select_tools", "execute_tools")
        workflow.add_edge("execute_tools", "process_results")
        workflow.add_edge("process_results", "format_response")
        workflow.add_edge("format_response", END)
        
        self.graph = workflow
        return workflow
    
    async def _analyze_request(self, state: LangGraphState) -> LangGraphState:
        """Analyze the request to understand what tools are needed."""
        messages = state.get("messages", [])
        last_message = messages[-1] if messages else None
        
        if last_message:
            query = last_message.content
            
            # Simple analysis to determine tool requirements
            tool_requirements = []
            if "price" in query.lower():
                tool_requirements.append("items_price")
            if "quantity" in query.lower():
                tool_requirements.append("items_quantity")
            if "search" in query.lower():
                tool_requirements.append("search")
            if "calculate" in query.lower():
                tool_requirements.append("calculate")
            
            state["agent_state"].data["tool_requirements"] = tool_requirements
            state["agent_state"].data["original_query"] = query
            
            state["reasoning_steps"].append({
                "step": "analyze_request",
                "timestamp": datetime.now().isoformat(),
                "data": {"query": query, "required_tools": tool_requirements}
            })
        
        return state
    
    async def _select_tools(self, state: LangGraphState) -> LangGraphState:
        """Select appropriate tools based on analysis."""
        tool_requirements = state["agent_state"].data.get("tool_requirements", [])
        
        # Match tool requirements to available tools
        selected_tools = []
        for tool in self.tools:
            # Check if any requirement matches the tool name
            for req in tool_requirements:
                if req.lower() in tool.name.lower() or tool.name.lower().endswith(req.lower()):
                    selected_tools.append(tool.name)
                    break
        
        # If no specific tools match, try to find any available tools
        if not selected_tools and self.tools:
            # For price queries, look for price tools
            if any("price" in req for req in tool_requirements):
                price_tools = [t.name for t in self.tools if "price" in t.name.lower()]
                selected_tools.extend(price_tools)
            
            # For quantity queries, look for quantity tools  
            if any("quantity" in req for req in tool_requirements):
                quantity_tools = [t.name for t in self.tools if "quantity" in t.name.lower()]
                selected_tools.extend(quantity_tools)
        
        # If still no tools, select all available tools as fallback
        if not selected_tools and self.tools:
            selected_tools = [tool.name for tool in self.tools[:2]]  # Limit to first 2 tools
        
        state["agent_state"].data["selected_tools"] = selected_tools
        
        state["reasoning_steps"].append({
            "step": "select_tools",
            "timestamp": datetime.now().isoformat(),
            "data": {"selected_tools": selected_tools}
        })
        
        return state
    
    async def _execute_tools(self, state: LangGraphState) -> LangGraphState:
        """Execute the selected tools."""
        selected_tools = state["agent_state"].data.get("selected_tools", [])
        query = state["agent_state"].data.get("original_query", "")
        
        tool_results = []
        
        for tool_name in selected_tools:
            # Find the tool by name
            tool = next((t for t in self.tools if t.name == tool_name), None)
            if tool:
                try:
                    result = await tool._arun(query)
                    tool_results.append({
                        "tool": tool_name,
                        "result": result,
                        "success": True,
                        "error": None
                    })
                    state["tools_used"].append(tool_name)
                except Exception as e:
                    tool_results.append({
                        "tool": tool_name,
                        "result": None,
                        "success": False,
                        "error": str(e)
                    })
        
        state["agent_state"].data["tool_results"] = tool_results
        
        state["reasoning_steps"].append({
            "step": "execute_tools",
            "timestamp": datetime.now().isoformat(),
            "data": {"tools_executed": len(tool_results), "successful": len([r for r in tool_results if r["success"]])}
        })
        
        return state
    
    async def _process_results(self, state: LangGraphState) -> LangGraphState:
        """Process and combine tool results."""
        tool_results = state["agent_state"].data.get("tool_results", [])
        
        # Combine successful results
        successful_results = [r for r in tool_results if r["success"]]
        failed_results = [r for r in tool_results if not r["success"]]
        
        processed_data = {
            "successful_tools": len(successful_results),
            "failed_tools": len(failed_results),
            "combined_results": [r["result"] for r in successful_results],
            "errors": [r["error"] for r in failed_results if r["error"]]
        }
        
        state["agent_state"].data["processed_results"] = processed_data
        
        state["reasoning_steps"].append({
            "step": "process_results",
            "timestamp": datetime.now().isoformat(),
            "data": processed_data
        })
        
        return state
    
    async def _format_response(self, state: LangGraphState) -> LangGraphState:
        """Format the final response."""
        processed_results = state["agent_state"].data.get("processed_results", {})
        query = state["agent_state"].data.get("original_query", "")
        
        combined_results = processed_results.get("combined_results", [])
        errors = processed_results.get("errors", [])
        
        if combined_results:
            response = f"Based on your query '{query}', here are the results:\n\n"
            for i, result in enumerate(combined_results, 1):
                response += f"{i}. {result}\n"
            
            if errors:
                response += f"\nNote: Some tools encountered errors: {'; '.join(errors)}"
        else:
            response = f"I couldn't find specific results for your query '{query}'. "
            if errors:
                response += f"Errors encountered: {'; '.join(errors)}"
        
        state["final_answer"] = response
        state["messages"].append(AIMessage(content=response))
        
        state["reasoning_steps"].append({
            "step": "format_response",
            "timestamp": datetime.now().isoformat(),
            "data": {"response_length": len(response)}
        })
        
        return state
    
    def compile(self):
        """Compile the workflow."""
        if not self.graph:
            self.create_workflow()
        return self.graph.compile()


class LangGraphConversationWorkflow:
    """LangGraph implementation of conversation workflow."""
    
    def __init__(self, tools: Optional[List[BaseTool]] = None):
        self.tools = tools or []
        self.graph: Optional[StateGraph] = None
    
    def create_workflow(self) -> StateGraph:
        """Create the LangGraph workflow for conversation."""
        workflow = StateGraph(LangGraphState)
        
        # Add nodes
        workflow.add_node("load_context", self._load_context)
        workflow.add_node("analyze_intent", self._analyze_intent)
        workflow.add_node("generate_response", self._generate_response)
        workflow.add_node("save_context", self._save_context)
        
        # Define the flow
        workflow.set_entry_point("load_context")
        workflow.add_edge("load_context", "analyze_intent")
        workflow.add_edge("analyze_intent", "generate_response")
        workflow.add_edge("generate_response", "save_context")
        workflow.add_edge("save_context", END)
        
        self.graph = workflow
        return workflow
    
    async def _load_context(self, state: LangGraphState) -> LangGraphState:
        """Load conversation context."""
        # In real implementation, this would load from memory provider
        conversation_history = state.get("messages", [])
        
        state["agent_state"].data["conversation_context"] = {
            "message_count": len(conversation_history),
            "last_topics": [],  # Would extract topics from history
            "user_preferences": {}  # Would load user preferences
        }
        
        state["reasoning_steps"].append({
            "step": "load_context",
            "timestamp": datetime.now().isoformat(),
            "data": state["agent_state"].data["conversation_context"]
        })
        
        return state
    
    async def _analyze_intent(self, state: LangGraphState) -> LangGraphState:
        """Analyze user intent from message."""
        messages = state.get("messages", [])
        last_message = messages[-1] if messages else None
        
        if last_message:
            content = last_message.content
            
            # Simple intent analysis
            intent = "general"
            if any(word in content.lower() for word in ["hello", "hi", "hey"]):
                intent = "greeting"
            elif any(word in content.lower() for word in ["bye", "goodbye", "exit"]):
                intent = "farewell"
            elif "?" in content:
                intent = "question"
            elif any(word in content.lower() for word in ["find", "search", "get", "show"]):
                intent = "search"
            
            state["agent_state"].data["intent_analysis"] = {
                "intent": intent,
                "confidence": 0.8,
                "entities": [],  # Could extract entities
                "sentiment": "neutral"  # Could analyze sentiment
            }
            
            state["reasoning_steps"].append({
                "step": "analyze_intent",
                "timestamp": datetime.now().isoformat(),
                "data": state["agent_state"].data["intent_analysis"]
            })
        
        return state
    
    async def _generate_response(self, state: LangGraphState) -> LangGraphState:
        """Generate conversational response."""
        intent_analysis = state["agent_state"].data.get("intent_analysis", {})
        intent = intent_analysis.get("intent", "general")
        
        messages = state.get("messages", [])
        last_message = messages[-1] if messages else None
        user_message = last_message.content if last_message else ""
        
        # Generate response based on intent
        if intent == "greeting":
            response = "Hello! How can I help you today?"
        elif intent == "farewell":
            response = "Goodbye! Feel free to ask if you need anything else."
        elif intent == "question" or intent == "search":
            response = f"Let me help you with that. You asked: '{user_message}'. "
            response += "I can search for information, analyze data, or help with various tasks."
        else:
            response = f"I understand you said: '{user_message}'. How can I assist you further?"
        
        state["final_answer"] = response
        state["messages"].append(AIMessage(content=response))
        
        state["reasoning_steps"].append({
            "step": "generate_response",
            "timestamp": datetime.now().isoformat(),
            "data": {"intent": intent, "response_length": len(response)}
        })
        
        return state
    
    async def _save_context(self, state: LangGraphState) -> LangGraphState:
        """Save conversation context."""
        # In real implementation, this would save to memory provider
        state["agent_state"].data["context_saved"] = {
            "timestamp": datetime.now().isoformat(),
            "message_count": len(state.get("messages", [])),
            "session_id": state.get("context", {}).session_id if state.get("context") else "unknown"
        }
        
        state["reasoning_steps"].append({
            "step": "save_context",
            "timestamp": datetime.now().isoformat(),
            "data": state["agent_state"].data["context_saved"]
        })
        
        return state
    
    def compile(self):
        """Compile the workflow."""
        if not self.graph:
            self.create_workflow()
        return self.graph.compile()


def create_default_langgraph_state(query: str, context: AgentContext) -> LangGraphState:
    """Create a default LangGraph state."""
    return LangGraphState(
        messages=[HumanMessage(content=query)],
        agent_state=AgentState(
            context=context,
            data={"query": query}
        ),
        context=context,
        tools_used=[],
        reasoning_steps=[],
        final_answer=None
    ) 