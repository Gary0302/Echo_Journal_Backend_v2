# services/journal_service.py
from fastapi import HTTPException, status
from services.external import mongodb_handler
from typing import List
import logging
from datetime import datetime, timedelta, timezone
# Import relativedelta for easy month calculations
from dateutil.relativedelta import relativedelta

logger = logging.getLogger(__name__)

async def get_past_entry_dates(uid: str, year_str: str, month_str: str) -> List[str]:
    """
    Service function to get distinct dates with journal entries within a 5-month span
    centered around the requested year and month.

    Args:
        uid: The User Identifier.
        year_str: The requested year (e.g., "2025").
        month_str: The requested month (e.g., "02" for February).

    Raises:
        HTTPException(400): If year or month format is invalid.
        HTTPException(500): If a database error occurs.

    Returns:
        A list of distinct date strings ("YYYY-MM-DD").
    """
    logger.info(f"Getting past entry dates for UID: {uid}, Year: {year_str}, Month: {month_str}")

    # 1. Validate Input
    try:
        year = int(year_str)
        month = int(month_str)
        # Basic validation for month and year ranges
        if not (1 <= month <= 12):
            raise ValueError("Month must be between 01 and 12.")
        if not (1900 <= year <= 2100): # Adjust reasonable year range if needed
            raise ValueError("Year seems out of reasonable range.")
        # Create the first day of the requested month
        requested_month_start = datetime(year, month, 1, tzinfo=timezone.utc)
    except ValueError as e:
        logger.warning(f"Invalid year/month input for UID {uid}: Year='{year_str}', Month='{month_str}'. Error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid year or month format: {e}",
        )

    # 2. Calculate 5-Month Date Range (Requested Month +/- 2 Months)
    # Start date: First day of the month, 2 months prior to requested month
    start_date = requested_month_start - relativedelta(months=2)
    # End date: First day of the month, 3 months after requested month (exclusive)
    # (Because range is [start, end) )
    end_date = requested_month_start + relativedelta(months=3)

    logger.debug(f"Calculated date range for UID {uid}: {start_date} to {end_date}")

    # 3. Call DB Handler
    try:
        date_strings = await mongodb_handler.get_distinct_journal_dates_in_range(
            uid=uid,
            start_date=start_date,
            end_date=end_date
        )
        logger.info(f"Successfully retrieved {len(date_strings)} distinct dates for UID {uid}.")
        return date_strings
    except Exception as e:
        # Log the error from the handler if needed (though handler logs it too)
        logger.error(f"Database error while fetching past entry dates for UID {uid}: {e}", exc_info=True)
        # Raise 500 for unexpected DB errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while retrieving journal dates."
        )

# Add other journal-related service functions here later if needed