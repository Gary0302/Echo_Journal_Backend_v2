# models/anonymous.py
from pydantic import BaseModel, Field

class AnonymousRequest(BaseModel):
    """Request model for the anonymous reflection endpoint."""
    prompt: str = Field(..., description="The journal prompt text submitted by the user.")
    emotions: int = Field(..., description="User's self-rated emotion score associated with the prompt.") # Consider adding constraints like ge=1, le=5 if applicable

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "prompt": "Feeling a bit overwhelmed today with all the tasks.",
                    "emotions": 2
                }
            ]
        }
    }

class AnonymousResponse(BaseModel):
    """Response model for the anonymous reflection endpoint."""
    reflection: str = Field(..., description="The AI-generated reflection based on the prompt.")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "reflection": "It sounds like you're carrying a heavy load. Remember to breathe and take things one step at a time."
                }
            ]
        }
    }