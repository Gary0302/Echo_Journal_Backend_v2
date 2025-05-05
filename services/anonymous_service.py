# services/anonymous_service.py
from fastapi import HTTPException, status
from models.anonymous import AnonymousRequest # Import the request model
from services.external import gemini_handler # Import the Gemini handler
from typing import Optional
import logging

logger = logging.getLogger(__name__)

async def process_anonymous_reflection(request_data: AnonymousRequest) -> str:
    """
    Service function to process an anonymous reflection request.

    Args:
        request_data: The incoming request data containing prompt and emotions.

    Raises:
        HTTPException(500): If the AI generation fails.

    Returns:
        The generated reflection text.
    """
    logger.info("Processing anonymous reflection request.")

    reflection_text: Optional[str] = await gemini_handler.generate_single_reflection_async(
        prompt=request_data.prompt,
        emotions=request_data.emotions
    )

    if reflection_text is None:
        logger.error("Failed to generate reflection via Gemini for anonymous request.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not generate reflection at this time. Please try again later."
        )

    logger.info("Successfully processed anonymous reflection request.")
    return reflection_text