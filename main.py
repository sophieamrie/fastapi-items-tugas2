from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import models, schemas
from database import engine, get_db

models.Base.metadata.create_all(bind=engine)
app = FastAPI(title="Items API", version="1.0.0")

@app.get("/items/", response_model=List[schemas.ItemResponse])
def get_all_items(db: Session = Depends(get_db)):
    return db.query(models.Item).all()

@app.get("/items/{item_id}", response_model=schemas.ItemResponse)
def get_item_by_id(item_id: int, db: Session = Depends(get_db)):
    item = db.query(models.Item).filter(models.Item.id == item_id).first()
    if item is None:
        raise HTTPException(status_code=404, detail=f"Item {item_id} tidak ditemukan")
    return item