"""
RAG Pipeline API Endpoints

Provides REST API endpoints for the RAG pipeline:
User Input → RAG → Rerank → LLM → Agent Response
"""

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import logging

from src.orchestration.rag_pipeline import RAGPipelineOrchestrator
from src.api.auth import get_current_user

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/rag", tags=["RAG Pipeline"])

# Pydantic models
class RAGQueryRequest(BaseModel):
    """Request model for RAG pipeline queries"""
    query: str = Field(..., description="User query/question", min_length=1, max_length=2000)
    user_id: str = Field(..., description="Unique user identifier")
    session_id: Optional[str] = Field(None, description="Optional session identifier")
    conversation_id: Optional[str] = Field(None, description="Optional conversation identifier")
    include_metrics: bool = Field(True, description="Include pipeline metrics in response")
    include_results: bool = Field(False, description="Include search and reranked results in response")

class RAGQueryResponse(BaseModel):
    """Response model for RAG pipeline queries"""
    status: str = Field(..., description="Response status (success/error)")
    user_input: str = Field(..., description="Original user input")
    agent_response: str = Field(..., description="Generated agent response")
    conversation_id: Optional[str] = Field(None, description="Conversation identifier")
    timestamp: str = Field(..., description="Response timestamp")
    pipeline_metrics: Optional[Dict[str, Any]] = Field(None, description="Pipeline performance metrics")
    search_results: Optional[list] = Field(None, description="Search results")
    reranked_results: Optional[list] = Field(None, description="Reranked results")
    error: Optional[str] = Field(None, description="Error message if status is error")

class RAGHealthResponse(BaseModel):
    """Response model for RAG pipeline health check"""
    status: str = Field(..., description="Overall health status")
    components: Dict[str, Dict[str, Any]] = Field(..., description="Component health status")
    timestamp: str = Field(..., description="Health check timestamp")
    error: Optional[str] = Field(None, description="Error message if unhealthy")

# Global RAG pipeline instance (will be initialized in app startup)
rag_pipeline: Optional[RAGPipelineOrchestrator] = None

def get_rag_pipeline() -> RAGPipelineOrchestrator:
    """Get the RAG pipeline instance"""
    if rag_pipeline is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="RAG pipeline not initialized"
        )
    return rag_pipeline

@router.post("/query", response_model=RAGQueryResponse)
async def process_rag_query(
    request: RAGQueryRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    pipeline: RAGPipelineOrchestrator = Depends(get_rag_pipeline)
):
    """
    Process a query through the complete RAG pipeline
    
    Flow: User Input → RAG → Rerank → LLM → Agent Response
    """
    
    try:
        logger.info(f"Processing RAG query for user {request.user_id}: {request.query[:100]}...")
        
        # Process query through pipeline
        response = await pipeline.process_query(
            user_input=request.query,
            user_id=request.user_id,
            session_id=request.session_id,
            conversation_id=request.conversation_id
        )
        
        # Prepare response
        rag_response = RAGQueryResponse(
            status=response["status"],
            user_input=response["user_input"],
            agent_response=response["agent_response"],
            conversation_id=response.get("conversation_id"),
            timestamp=response["timestamp"]
        )
        
        # Include optional fields based on request
        if request.include_metrics and "pipeline_metrics" in response:
            rag_response.pipeline_metrics = response["pipeline_metrics"]
        
        if request.include_results:
            rag_response.search_results = response.get("search_results", [])
            rag_response.reranked_results = response.get("reranked_results", [])
        
        if response["status"] == "error":
            rag_response.error = response.get("error")
        
        logger.info(f"RAG query completed for user {request.user_id}")
        return rag_response
        
    except Exception as e:
        logger.error(f"RAG query failed for user {request.user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"RAG pipeline error: {str(e)}"
        )

@router.get("/health", response_model=RAGHealthResponse)
async def get_rag_health(
    pipeline: RAGPipelineOrchestrator = Depends(get_rag_pipeline)
):
    """
    Get health status of the RAG pipeline and all components
    """
    
    try:
        health_status = await pipeline.health_check()
        
        return RAGHealthResponse(
            status=health_status["status"],
            components=health_status["components"],
            timestamp=health_status["timestamp"],
            error=health_status.get("error")
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Health check error: {str(e)}"
        )

@router.post("/conversation/{conversation_id}/clear")
async def clear_conversation(
    conversation_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    pipeline: RAGPipelineOrchestrator = Depends(get_rag_pipeline)
):
    """
    Clear conversation history for a specific conversation
    """
    
    try:
        # Clear conversation from memory
        memory_provider = pipeline.memory_provider
        history_key = f"conversation_{conversation_id}"
        
        # Clear the conversation
        await memory_provider.clear(history_key)
        
        logger.info(f"Cleared conversation {conversation_id} for user {current_user['user_id']}")
        
        return {
            "status": "success",
            "message": f"Conversation {conversation_id} cleared successfully",
            "conversation_id": conversation_id
        }
        
    except Exception as e:
        logger.error(f"Failed to clear conversation {conversation_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear conversation: {str(e)}"
        )

@router.get("/conversation/{conversation_id}/history")
async def get_conversation_history(
    conversation_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    pipeline: RAGPipelineOrchestrator = Depends(get_rag_pipeline)
):
    """
    Get conversation history for a specific conversation
    """
    
    try:
        # Retrieve conversation history from memory
        memory_provider = pipeline.memory_provider
        history_key = f"conversation_{conversation_id}"
        
        conversation_history = await memory_provider.retrieve(history_key)
        
        return {
            "status": "success",
            "conversation_id": conversation_id,
            "history": conversation_history,
            "count": len(conversation_history) if conversation_history else 0
        }
        
    except Exception as e:
        logger.error(f"Failed to get conversation history {conversation_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get conversation history: {str(e)}"
        )

@router.post("/query/batch")
async def process_batch_queries(
    requests: list[RAGQueryRequest],
    current_user: Dict[str, Any] = Depends(get_current_user),
    pipeline: RAGPipelineOrchestrator = Depends(get_rag_pipeline)
):
    """
    Process multiple queries through the RAG pipeline in batch
    """
    
    try:
        logger.info(f"Processing batch of {len(requests)} queries for user {current_user['user_id']}")
        
        responses = []
        for request in requests:
            response = await pipeline.process_query(
                user_input=request.query,
                user_id=request.user_id,
                session_id=request.session_id,
                conversation_id=request.conversation_id
            )
            
            # Create response object
            rag_response = RAGQueryResponse(
                status=response["status"],
                user_input=response["user_input"],
                agent_response=response["agent_response"],
                conversation_id=response.get("conversation_id"),
                timestamp=response["timestamp"]
            )
            
            if request.include_metrics and "pipeline_metrics" in response:
                rag_response.pipeline_metrics = response["pipeline_metrics"]
            
            if request.include_results:
                rag_response.search_results = response.get("search_results", [])
                rag_response.reranked_results = response.get("reranked_results", [])
            
            if response["status"] == "error":
                rag_response.error = response.get("error")
            
            responses.append(rag_response)
        
        logger.info(f"Batch processing completed for user {current_user['user_id']}")
        
        return {
            "status": "success",
            "responses": responses,
            "total_queries": len(requests),
            "successful_queries": len([r for r in responses if r.status == "success"]),
            "failed_queries": len([r for r in responses if r.status == "error"])
        }
        
    except Exception as e:
        logger.error(f"Batch query processing failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch processing error: {str(e)}"
        )

# WebSocket endpoint for real-time RAG queries
from fastapi import WebSocket, WebSocketDisconnect

@router.websocket("/ws/{user_id}")
async def rag_websocket(
    websocket: WebSocket,
    user_id: str,
    pipeline: RAGPipelineOrchestrator = Depends(get_rag_pipeline)
):
    """
    WebSocket endpoint for real-time RAG queries
    """
    
    await websocket.accept()
    logger.info(f"WebSocket connection established for user {user_id}")
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            
            # Extract query data
            query = data.get("query")
            session_id = data.get("session_id")
            conversation_id = data.get("conversation_id")
            
            if not query:
                await websocket.send_json({
                    "status": "error",
                    "error": "Query is required"
                })
                continue
            
            # Process query through pipeline
            response = await pipeline.process_query(
                user_input=query,
                user_id=user_id,
                session_id=session_id,
                conversation_id=conversation_id
            )
            
            # Send response back to client
            await websocket.send_json({
                "status": response["status"],
                "user_input": response["user_input"],
                "agent_response": response["agent_response"],
                "conversation_id": response.get("conversation_id"),
                "timestamp": response["timestamp"],
                "pipeline_metrics": response.get("pipeline_metrics"),
                "error": response.get("error")
            })
            
    except WebSocketDisconnect:
        logger.info(f"WebSocket connection closed for user {user_id}")
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {str(e)}")
        try:
            await websocket.send_json({
                "status": "error",
                "error": str(e)
            })
        except:
            pass 