"""
Company profile endpoints.

These are public (no auth required) — the frontend needs company data
to populate dropdowns and show principles before the user logs in.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import CompanyProfile
from app.schemas.companies import CompanyListItem, CompanyResponse

router = APIRouter(prefix="/api/v1/companies", tags=["companies"])


@router.get("", response_model=list[CompanyListItem])
async def list_companies(db: AsyncSession = Depends(get_db)):
    """List all company profiles (compact — no principles).

    Returns all 22+ companies sorted by name.
    Used to populate the company selector dropdown.
    """
    result = await db.execute(
        select(CompanyProfile).order_by(CompanyProfile.name)
    )
    companies = result.scalars().all()
    return [CompanyListItem.model_validate(c) for c in companies]


@router.get("/{company_id}", response_model=CompanyResponse)
async def get_company(company_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get a company profile with full principles and interview guidance.

    Called when the user selects a company — the frontend shows the
    principles in a sidebar panel.
    """
    result = await db.execute(
        select(CompanyProfile).where(CompanyProfile.id == company_id)
    )
    company = result.scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return CompanyResponse.model_validate(company)
