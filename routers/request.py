from pydantic import BaseModel

class ItemRequest(BaseModel):
    input_data: str