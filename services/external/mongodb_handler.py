# services/external/mongodb_handler.py
from motor.motor_asyncio import AsyncIOMotorDatabase, AsyncIOMotorCollection
from core.db import get_db # Import the async function to get db instance
from models.user import UserCreate, UserInDB # Import relevant user models
# Ensure models for journal/reflection are imported if needed by future functions
# from models.journal import JournalInDB
# from models.dashboard import WeeklyReflectionInDB

from typing import Optional, List, Dict # Import necessary types
import logging
from datetime import datetime, timedelta, timezone # Import datetime components

logger = logging.getLogger(__name__)

# --- Define Collection Names (Matching V1) ---
USERDATA_COLLECTION = "userdata"
JOURNALS_COLLECTION = "journals"
REFLECTIONS_COLLECTION = "reflections" # Define even if not used yet
WEEKLY_REFLECTIONS_COLLECTION = "weekly_reflections"
WISPERS_COLLECTION = "wispers" # Define even if not used yet
# --- End Collection Names ---

# --- Helper functions to get specific collections ---
async def get_userdata_collection() -> AsyncIOMotorCollection:
    """Helper function to get the userdata collection instance."""
    db: AsyncIOMotorDatabase = await get_db()
    return db[USERDATA_COLLECTION]

async def get_journals_collection() -> AsyncIOMotorCollection:
    """Helper function to get the journals collection instance."""
    db: AsyncIOMotorDatabase = await get_db()
    return db[JOURNALS_COLLECTION]

async def get_weekly_reflections_collection() -> AsyncIOMotorCollection:
    """Helper function to get the weekly_reflections collection instance."""
    db: AsyncIOMotorDatabase = await get_db()
    return db[WEEKLY_REFLECTIONS_COLLECTION]

# Add more helpers for other collections (reflections, wispers) if needed
# async def get_reflections_collection() -> AsyncIOMotorCollection: ...
# async def get_wispers_collection() -> AsyncIOMotorCollection: ...

# --- End Helper functions ---


async def get_user_by_uid(uid: str) -> Optional[UserInDB]:
    """
    Finds a user in the 'userdata' collection by their UID.

    Args:
        uid: The User Identifier.

    Returns:
        A UserInDB model instance if found, otherwise None.
    """
    user_collection = await get_userdata_collection()
    logger.debug(f"Querying collection '{USERDATA_COLLECTION}' for UID: {uid}")
    user_doc = await user_collection.find_one({"UID": uid})
    if user_doc:
        try:
            # Map DB doc to Pydantic model
            return UserInDB(**user_doc)
        except Exception as e:
             logger.error(f"Error parsing user document from '{USERDATA_COLLECTION}' for UID {uid}: {e}", exc_info=True)
             return None
    logger.debug(f"User not found in '{USERDATA_COLLECTION}' for UID: {uid}")
    return None

async def create_new_user(user_data: UserCreate) -> UserInDB:
    """
    Creates a new user document in the 'userdata' collection.

    Args:
        user_data: UserCreate model containing UID and Uname.

    Returns:
        The newly created user data as a UserInDB model instance.
        Raises ValueError if insertion fails.
    """
    user_collection = await get_userdata_collection()
    logger.info(f"Attempting to insert new user into '{USERDATA_COLLECTION}' with UID: {user_data.UID}")

    # Prepare document based on UserInDB model (which includes defaults)
    new_user_doc = UserInDB(
        UID=user_data.UID,
        Uname=user_data.Uname,
        Ustreak=0,
        UL_streak=0
        # Add other default fields like creation timestamp if needed in UserInDB model
        # e.g., account_created_at=datetime.now(timezone.utc)
    ).model_dump(by_alias=True, exclude_unset=True) # Use model_dump for Pydantic v2

    try:
        result = await user_collection.insert_one(new_user_doc)
        if result.inserted_id:
            # Retrieve to confirm and return consistent data
            created_user = await get_user_by_uid(user_data.UID)
            if created_user:
                 logger.info(f"Successfully inserted and retrieved user from '{USERDATA_COLLECTION}' with UID: {user_data.UID}")
                 return created_user
            else:
                 # This case should ideally not happen if insert_one succeeded without error
                 # and get_user_by_uid works correctly. Log and raise.
                 logger.error(f"Failed to retrieve user from '{USERDATA_COLLECTION}' immediately after creation for UID {user_data.UID}")
                 raise ValueError("User creation failed: Could not retrieve after insert.")
        else:
            logger.error(f"MongoDB insert_one did not return an inserted_id into '{USERDATA_COLLECTION}' for UID {user_data.UID}")
            raise ValueError("User creation failed: No document inserted.")
    except Exception as e:
        # Log the detailed exception, including potential DuplicateKeyError
        logger.error(f"Database error during user creation in '{USERDATA_COLLECTION}' for UID {user_data.UID}: {e}", exc_info=True)
        # Re-raise a more generic or specific exception
        # Consider catching pymongo.errors.DuplicateKeyError specifically if needed
        raise ValueError(f"Database error during user creation: {e}")


async def get_journals_for_user_past_days(uid: str, days: int = 7) -> List[Dict]:
    """
    Retrieves journal entries for a specific user from the past N days.
    Assumes journals collection documents contain 'UID' and 'created_at' fields.

    Args:
        uid: The User Identifier.
        days: The number of past days to retrieve journals for (default: 7).

    Returns:
        A list of journal documents (as dicts), containing at least 'prompt'.
        Returns an empty list if no journals are found or on error.
    """
    journals_collection = await get_journals_collection()
    # Calculate the start date (N days ago from today)
    # Using timezone.utc for consistency, adjust if your DB stores naive datetimes
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=days)

    logger.debug(f"Querying collection '{JOURNALS_COLLECTION}' for UID '{uid}' from {start_date} to {end_date}")

    try:
        # Ensure the query matches the actual fields in your journals documents
        cursor = journals_collection.find(
            {
                "UID": uid, # Assuming journals have a UID field linking to the user
                "created_at": {"$gte": start_date, "$lt": end_date},
                "prompt": {"$exists": True, "$ne": ""} # Ensure prompt exists and is not empty
            },
            # Project only fields needed for emotion analysis + maybe created_at for context
            {"prompt": 1, "created_at": 1, "_id": 0}
        ).sort("created_at", -1) # Sort descending or ascending as needed

        # Use length=None to retrieve all matching documents
        journals = await cursor.to_list(length=None)
        logger.info(f"Found {len(journals)} journals in '{JOURNALS_COLLECTION}' for UID '{uid}' in the past {days} days.")
        return journals if journals else []
    except Exception as e:
        logger.error(f"Error retrieving journals from '{JOURNALS_COLLECTION}' for UID '{uid}': {e}", exc_info=True)
        return [] # Return empty list on error


# --- Placeholder for future functions for other endpoints ---

# Placeholder for getting latest weekly reflection (used by dashboard service)
async def get_latest_weekly_reflection_for_user(uid: str) -> Optional[Dict]:
    """
    Retrieves the most recent weekly reflection document for a user.
    Returns the full document as a dict, or None if not found or on error.
    """
    weekly_ref_collection = await get_weekly_reflections_collection()
    logger.debug(f"Querying collection '{WEEKLY_REFLECTIONS_COLLECTION}' for latest entry for UID: {uid}")
    try:
        # Find one document, sorted by creation date descending
        reflection_doc = await weekly_ref_collection.find_one(
            {"UID": uid}, # Assuming weekly reflections also have UID field
            sort=[("created_at", -1)] # Assuming 'created_at' field exists
        )
        if reflection_doc:
            logger.info(f"Found latest weekly reflection for UID {uid}")
            # Potentially convert _id to str if needed by caller
            # reflection_doc["_id"] = str(reflection_doc["_id"])
            return reflection_doc
        else:
            logger.info(f"No weekly reflection found for UID {uid}")
            return None
    except Exception as e:
        logger.error(f"Error retrieving latest weekly reflection for UID {uid}: {e}", exc_info=True)
        return None


# Placeholder for getting journal entry dates (used by journal service)
async def get_distinct_journal_dates_in_range(uid: str, start_date: datetime, end_date: datetime) -> List[str]:
    """
    Retrieves distinct dates (YYYY-MM-DD) with journal entries for a user within a date range.
    """
    journals_collection = await get_journals_collection()
    logger.debug(f"Querying distinct journal dates for UID '{uid}' from {start_date} to {end_date}")
    try:
        pipeline = [
            {
                "$match": {
                    "UID": uid,
                    "created_at": {"$gte": start_date, "$lt": end_date}
                }
            },
            {
                # Project created_at to YYYY-MM-DD format string
                "$project": {
                    "dateStr": {
                        "$dateToString": { "format": "%Y-%m-%d", "date": "$created_at", "timezone": "UTC" } # Adjust timezone if needed
                    }
                }
            },
            {
                # Group by the date string to get distinct dates
                "$group": {
                    "_id": "$dateStr"
                }
            },
            {
                # Sort the distinct dates
                "$sort": { "_id": 1 }
            },
            {
                 # Project to get just the date string
                 "$project": { "_id": 0, "date": "$_id"}
            }
        ]
        # Use aggregate for distinct dates projection
        results = await journals_collection.aggregate(pipeline).to_list(length=None)
        dates = [result["date"] for result in results]
        logger.info(f"Found {len(dates)} distinct journal dates for UID '{uid}' in range.")
        return dates
    except Exception as e:
        logger.error(f"Error retrieving distinct journal dates for UID '{uid}': {e}", exc_info=True)
        return []

# --- End Placeholders ---
async def get_distinct_journal_dates_in_range(uid: str, start_date: datetime, end_date: datetime) -> List[str]:
    """
    Retrieves distinct dates (YYYY-MM-DD format strings) with journal entries
    for a user within a specified date range (inclusive start, exclusive end).
    Queries the 'journals' collection.

    Args:
        uid: The User Identifier.
        start_date: The beginning of the date range (timezone-aware recommended).
        end_date: The end of the date range (timezone-aware recommended).

    Returns:
        A sorted list of distinct date strings ("YYYY-MM-DD"), or empty list on error.
    """
    journals_collection = await get_journals_collection()
    logger.debug(f"Querying distinct journal dates in '{JOURNALS_COLLECTION}' for UID '{uid}' from {start_date} to {end_date}")
    try:
        # Ensure the pipeline matches your document structure ('UID', 'created_at')
        # Adjust timezone in $dateToString if your created_at is stored differently
        pipeline = [
            {
                # Filter by user and date range
                "$match": {
                    "UID": uid,
                    "created_at": {"$gte": start_date, "$lt": end_date}
                }
            },
            {
                # Extract date part as string
                "$project": {
                    "dateStr": {
                        "$dateToString": {
                            "format": "%Y-%m-%d",
                            "date": "$created_at",
                            "timezone": "UTC" # Use UTC or your DB's timezone
                        }
                    }
                }
            },
            {
                # Group by date string to get unique dates
                "$group": {
                    "_id": "$dateStr"
                }
            },
            {
                # Sort the dates chronologically
                "$sort": { "_id": 1 }
            },
            {
                 # Reshape the output to just the date string
                 "$project": { "_id": 0, "date": "$_id"}
            }
        ]
        # Execute the aggregation pipeline
        results = await journals_collection.aggregate(pipeline).to_list(length=None)
        # Extract the date strings from the results
        dates = [result["date"] for result in results if "date" in result]
        logger.info(f"Found {len(dates)} distinct journal dates for UID '{uid}' in range.")
        return dates
    except Exception as e:
        logger.error(f"Error retrieving distinct journal dates from '{JOURNALS_COLLECTION}' for UID '{uid}': {e}", exc_info=True)
        return [] # Return empty list on error