# models/user.py
from pydantic import BaseModel, Field
from typing import Optional

class UserBase(BaseModel):
    """Base model for user data, excluding sensitive info if any."""
    UID: str = Field(..., description="Unique User Identifier")
    Uname: str = Field(..., description="User's display name")

class UserCreate(UserBase):
    """Model for creating a new user via POST /user_init."""
    # Inherits UID and Uname
    pass

class UserResponse(UserBase):
    """Model for returning user data via GET /user_init or after POST."""
    # Inherits UID and Uname
    Ustreak: int = Field(..., description="Main consecutive daily entry streak")
    UL_streak: int = Field(..., description="Other consecutive record streak (e.g., weekly)")

    # Optional: Add other fields if needed later, e.g., account creation date
    # account_created_at: Optional[datetime] = None

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "UID": "user-123-abc",
                    "Uname": "Gary",
                    "Ustreak": 15,
                    "UL_streak": 2
                }
            ]
        }
    }

class UserInDB(UserBase):
    """Model representing user data as stored in MongoDB."""
    # Inherits UID and Uname
    Ustreak: int = 0
    UL_streak: int = 0
    # Add any other fields stored in the DB
    # e.g., last_entry_date: Optional[datetime] = None
    # e.g., account_created_at: datetime = Field(default_factory=datetime.utcnow)

    # Allow extra fields in case DB has more data than the model explicitly defines
    # model_config = ConfigDict(extra='allow') # Using older Pydantic v1 style temporarily for clarity
    # For Pydantic v2:
    model_config = {
         "extra": "allow"
    }