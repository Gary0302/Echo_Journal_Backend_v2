# models/journal.py
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

# No specific model needed for GET /past_entries request/response
# We might add models here later if we implement endpoints
# for creating or retrieving full journal entries.

# Example placeholder for a potential Journal DB model:
# class JournalInDB(BaseModel):
#     _id: Optional[str] = None # Or ObjectId depending on handling
#     UID: str
#     created_at: datetime
#     prompt: str
#     reflection: Optional[str] = None
#     emotions: Optional[int] = None
#     # ... other fields ...