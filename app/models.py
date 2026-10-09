"""
Pydantic models for request/response validation.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class Citation(BaseModel):
    """Citation model for source references."""
    document_title: str = Field(..., description="Title of the source document")
    page: Optional[int] = Field(None, description="Page number")
    section: Optional[str] = Field(None, description="Section name")
    chunk_text: str = Field(..., description="Retrieved text chunk")
    relevance_score: Optional[float] = Field(None, description="Relevance score")


class QuestionRequest(BaseModel):
    """Question request model."""
    question: str = Field(..., description="User's question", min_length=1)
    top_k: Optional[int] = Field(3, description="Number of chunks to retrieve")


class QuestionResponse(BaseModel):
    """Question response model."""
    answer: str = Field(..., description="Generated answer")
    citations: List[Citation] = Field(default_factory=list, description="Source citations")
    confidence_score: float = Field(0.0, description="Confidence score (0-1)")
    is_supported: bool = Field(False, description="Whether answer is supported by documents")
    question: str = Field(..., description="Original question")
    message: Optional[str] = Field(None, description="Additional message")


class DocumentUploadResponse(BaseModel):
    """Document upload response model."""
    success: bool
    filename: str
    file_path: str
    file_size: int
    message: str
    chunks_created: int = 0


class DocumentInfo(BaseModel):
    """Document information model."""
    id: int
    title: str
    source_type: str
    file_path: str
    created_at: datetime
    chunk_count: Optional[int] = 0


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str
    app_name: str
    version: str
    environment: str


class ChatMessage(BaseModel):
    """Chat message model."""
    id: int
    question: str
    answer: str
    citations: List[Dict[str, Any]]
    created_at: datetime