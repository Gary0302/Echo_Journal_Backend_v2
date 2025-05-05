# api/routers/anonymous.py
from fastapi import APIRouter, HTTPException, status, Body
from fastapi.responses import JSONResponse # Import JSONResponse
from models.anonymous import AnonymousRequest, AnonymousResponse # Import request/response models
from services import anonymous_service # Import the service logic
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post(
    "/anonymous",
    # We don't use response_model here because we construct JSONResponse manually
    # response_model=AnonymousResponse, # Can still define for docs if desired
    summary="Generate Anonymous Reflection",
    description="Generates a reflection based on the provided prompt and emotion score, without saving any data.",
    tags=["Anonymous"] # Tag for Swagger UI
)
async def create_anonymous_reflection(
    item: AnonymousRequest = Body(...)
):
    """
    API endpoint to generate an anonymous reflection.
    Accepts prompt and emotions in the request body.
    Does not store any user data.
    """
    logger.debug("POST /anonymous received.")
    try:
        reflection = await anonymous_service.process_anonymous_reflection(item)
        # Return the specific JSON structure expected ("status" and "reflection")
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "success",
                "reflection": reflection
            }
        )
    except HTTPException as http_exc:
        # Re-raise known HTTP errors (like 500 from service)
        raise http_exc
    except Exception as e:
        # Catch unexpected errors
        logger.error(f"Unexpected error in POST /anonymous: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while generating the reflection."
        )