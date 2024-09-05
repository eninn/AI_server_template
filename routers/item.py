from pydantic import BaseModel

class ItemRequest(BaseModel):
    input_data: str

class ItemResponse(BaseModel):
    checkout: bool
    return_data: str | None
    runtime: float | None
    message: str
