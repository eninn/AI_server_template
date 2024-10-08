from pydantic import BaseModel

class ItemResponse(BaseModel):
    checkout: bool
    return_data: str
    runtime: float
    message: str
