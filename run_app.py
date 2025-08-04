#!/usr/bin/env python3
"""
Simple script to run the Agentic RAG FastAPI application locally
"""

import uvicorn
import os
import sys

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

if __name__ == "__main__":
    print("🚀 Starting Agentic RAG System...")
    print("📊 Services:")
    print("   - PostgreSQL: localhost:5433")
    print("   - Redis: localhost:6380")
    print("   - Qdrant: localhost:6333")
    print("   - FastAPI: localhost:8000")
    print("   - API Docs: http://localhost:8000/docs")
    print("   - Health Check: http://localhost:8000/health")
    print()
    
    # Set environment variables for local development
    os.environ.setdefault("APP_ENV", "development")
    os.environ.setdefault("LOG_LEVEL", "INFO")
    os.environ.setdefault("POSTGRES_HOST", "localhost")
    os.environ.setdefault("POSTGRES_PORT", "5433")
    os.environ.setdefault("REDIS_HOST", "localhost")
    os.environ.setdefault("REDIS_PORT", "6380")
    os.environ.setdefault("QDRANT_URL", "http://localhost:6333")
    
    # Run the FastAPI application
    uvicorn.run(
        "main:app",  # Updated to use the correct module path
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 