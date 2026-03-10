from pydantic import BaseModel
from typing import Optional

class ItemResponse(BaseModel):
    id:           int
    name:         str
    description:  Optional[str] = None
    price:        float
    is_available: bool

    class Config:
        orm_mode = True