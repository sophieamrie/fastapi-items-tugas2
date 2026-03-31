from pydantic import BaseModel
from typing import Optional

# ===================== AUTH SCHEMAS =====================

class RegisterRequest(BaseModel):
    username: str
    password: str
    role: Optional[str] = "user"

class LoginRequest(BaseModel):
    username: str
    password: str

# ===================== ITEM SCHEMAS =====================

class ItemCreate(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    is_available: bool = True

class ItemUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    is_available: Optional[bool] = None

class ItemResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    price: float
    is_available: bool

    class Config:
        from_attributes = True