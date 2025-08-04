"""
Main FastAPI Application Entry Point

This module creates and exports the FastAPI application for uvicorn.
"""

from src.api.main import create_app

# Create the FastAPI application
app = create_app()

# Export the app for uvicorn
__all__ = ["app"] 