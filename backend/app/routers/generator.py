"""
AI answer generator endpoint.

Takes bullet-point inputs and generates a STAR-formatted narrative.
The generated answer can then be edited and submitted for evaluation.
"""

import asyncio
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.rate_limit import rate_limit
from app.services.generator import AnswerGeneratorService

router = APIRouter(prefix="/api/v1/generator", tags=["generator"])


class GenerateRequest(BaseModel):
    """Request to generate a STAR answer from bullet points."""

    question_text: str = Field(..., min_length=10)
    company_name: str = Field(..., min_length=1)
    target_role: str = Field(..., min_length=1)
    experience_level: str = Field(..., min_length=1)
    situation_bullets: str = Field(..., min_length=5)
    task_bullets: str = Field(..., min_length=5)
    action_bullets: str = Field(..., min_length=5)
    result_bullets: str = Field(..., min_length=5)


class GenerateResponse(BaseModel):
    """Generated answer response."""

    answer_text: str
    word_count: int
    model_used: str
    input_tokens: int
    output_tokens: int
    processing_seconds: int


# 5 generations per minute — each one calls Claude API
@router.post(
    "",
    response_model=GenerateResponse,
    dependencies=[Depends(rate_limit(max_requests=5, window_seconds=60))],
)
async def generate_answer(request: GenerateRequest):
    """Generate a STAR-formatted answer from bullet-point inputs.

    The generated answer is returned for the user to review and edit
    before submitting for evaluation. This is NOT auto-submitted.
    """
    service = AnswerGeneratorService()

    try:
        result = await asyncio.to_thread(
            service.generate,
            question_text=request.question_text,
            company_name=request.company_name,
            target_role=request.target_role,
            experience_level=request.experience_level,
            situation_bullets=request.situation_bullets,
            task_bullets=request.task_bullets,
            action_bullets=request.action_bullets,
            result_bullets=request.result_bullets,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")

    word_count = len(result.answer_text.split())

    return GenerateResponse(
        answer_text=result.answer_text,
        word_count=word_count,
        model_used=result.model,
        input_tokens=result.input_tokens,
        output_tokens=result.output_tokens,
        processing_seconds=result.processing_seconds,
    )
