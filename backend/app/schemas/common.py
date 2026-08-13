"""Shared / common Pydantic schemas."""

from __future__ import annotations

from typing import Generic, List, Optional, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response wrapper."""

    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int


class MessageResponse(BaseModel):
    """Simple message response."""

    message: str
    success: bool = True


class HealthResponse(BaseModel):
    """API health check response."""

    status: str
    version: str
    environment: str
    database: str
