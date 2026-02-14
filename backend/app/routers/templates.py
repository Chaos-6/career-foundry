"""
Answer template endpoints.

CRUD for user-owned answer templates. All endpoints require authentication
since templates are personal resources. Templates can be:

1. Created from scratch in the template library
2. Saved from an existing evaluated answer ("Save as Template")
3. Loaded into the NewEvaluation form to pre-fill the answer textarea

Templates are scoped to the authenticated user — you can only see/edit
your own templates.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models import AnswerTemplate, User
from app.schemas.templates import (
    TemplateCreateRequest,
    TemplateListItem,
    TemplateResponse,
    TemplateUpdateRequest,
)

router = APIRouter(prefix="/api/v1/templates", tags=["templates"])


@router.post("", response_model=TemplateResponse, status_code=201)
async def create_template(
    request: TemplateCreateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new answer template.

    If is_default=True, clears any existing default template first
    (only one default allowed per user).
    """
    # If marking as default, clear existing default
    if request.is_default:
        await db.execute(
            update(AnswerTemplate)
            .where(
                AnswerTemplate.user_id == user.id,
                AnswerTemplate.is_default == True,  # noqa: E712
            )
            .values(is_default=False)
        )

    template = AnswerTemplate(
        user_id=user.id,
        name=request.name,
        template_text=request.template_text,
        role_tags=request.role_tags,
        competency_tags=request.competency_tags,
        is_default=request.is_default,
    )
    db.add(template)
    await db.commit()
    await db.refresh(template)

    return TemplateResponse.model_validate(template)


@router.get("", response_model=list[TemplateResponse])
async def list_templates(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all templates for the current user.

    Returns full template data (including text) ordered by:
    1. Default templates first
    2. Most recently updated
    """
    result = await db.execute(
        select(AnswerTemplate)
        .where(AnswerTemplate.user_id == user.id)
        .order_by(
            AnswerTemplate.is_default.desc(),
            AnswerTemplate.updated_at.desc(),
        )
    )
    templates = result.scalars().all()

    return [TemplateResponse.model_validate(t) for t in templates]


@router.get("/{template_id}", response_model=TemplateResponse)
async def get_template(
    template_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a single template by ID.

    Also increments usage_count — this is called when the user loads
    a template into the evaluation form.
    """
    result = await db.execute(
        select(AnswerTemplate).where(
            AnswerTemplate.id == template_id,
            AnswerTemplate.user_id == user.id,
        )
    )
    template = result.scalar_one_or_none()

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    # Increment usage count (lightweight tracking)
    template.usage_count = (template.usage_count or 0) + 1
    await db.commit()
    await db.refresh(template)

    return TemplateResponse.model_validate(template)


@router.put("/{template_id}", response_model=TemplateResponse)
async def update_template(
    template_id: UUID,
    request: TemplateUpdateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update an existing template.

    Only provided fields are updated (partial update via PUT — pragmatic
    choice over PATCH given the simple schema).
    """
    result = await db.execute(
        select(AnswerTemplate).where(
            AnswerTemplate.id == template_id,
            AnswerTemplate.user_id == user.id,
        )
    )
    template = result.scalar_one_or_none()

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    # If marking as default, clear existing default
    if request.is_default:
        await db.execute(
            update(AnswerTemplate)
            .where(
                AnswerTemplate.user_id == user.id,
                AnswerTemplate.is_default == True,  # noqa: E712
                AnswerTemplate.id != template_id,
            )
            .values(is_default=False)
        )

    # Apply updates (only non-None fields)
    update_data = request.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(template, field, value)

    await db.commit()
    await db.refresh(template)

    return TemplateResponse.model_validate(template)


@router.delete("/{template_id}", status_code=204)
async def delete_template(
    template_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a template.

    Hard delete — templates are personal drafts, not shared resources,
    so no need for soft delete.
    """
    result = await db.execute(
        select(AnswerTemplate).where(
            AnswerTemplate.id == template_id,
            AnswerTemplate.user_id == user.id,
        )
    )
    template = result.scalar_one_or_none()

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    await db.delete(template)
    await db.commit()
