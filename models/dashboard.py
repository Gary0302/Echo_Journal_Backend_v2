# models/dashboard.py
from pydantic import BaseModel, Field
from typing import List

class EmotionPercentage(BaseModel):
    """Represents a single emotion and its percentage."""
    emotion: str = Field(..., description="Name of the emotion")
    # Use float for percentage to allow decimals if needed
    percentage: float = Field(..., description="Percentage value for this emotion (0-100)")

class EmotionalBreakdownResponse(BaseModel):
    """Response model for the emotional breakdown endpoint."""
    emotions: List[EmotionPercentage] = Field(
        ...,
        description="List of dominant emotions and their percentages. Should contain 3 to 5 emotions as per API spec.",
        min_length=3, # Pydantic v2 validator, works for lists
        max_length=5  # Pydantic v2 validator, works for lists
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "emotions": [
                        {"emotion": "Happy", "percentage": 40.0},
                        {"emotion": "Sad", "percentage": 30.0},
                        {"emotion": "Calm", "percentage": 30.0}
                    ]
                }
            ]
        }
    }

# Add models for Weekly Reflection later
class WeeklyReflectionResponse(BaseModel):
    reflection: str = Field(..., description="The text content of the weekly reflection.")

    model_config = {
      "json_schema_extra": {
          "examples": [
              {
                  "reflection": "This week I felt more balanced and productive, noticing a pattern of..."
              }
          ]
      }
    }
