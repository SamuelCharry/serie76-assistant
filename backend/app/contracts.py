"""Draft schemas; the mandatory conversation endpoint is not implemented yet."""
from pydantic import BaseModel, Field, field_validator

class ConversationRequest(BaseModel):
    session_id: str | None = None
    query: str = Field(min_length=1)

    @field_validator("query")
    @classmethod
    def nonblank_query(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("query must not be blank")
        return value

class ConversationResponse(BaseModel):
    session_id: str
    answer: str

# Product cards and debug traces will be designed after validating the data model.
