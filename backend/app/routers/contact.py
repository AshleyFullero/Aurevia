"""
Contact Router
──────────────
Endpoints:
  POST /api/v1/contact   — Submit a contact / demo-request form
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.contact import ContactSubmission

router = APIRouter(prefix="/contact", tags=["Contact"])


# ── Schemas ───────────────────────────────────────────────────────────────────

class ContactCreate(BaseModel):
    """Request body for submitting a contact or demo-request form."""
    name: str = Field(..., min_length=1, max_length=200, description="Full name")
    email: str = Field(..., description="Email address")
    company: str | None = Field(None, max_length=200, description="Company name (optional)")
    message: str = Field(..., min_length=5, max_length=5000, description="Message body")
    source: str = Field("website", max_length=100, description="Form source identifier")
    page_url: str | None = Field(None, max_length=500, description="Page URL where the form was submitted")

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        v = v.strip().lower()
        if "@" not in v or "." not in v.split("@")[-1]:
            raise ValueError("Invalid email address")
        return v

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        return v.strip()


class ContactResponse(BaseModel):
    """Response after submitting a contact form."""
    success: bool
    message: str
    id: int


# ── Endpoint ──────────────────────────────────────────────────────────────────

@router.post(
    "",
    response_model=ContactResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit contact or demo-request form",
    description=(
        "Accepts a name, email, optional company, and message. "
        "Stores the submission in the database and returns a confirmation. "
        "Used by the landing page contact and demo-request forms."
    ),
)
async def submit_contact(
    payload: ContactCreate,
    db: AsyncSession = Depends(get_db),
):
    """Save a contact form submission."""
    submission = ContactSubmission(
        name=payload.name,
        email=payload.email,
        company=payload.company,
        message=payload.message,
        source=payload.source,
        page_url=payload.page_url,
    )
    db.add(submission)
    await db.commit()
    await db.refresh(submission)

    return ContactResponse(
        success=True,
        message="Thanks for reaching out! We'll get back to you within 24 hours.",
        id=submission.id,
    )
