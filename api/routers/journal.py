# api/routers/journal.py
from fastapi import APIRouter, Query, HTTPException, status, Depends
from typing import List
from services import journal_service # Import the service logic
import logging
import re # Import regex for validation pattern

logger = logging.getLogger(__name__)
router = APIRouter()

# --- Regular Expressions for Query Parameter Validation ---
# Matches YYYY format (e.g., 2024)
YEAR_REGEX = r"^\d{4}$"
# Matches MM format (01-12)
MONTH_REGEX = r"^(0[1-9]|1[0-2])$"
# --- End Regex ---


@router.get(
    "/past_entries",
    response_model=List[str], # Response is a list of date strings
    summary="Get Dates with Journal Entries",
    description="Retrieves a list of distinct dates (YYYY-MM-DD) that have journal entries "
                "within a 5-month window (requested month ± 2 months) for the user.",
    tags=["Journal"]
)
async def get_journal_past_entries(
    UID: str = Query(..., description="The unique identifier for the user."),
    year: str = Query(..., description="The target year in YYYY format (e.g., '2025').",
                      pattern=YEAR_REGEX), # Apply regex pattern validation
    month: str = Query(..., description="The target month in MM format (e.g., '02' for February).",
                       pattern=MONTH_REGEX) # Apply regex pattern validation
):
    """
    API endpoint to get dates with journal entries for a specific month span.
    Requires UID, year (YYYY), and month (MM) as query parameters.
    """
    logger.debug(f"GET /past_entries received for UID: {UID}, Year: {year}, Month: {month}")
    # Basic format validation is handled by pattern in Query.
    # Service layer handles deeper validation (e.g., numeric conversion, range).
    try:
        dates = await journal_service.get_past_entry_dates(
            uid=UID,
            year_str=year,
            month_str=month
        )
        return dates
    except HTTPException as http_exc:
        # Re-raise known HTTP errors (like 400 Bad Request) from the service layer
        raise http_exc
    except Exception as e:
        # Catch unexpected errors
        logger.error(f"Unexpected error in GET /past_entries for UID {UID}, {year}-{month}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while fetching past entry dates."
        )

# Add other journal-related endpoints here later (e.g., POST new entry, GET specific entry)