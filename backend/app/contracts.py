"""Public conversation contract. Tool traces use a separate development endpoint."""
from uuid import UUID
from pydantic import BaseModel, Field, field_validator, ConfigDict

class ConversationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    session_id: UUID | None = None
    query: str = Field(min_length=1, max_length=4000)

    @field_validator("query")
    @classmethod
    def nonblank_query(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("query must not be blank")
        return value

class ConversationResponse(BaseModel):
    session_id: UUID
    answer: str
    message_id: UUID
    products: list[dict] = Field(default_factory=list)
