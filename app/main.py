"""
FastAPI application entry point for the CCA AI Assistant.
Document-based AI assistant with RAG and citations.
"""

import os
from typing import Optional
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.config import config
from app.rag import RAGPipeline
from app.database import Database
from app.models import (
    QuestionRequest,
    QuestionResponse,
    DocumentUploadResponse,
    HealthResponse
)

# ============================================
# Initialize FastAPI App
# ============================================
app = FastAPI(
    title=config.APP_NAME,
    version="0.1.0",
    description="Document-based AI assistant with RAG and citations",
    debug=config.DEBUG,
)

# ============================================
# CORS Configuration
# ============================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development - restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================
# Initialize Components
# ============================================
db = Database()
rag_pipeline = None  # Lazy initialization


def get_rag_pipeline():
    """Get or initialize the RAG pipeline."""
    global rag_pipeline
    if rag_pipeline is None:
        rag_pipeline = RAGPipeline(
            GEMINI_API_KEY=config.GEMINI_API_KEY,
            model=config.GEMINI_MODEL,
            embedding_model=config.GEMINI_EMBEDDING_MODEL,
            chunk_size=config.CHUNK_SIZE,
            chunk_overlap=config.CHUNK_OVERLAP,
        )
    return rag_pipeline


# ============================================
# Health Check Endpoints
# ============================================

@app.get("/", response_model=HealthResponse)
async def root():
    """Root endpoint - API health check."""
    return HealthResponse(
        status="healthy",
        app_name=config.APP_NAME,
        version="0.1.0",
        environment="development" if config.DEBUG else "production",
    )


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "database": "connected" if db.is_connected() else "disconnected",
        "openai": "configured" if config.GEMINI_API_KEY else "not configured",
    }


# ============================================
# Document Management Endpoints
# ============================================

@app.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
):
    """
    Upload and process a document into the knowledge base.
    """
    # Validate file extension
    if not config.is_allowed_file(file.filename):
        raise HTTPException(
            status_code=400,
            detail=f"File type not allowed. Allowed: {config.ALLOWED_EXTENSIONS}"
        )
    
    # Check file size
    content = await file.read()
    file_size = len(content)
    
    if file_size > config.MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Max size: {config.MAX_UPLOAD_SIZE} bytes"
        )
    
    # Save file
    file_path = os.path.join("data", file.filename)
    os.makedirs("data", exist_ok=True)
    
    with open(file_path, "wb") as f:
        f.write(content)
    
    # Process document with RAG pipeline
    try:
        rag = get_rag_pipeline()
        result = rag.ingest_document(file_path)
        
        return DocumentUploadResponse(
            success=True,
            filename=file.filename,
            file_path=file_path,
            file_size=file_size,
            message=f"Document '{file.filename}' processed successfully",
            chunks_created=result.get("chunks_created", 0),
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing document: {str(e)}"
        )


@app.get("/documents")
async def list_documents():
    """
    List all documents in the knowledge base.
    """
    try:
        documents = db.get_all_documents()
        return {
            "success": True,
            "count": len(documents),
            "documents": documents,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching documents: {str(e)}"
        )


@app.delete("/documents/{document_id}")
async def delete_document(document_id: int):
    """
    Delete a document from the knowledge base.
    """
    try:
        success = db.delete_document(document_id)
        if success:
            return {
                "success": True,
                "message": f"Document {document_id} deleted successfully"
            }
        else:
            raise HTTPException(
                status_code=404,
                detail=f"Document {document_id} not found"
            )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting document: {str(e)}"
        )


# ============================================
# Question Answering Endpoints
# ============================================

@app.post("/ask", response_model=QuestionResponse)
async def ask_question(request: QuestionRequest):
    """
    Ask a question and get a grounded answer with citations.
    """
    try:
        # Validate that we have documents
        doc_count = db.get_document_count()
        if doc_count == 0:
            return QuestionResponse(
                answer="No documents have been uploaded yet. Please upload some documents first.",
                citations=[],
                confidence_score=0.0,
                is_supported=False,
                question=request.question,
                message="Knowledge base is empty",
            )
        
        # Get RAG pipeline and answer
        rag = get_rag_pipeline()
        result = rag.answer_question(
            question=request.question,
            top_k=request.top_k or config.TOP_K_RETRIEVAL,
        )
        
        return QuestionResponse(
            answer=result.get("answer", ""),
            citations=result.get("citations", []),
            confidence_score=result.get("confidence_score", 0.0),
            is_supported=result.get("is_supported", False),
            question=request.question,
            message="Answer generated successfully",
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error answering question: {str(e)}"
        )


# ============================================
# Chat History
# ============================================

@app.get("/history")
async def get_chat_history(limit: Optional[int] = 50):
    """
    Get chat history.
    """
    try:
        history = db.get_chat_history(limit)
        return {
            "success": True,
            "count": len(history),
            "history": history,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching chat history: {str(e)}"
        )


# ============================================
# Error Handlers
# ============================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": exc.detail,
            "status_code": exc.status_code,
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    if config.DEBUG:
        import traceback
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(exc),
                "traceback": traceback.format_exc(),
            }
        )
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "An internal error occurred",
        }
    )


# ============================================
# Startup/Shutdown Events
# ============================================

@app.on_event("startup")
async def startup_event():
    """Run on application startup."""
    print(f"🚀 Starting {config.APP_NAME}...")
    print(f"📊 Database: {config.DATABASE_URL}")
    print(f"🔑 GEMINI_API_KEY: {'✅ Configured' if config.GEMINI_API_KEY else '❌ Not configured'}")
    print(f"🐛 Debug Mode: {config.DEBUG}")
    
    # Validate configuration
    try:
        config.validate()
    except ValueError as e:
        print(f"⚠️ Warning: {e}")
    
    # Initialize database
    await db.initialize()
    print("✅ Database initialized")


@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown."""
    print("🛑 Shutting down...")
    await db.close()
    print("👋 Goodbye!")


# ============================================
# Quick Test (if run directly)
# ============================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=config.DEBUG,
    )