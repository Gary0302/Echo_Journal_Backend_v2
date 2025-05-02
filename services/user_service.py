# services/user_service.py
from fastapi import HTTPException, status
from models.user import UserCreate, UserResponse, UserInDB
from services.external import mongodb_handler # Import the handler module
from typing import Optional
import logging

logger = logging.getLogger(__name__)

async def get_user_info(uid: str) -> UserResponse:
    """
    Service function to get user information by UID.

    Raises:
        HTTPException(404): If the user is not found.

    Returns:
        UserResponse: The user's data formatted for API response.
    """
    logger.info(f"Attempting to retrieve user info for UID: {uid}")
    user_db: Optional[UserInDB] = await mongodb_handler.get_user_by_uid(uid)

    if user_db is None:
        logger.warning(f"User not found for UID: {uid}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with UID '{uid}' not found.",
        )

    # Map UserInDB to UserResponse (fields should match in this case)
    # If field names differed or needed transformation, do it here.
    logger.info(f"Successfully retrieved user info for UID: {uid}")
    return UserResponse(
        UID=user_db.UID,
        Uname=user_db.Uname,
        Ustreak=user_db.Ustreak,
        UL_streak=user_db.UL_streak
        # Map other fields if necessary
    )

async def register_user(user_create_data: UserCreate) -> UserResponse:
    """
    Service function to register a new user.

    Raises:
        HTTPException(409): If a user with the same UID already exists.
        HTTPException(500): If there's a database error during creation.

    Returns:
        UserResponse: The newly created user's data.
    """
    logger.info(f"Attempting to register user with UID: {user_create_data.UID}")
    existing_user = await mongodb_handler.get_user_by_uid(user_create_data.UID)

    if existing_user:
        logger.warning(f"Registration failed: User already exists with UID: {user_create_data.UID}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"User with UID '{user_create_data.UID}' already exists.",
        )

    try:
        new_user_db: UserInDB = await mongodb_handler.create_new_user(user_create_data)
        logger.info(f"Successfully registered user with UID: {new_user_db.UID}")
        # Map UserInDB to UserResponse
        return UserResponse(
            UID=new_user_db.UID,
            Uname=new_user_db.Uname,
            Ustreak=new_user_db.Ustreak,
            UL_streak=new_user_db.UL_streak
            # Map other fields if necessary
        )
    except ValueError as e: # Catch specific error from handler
        logger.error(f"Registration failed due to database error for UID {user_create_data.UID}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to register user due to a database error."
        )
    except Exception as e: # Catch any other unexpected errors
        logger.error(f"An unexpected error occurred during registration for UID {user_create_data.UID}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during user registration."
        )