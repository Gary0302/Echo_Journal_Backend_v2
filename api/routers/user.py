# api/routers/user.py
from fastapi import APIRouter, Query, HTTPException, status, Body
from models.user import UserCreate, UserResponse # Import API models
from services import user_service # Import the service logic
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get(
    "/user_init",
    response_model=UserResponse,
    summary="Get Existing User Data",
    description="Retrieves data for an existing user based on their UID.",
    tags=["User"] # Optional: Tag for Swagger UI grouping
)
async def get_user(
    # Use Query for GET request parameters as discussed
    UID: str = Query(..., description="The unique identifier for the user to retrieve.")
):
    """
    API endpoint to get user data.
    Uses UID from query parameters.
    """
    logger.debug(f"GET /user_init received for UID: {UID}")
    try:
        user_info = await user_service.get_user_info(uid=UID)
        return user_info
    except HTTPException as http_exc:
        # Re-raise HTTPException from the service layer
        raise http_exc
    except Exception as e:
        # Catch any unexpected errors from the service layer or below
        logger.error(f"Unexpected error in GET /user_init for UID {UID}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while fetching user data."
        )

@router.post(
    "/user_init",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED, # Set default success status code
    summary="Add New User",
    description="Creates a new user record if the UID doesn't already exist.",
    tags=["User"]
)
async def create_user(
    # Use Body(...) or just the model type hint for the request body
    user_data: UserCreate = Body(...)
):
    """
    API endpoint to create a new user.
    Uses UserCreate model from request body.
    """
    logger.debug(f"POST /user_init received for UID: {user_data.UID}")
    try:
        new_user_info = await user_service.register_user(user_create_data=user_data)
        # If successful, return the 201 status code set in the decorator
        return new_user_info
    except HTTPException as http_exc:
        # Re-raise HTTPException (like 409 Conflict) from the service layer
        # Ensure appropriate status code is propagated
        raise http_exc
    except Exception as e:
         # Catch any unexpected errors
        logger.error(f"Unexpected error in POST /user_init for UID {user_data.UID}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while creating the user."
        )