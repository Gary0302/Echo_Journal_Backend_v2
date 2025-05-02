# api/routers/dashboard.py
from fastapi import APIRouter, Query, HTTPException, status
from models.dashboard import EmotionalBreakdownResponse, WeeklyReflectionResponse# Import the response model
from services import dashboard_service # Import the service logic
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get(
    "/emotional_breakdown",
    response_model=EmotionalBreakdownResponse,
    summary="Get Emotional Analysis Results",
    description="Retrieves an analysis of the user's dominant emotions based on recent journal entries.",
    tags=["Dashboard"] # Optional: Tag for Swagger UI grouping
)
async def get_dashboard_emotions(
    # Use Query for GET request parameters
    UID: str = Query(..., description="The unique identifier for the user.")
):
    """
    API endpoint to get the user's emotional breakdown.
    Requires the User ID (UID) as a query parameter.
    """
    logger.debug(f"GET /emotional_breakdown received for UID: {UID}")
    try:
        breakdown_data = await dashboard_service.get_emotional_breakdown(uid=UID)
        return breakdown_data
    except HTTPException as http_exc:
        # Re-raise known HTTP errors from the service layer
        raise http_exc
    except Exception as e:
        # Catch unexpected errors
        logger.error(f"Unexpected error in GET /emotional_breakdown for UID {UID}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while fetching the emotional breakdown."
        )

@router.get(
    "/weekly_reflection",
    response_model=WeeklyReflectionResponse,
    summary="Get Weekly Reflection Content",
    description="Retrieves the latest available weekly reflection content for the user.",
    tags=["Dashboard"]
)
async def get_dashboard_weekly_reflection(
    UID: str = Query(..., description="The unique identifier for the user.")
):
    """
    API endpoint to get the user's latest weekly reflection.
    Requires the User ID (UID) as a query parameter.
    """
    logger.debug(f"GET /weekly_reflection received for UID: {UID}")
    try:
        reflection_data = await dashboard_service.get_latest_weekly_reflection(uid=UID)
        return reflection_data
    except HTTPException as http_exc:
        # Re-raise known HTTP errors (like 404 Not Found) from the service layer
        raise http_exc
    except Exception as e:
        # Catch unexpected errors
        logger.error(f"Unexpected error in GET /weekly_reflection for UID {UID}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while fetching the weekly reflection."
        )
