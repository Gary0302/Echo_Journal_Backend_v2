# services/dashboard_service.py
from fastapi import HTTPException, status
from models.dashboard import EmotionalBreakdownResponse, EmotionPercentage, WeeklyReflectionResponse # Import response models
from services.external import mongodb_handler, gemini_handler # Import handlers
from typing import List, Dict, Optional # Import necessary types
import logging

logger = logging.getLogger(__name__)

async def get_emotional_breakdown(uid: str) -> EmotionalBreakdownResponse:
    """
    Service function to calculate and return the emotional breakdown for a user,
    based on journal entries from the past N days (default 7).

    Args:
        uid: The User Identifier.

    Raises:
        HTTPException(404): If no recent journals are found for the user.
        HTTPException(500): If Gemini analysis or other processing errors occur.

    Returns:
        EmotionalBreakdownResponse: The emotional breakdown result.
    """
    logger.info(f"Getting emotional breakdown for UID: {uid}")

    # 1. Get recent journals from DB (e.g., past 7 days)
    recent_journals: List[Dict] = await mongodb_handler.get_journals_for_user_past_days(uid, days=7)

    if not recent_journals:
        logger.warning(f"No recent journal entries found for UID {uid} to generate emotion breakdown.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No recent journal entries found to perform emotional analysis."
        )

    # 2. Extract prompts (ensure 'prompt' field exists and is not empty)
    prompts = [journal.get("prompt", "") for journal in recent_journals if journal.get("prompt")]
    if not prompts:
        logger.error(f"Journals found for UID {uid}, but failed to extract any valid prompts.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process journal entries for analysis."
        )

    # 3. Call Gemini for analysis
    logger.debug(f"Calling Gemini for emotion analysis with {len(prompts)} prompts for UID {uid}.")
    emotion_results: Optional[Dict[str, float]] = await gemini_handler.generate_emotion_breakdown_async(prompts)

    if emotion_results is None:
        logger.error(f"Gemini analysis failed for UID {uid}.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate emotional breakdown from AI analysis."
        )

    # 4. Format results into response model list
    emotion_list: List[EmotionPercentage] = []
    for name, percent in emotion_results.items():
         try:
             # Basic validation can happen here too if needed, though Pydantic model handles structure
             emotion_list.append(EmotionPercentage(emotion=name, percentage=percent))
         except Exception as e: # Catch potential errors creating EmotionPercentage
             logger.warning(f"Skipping invalid emotion data ('{name}': {percent}) for UID {uid}. Error: {e}")
             continue # Skip this item and continue with others

    if not emotion_list:
        logger.error(f"Emotion analysis result for UID {uid} was empty after formatting.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="AI analysis returned no valid emotions."
            )

    # 5. Create final response object (Pydantic validates list length here)
    try:
        # Pydantic model EmotionalBreakdownResponse handles min/max length validation
        response = EmotionalBreakdownResponse(emotions=emotion_list)
        logger.info(f"Successfully generated emotional breakdown for UID: {uid} with {len(emotion_list)} emotions.")
        return response
    except Exception as validation_error: # Catch Pydantic validation errors (e.g., list length)
         logger.error(f"Validation error creating EmotionalBreakdownResponse for UID {uid}: {validation_error}", exc_info=True)
         # Provide more specific feedback if possible, e.g., about list length
         raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            # Customize detail based on validation error if needed
            detail=f"Failed to format emotional breakdown response: {validation_error}"
         )


# --- Placeholder for Weekly Reflection Service ---
async def get_latest_weekly_reflection(uid: str) -> WeeklyReflectionResponse:
    """
    Service function to retrieve the latest weekly reflection for a user.

    Args:
        uid: The User Identifier.

    Raises:
        HTTPException(404): If no weekly reflection is found for the user.
        HTTPException(500): If a database or other error occurs.

    Returns:
        WeeklyReflectionResponse: The latest weekly reflection content.
    """
    logger.info(f"Getting latest weekly reflection for UID: {uid}")

    # 1. Get latest reflection from DB
    try:
        latest_reflection_doc: Optional[Dict] = await mongodb_handler.get_latest_weekly_reflection_for_user(uid)
    except Exception as e:
         logger.error(f"Database error retrieving weekly reflection for UID {uid}: {e}", exc_info=True)
         raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="A database error occurred while fetching the weekly reflection."
         )

    if latest_reflection_doc is None or "weekly_reflection" not in latest_reflection_doc:
        logger.warning(f"No weekly reflection found in DB for UID {uid}.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No weekly reflection found for this user."
        )

    # 2. Extract the reflection text (assuming field name is 'weekly_reflection')
    reflection_text = latest_reflection_doc.get("weekly_reflection", "")
    if not reflection_text:
         logger.warning(f"Weekly reflection document found for UID {uid}, but the reflection text is empty.")
         # Decide: return 404 or empty reflection? Let's return 404 as it's not useful.
         raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Weekly reflection content is empty."
         )

    # 3. Format response
    try:
        response = WeeklyReflectionResponse(reflection=reflection_text)
        logger.info(f"Successfully retrieved latest weekly reflection for UID: {uid}")
        return response
    except Exception as validation_error: # Catch Pydantic validation errors
         logger.error(f"Error creating Pydantic response model for weekly reflection (UID {uid}): {validation_error}", exc_info=True)
         raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to format weekly reflection response."
         )

async def get_latest_weekly_reflection(uid: str) -> WeeklyReflectionResponse:
    """
    Service function to retrieve the latest stored weekly reflection for a user.

    Args:
        uid: The User Identifier.

    Raises:
        HTTPException(404): If no weekly reflection is found for the user,
                           or if the reflection text is missing/empty.
        HTTPException(500): If a database or other unexpected error occurs.

    Returns:
        WeeklyReflectionResponse: Contains the latest weekly reflection text.
    """
    logger.info(f"Getting latest weekly reflection for UID: {uid}")

    # 1. Call the handler to get the latest reflection document from DB
    latest_reflection_doc: Optional[Dict] = await mongodb_handler.get_latest_weekly_reflection_for_user(uid)

    # Handle case where DB query itself failed (handler returns None)
    # Note: The handler logs the specific DB error. Here we raise 500.
    # If handler returned None because *no document was found*, that's handled next.
    # We might need more specific error signaling from handler if distinction is critical.
    # Assuming None means either "not found" or "DB error".

    if latest_reflection_doc is None:
        # This could be "not found" OR a database error during the query.
        # Check logs from mongodb_handler for specifics if needed.
        # For the API consumer, "Not Found" is usually appropriate if no data is available.
        logger.warning(f"No weekly reflection document found or DB error occurred for UID {uid}.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No weekly reflection found for this user."
        )

    # 2. Extract the reflection text (assuming field name is 'weekly_reflection')
    # Use .get() to safely access the field, defaulting to None or ""
    reflection_text = latest_reflection_doc.get("weekly_reflection")

    if not reflection_text: # Handles None or empty string ""
         logger.warning(f"Weekly reflection document found for UID {uid}, but the 'weekly_reflection' field is missing or empty.")
         # Even if the doc exists, if the essential data is missing, treat as not found.
         raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Weekly reflection content is missing or empty."
         )

    # 3. Format response using the Pydantic model
    try:
        response = WeeklyReflectionResponse(reflection=str(reflection_text)) # Ensure it's a string
        logger.info(f"Successfully retrieved latest weekly reflection for UID: {uid}")
        return response
    except Exception as validation_error: # Catch potential Pydantic validation errors
         logger.error(f"Error creating Pydantic response model for weekly reflection (UID {uid}): {validation_error}", exc_info=True)
         raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to format weekly reflection response."
         )