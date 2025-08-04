"""
API Data Models - Stage 7 TDD Implementation

Pydantic models for API request/response schemas.
Following TDD methodology: Models defined first, then endpoints.
"""

from pydantic import BaseModel, Field, field_validator, field_serializer
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from enum import Enum
import uuid


class HealthStatus(str, Enum):
    """Health status enumeration"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class WorkflowType(str, Enum):
    """Agent workflow types"""
    RAG = "rag"
    MULTI_STEP = "multi_step"
    TOOL_USAGE = "tool_usage"
    CONVERSATION = "conversation"


class SessionType(str, Enum):
    """Session types"""
    CONVERSATION = "conversation"
    WORKFLOW = "workflow"
    DOCUMENT_PROCESSING = "document_processing"


class ProcessingStatus(str, Enum):
    """Document processing status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class MessageRole(str, Enum):
    """Message roles in conversation"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


# Health Check Models
class HealthResponse(BaseModel):
    """Health check response model"""
    status: HealthStatus
    timestamp: datetime
    version: str = Field(default="1.0.0")
    uptime_seconds: Optional[float] = None

    @field_serializer('timestamp')
    def serialize_timestamp(self, value: datetime) -> str:
        return value.isoformat()


class ComponentHealth(BaseModel):
    """Individual component health status"""
    status: HealthStatus
    message: Optional[str] = None
    last_check: datetime
    response_time_ms: Optional[float] = None

    @field_serializer('last_check')
    def serialize_last_check(self, value: datetime) -> str:
        return value.isoformat()


class DetailedHealthResponse(BaseModel):
    """Detailed health check response"""
    overall_status: HealthStatus
    components: Dict[str, ComponentHealth]
    timestamp: datetime
    version: str = Field(default="1.0.0")

    @field_serializer('timestamp')
    def serialize_timestamp(self, value: datetime) -> str:
        return value.isoformat()


# Chat Models
class ChatMessage(BaseModel):
    """Individual chat message"""
    role: MessageRole
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)

    @field_serializer('timestamp')
    def serialize_timestamp(self, value: datetime) -> str:
        return value.isoformat()


class ChatRequest(BaseModel):
    """Chat request model"""
    message: str = Field(..., min_length=1, max_length=10000)
    session_id: str = Field(..., pattern=r"^[a-zA-Z0-9_-]+$")
    context: Optional[Dict[str, Any]] = None
    history: Optional[List[ChatMessage]] = None
    parameters: Optional[Dict[str, Any]] = None

    @field_validator('message')
    @classmethod
    def validate_message(cls, v):
        if not v.strip():
            raise ValueError('Message cannot be empty')
        return v.strip()


class ChatResponse(BaseModel):
    """Chat response model"""
    response: str
    session_id: str
    timestamp: datetime = Field(default_factory=datetime.now)
    context: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None

    @field_serializer('timestamp')
    def serialize_timestamp(self, value: datetime) -> str:
        return value.isoformat()


# Document Models
class DocumentMetadata(BaseModel):
    """Document metadata"""
    title: Optional[str] = None
    author: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    source: Optional[str] = None
    created_date: Optional[datetime] = None
    custom_fields: Optional[Dict[str, Any]] = None

    @field_serializer('created_date')
    def serialize_created_date(self, value: Optional[datetime]) -> Optional[str]:
        return value.isoformat() if value else None


class DocumentUploadRequest(BaseModel):
    """Document upload request"""
    metadata: Optional[DocumentMetadata] = None
    processing_options: Optional[Dict[str, Any]] = None


class DocumentUploadResponse(BaseModel):
    """Document upload response"""
    document_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    status: ProcessingStatus
    processing_status: str
    metadata: Optional[DocumentMetadata] = None
    estimated_completion_time: Optional[datetime] = None

    @field_serializer('estimated_completion_time')
    def serialize_estimated_completion_time(self, value: Optional[datetime]) -> Optional[str]:
        return value.isoformat() if value else None


class DocumentStatusResponse(BaseModel):
    """Document processing status response"""
    document_id: str
    status: ProcessingStatus
    processing_progress: float = Field(ge=0, le=100)
    error_message: Optional[str] = None
    completed_at: Optional[datetime] = None
    chunks_count: Optional[int] = None
    vector_count: Optional[int] = None

    @field_serializer('completed_at')
    def serialize_completed_at(self, value: Optional[datetime]) -> Optional[str]:
        return value.isoformat() if value else None


class DocumentListItem(BaseModel):
    """Document list item"""
    document_id: str
    title: Optional[str]
    status: ProcessingStatus
    uploaded_at: datetime
    processed_at: Optional[datetime] = None
    file_size: Optional[int] = None
    file_type: Optional[str] = None

    @field_serializer('uploaded_at')
    def serialize_uploaded_at(self, value: datetime) -> str:
        return value.isoformat()

    @field_serializer('processed_at')
    def serialize_processed_at(self, value: Optional[datetime]) -> Optional[str]:
        return value.isoformat() if value else None


class DocumentListResponse(BaseModel):
    """Document list response"""
    documents: List[DocumentListItem]
    total_count: int
    page: int = Field(ge=1)
    page_size: int = Field(ge=1, le=100)
    has_next: bool
    has_previous: bool


# Search Models
class SearchFilter(BaseModel):
    """Search filter model"""
    document_type: Optional[str] = None
    author: Optional[str] = None
    date_range: Optional[Dict[str, datetime]] = None
    tags: Optional[List[str]] = None
    custom_filters: Optional[Dict[str, Any]] = None

    @field_serializer('date_range')
    def serialize_date_range(self, value: Optional[Dict[str, datetime]]) -> Optional[Dict[str, str]]:
        if value is None:
            return None
        return {k: v.isoformat() for k, v in value.items()}


class SearchRequest(BaseModel):
    """Search request model"""
    query: str = Field(..., min_length=1, max_length=1000)
    filters: Optional[SearchFilter] = None
    limit: int = Field(default=10, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
    rerank: bool = Field(default=False)
    reranker: Optional[str] = Field(default="bge")
    search_strategy: Optional[str] = Field(default="hybrid")

    @field_validator('query')
    @classmethod
    def validate_query(cls, v):
        if not v.strip():
            raise ValueError('Query cannot be empty')
        return v.strip()


class SearchResult(BaseModel):
    """Individual search result"""
    document_id: str
    title: Optional[str]
    content: str
    score: float
    metadata: Optional[Dict[str, Any]] = None
    highlights: Optional[List[str]] = None


class SearchResponse(BaseModel):
    """Search response model"""
    results: List[SearchResult]
    query: str
    total_results: int
    search_time: float
    reranking_applied: bool = False
    search_strategy_used: str


# Agent Models
class AgentWorkflowRequest(BaseModel):
    """Agent workflow execution request"""
    workflow_type: WorkflowType
    query: str = Field(..., min_length=1, max_length=5000)
    session_id: str = Field(..., pattern=r"^[a-zA-Z0-9_-]+$")
    parameters: Optional[Dict[str, Any]] = None
    context: Optional[Dict[str, Any]] = None

    @field_validator('query')
    @classmethod
    def validate_query(cls, v):
        if not v.strip():
            raise ValueError('Query cannot be empty')
        return v.strip()


class AgentWorkflowResponse(BaseModel):
    """Agent workflow execution response"""
    workflow_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    status: str
    result: Optional[str] = None
    execution_time: float
    steps_completed: int = 0
    total_steps: Optional[int] = None
    error_message: Optional[str] = None


class AgentWorkflowStatus(BaseModel):
    """Agent workflow status response"""
    workflow_id: str
    status: str
    current_step: Optional[str] = None
    progress: float = Field(ge=0, le=100)
    result: Optional[str] = None
    error_message: Optional[str] = None
    started_at: datetime
    completed_at: Optional[datetime] = None

    @field_serializer('started_at')
    def serialize_started_at(self, value: datetime) -> str:
        return value.isoformat()

    @field_serializer('completed_at')
    def serialize_completed_at(self, value: Optional[datetime]) -> Optional[str]:
        return value.isoformat() if value else None


class AgentSessionRequest(BaseModel):
    """Agent session creation request"""
    session_type: SessionType
    user_id: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None


class AgentSessionResponse(BaseModel):
    """Agent session response"""
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    status: str
    session_type: SessionType
    created_at: datetime = Field(default_factory=datetime.now)
    user_id: Optional[str] = None

    @field_serializer('created_at')
    def serialize_created_at(self, value: datetime) -> str:
        return value.isoformat()


class AgentSessionDetails(BaseModel):
    """Agent session details"""
    session_id: str
    status: str
    session_type: SessionType
    created_at: datetime
    last_activity: datetime
    user_id: Optional[str] = None
    history: List[ChatMessage] = []
    metadata: Optional[Dict[str, Any]] = None

    @field_serializer('created_at')
    def serialize_created_at(self, value: datetime) -> str:
        return value.isoformat()

    @field_serializer('last_activity')
    def serialize_last_activity(self, value: datetime) -> str:
        return value.isoformat()


# Authentication Models
class LoginRequest(BaseModel):
    """Login request model"""
    username: str = Field(..., min_length=1, max_length=100)
    password: str = Field(..., min_length=1)


class LoginResponse(BaseModel):
    """Login response model"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_token: Optional[str] = None
    user_id: str
    username: str


class TokenResponse(BaseModel):
    """Token validation response"""
    valid: bool
    user_id: Optional[str] = None
    username: Optional[str] = None
    permissions: Optional[List[str]] = None


# WebSocket Models
class WebSocketMessage(BaseModel):
    """WebSocket message model"""
    type: str
    content: str
    session_id: str
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Optional[Dict[str, Any]] = None

    @field_serializer('timestamp')
    def serialize_timestamp(self, value: datetime) -> str:
        return value.isoformat()


class WebSocketResponse(BaseModel):
    """WebSocket response model"""
    type: str
    content: str
    session_id: str
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Optional[Dict[str, Any]] = None

    @field_serializer('timestamp')
    def serialize_timestamp(self, value: datetime) -> str:
        return value.isoformat()


# Error Models
class ErrorResponse(BaseModel):
    """Error response model"""
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    request_id: Optional[str] = None

    @field_serializer('timestamp')
    def serialize_timestamp(self, value: datetime) -> str:
        return value.isoformat()


class ValidationError(BaseModel):
    """Validation error model"""
    field: str
    message: str
    value: Optional[Any] = None


class ValidationErrorResponse(BaseModel):
    """Validation error response"""
    errors: List[ValidationError]
    message: str = "Validation error"
    timestamp: datetime = Field(default_factory=datetime.now)

    @field_serializer('timestamp')
    def serialize_timestamp(self, value: datetime) -> str:
        return value.isoformat()


# Metrics Models
class MetricsResponse(BaseModel):
    """Metrics response model"""
    metrics: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.now)

    @field_serializer('timestamp')
    def serialize_timestamp(self, value: datetime) -> str:
        return value.isoformat()


# Batch Processing Models
class BatchUploadRequest(BaseModel):
    """Batch upload request"""
    metadata: Optional[DocumentMetadata] = None
    processing_options: Optional[Dict[str, Any]] = None


class BatchUploadResponse(BaseModel):
    """Batch upload response"""
    batch_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    documents: List[DocumentUploadResponse]
    total_count: int
    status: ProcessingStatus
    estimated_completion_time: Optional[datetime] = None

    @field_serializer('estimated_completion_time')
    def serialize_estimated_completion_time(self, value: Optional[datetime]) -> Optional[str]:
        return value.isoformat() if value else None


class BatchStatusResponse(BaseModel):
    """Batch processing status"""
    batch_id: str
    status: ProcessingStatus
    total_documents: int
    completed_documents: int
    failed_documents: int
    processing_progress: float = Field(ge=0, le=100)
    started_at: datetime
    completed_at: Optional[datetime] = None
    error_summary: Optional[Dict[str, int]] = None

    @field_serializer('started_at')
    def serialize_started_at(self, value: datetime) -> str:
        return value.isoformat()

    @field_serializer('completed_at')
    def serialize_completed_at(self, value: Optional[datetime]) -> Optional[str]:
        return value.isoformat() if value else None 