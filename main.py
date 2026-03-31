from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import List, Optional
import models, schemas
from database import engine, get_db
import jwt
import datetime

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Items API", version="2.0.0")

SECRET_KEY = "secret-key-rahasia-hasanuddin-2024"
ALGORITHM = "HS256"
security = HTTPBearer()

# ===================== IN-MEMORY USER DB =====================
users_db = {}  # { username: { password, role } }

# ===================== AUTH HELPERS =====================

def generate_token(username: str, role: str) -> str:
    payload = {
        "username": username,
        "role": role,
        "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=1)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token telah kadaluarsa")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token tidak valid")

def require_role(*roles):
    def checker(current_user: dict = Depends(get_current_user)):
        if current_user["role"] not in roles:
            raise HTTPException(status_code=403, detail="Akses ditolak")
        return current_user
    return checker

# ===================== AUTH ENDPOINTS =====================

@app.post("/register", status_code=201)
def register(data: schemas.RegisterRequest):
    if data.username in users_db:
        raise HTTPException(status_code=409, detail="Username sudah terdaftar")
    users_db[data.username] = {"password": data.password, "role": data.role}
    return {"message": "Registrasi berhasil"}

@app.post("/login")
def login(data: schemas.LoginRequest):
    user = users_db.get(data.username)
    if not user or user["password"] != data.password:
        raise HTTPException(status_code=401, detail="Username atau password salah")
    token = generate_token(data.username, user["role"])
    return {"token": token, "role": user["role"]}

# ===================== CRUD ITEMS ENDPOINTS =====================

@app.get("/items/", response_model=List[schemas.ItemResponse])
def get_all_items(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    return db.query(models.Item).all()

@app.get("/items/{item_id}", response_model=schemas.ItemResponse)
def get_item_by_id(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    item = db.query(models.Item).filter(models.Item.id == item_id).first()
    if item is None:
        raise HTTPException(status_code=404, detail=f"Item {item_id} tidak ditemukan")
    return item

@app.post("/items/", response_model=schemas.ItemResponse, status_code=201)
def create_item(
    data: schemas.ItemCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("admin"))
):
    item = models.Item(**data.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item

@app.put("/items/{item_id}", response_model=schemas.ItemResponse)
def update_item(
    item_id: int,
    data: schemas.ItemUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("admin"))
):
    item = db.query(models.Item).filter(models.Item.id == item_id).first()
    if item is None:
        raise HTTPException(status_code=404, detail=f"Item {item_id} tidak ditemukan")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(item, key, value)
    db.commit()
    db.refresh(item)
    return item

@app.delete("/items/{item_id}")
def delete_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("admin"))
):
    item = db.query(models.Item).filter(models.Item.id == item_id).first()
    if item is None:
        raise HTTPException(status_code=404, detail=f"Item {item_id} tidak ditemukan")
    db.delete(item)
    db.commit()
    return {"message": f"Item {item_id} berhasil dihapus"}