# fastapi-items-tugas2

# Items API — FastAPI + SQLAlchemy + SQLite

RESTful API sederhana untuk manajemen item, dibuat menggunakan FastAPI, SQLAlchemy (ORM), dan SQLite.

## Struktur Project

items-api/
├── database.py      # Koneksi DB, SessionLocal, Base
├── models.py        # SQLAlchemy Model (struktur tabel)
├── schemas.py       # Pydantic Schema (validasi output)
├── main.py          # FastAPI app & endpoint
├── seed.py          # Data awal untuk testing
└── requirements.txt

## Cara Menjalankan

### 1. Install dependencies
pip install -r requirements.txt

### 2. Tambah data awal
py seed.py

### 3. Jalankan server
uvicorn main:app --reload

### 4. Buka Swagger UI
http://127.0.0.1:8000/docs

## Endpoint

| Method | Endpoint       | Deskripsi                 | Status |
|--------|----------------|---------------------------|--------|
| GET    | /items/        | Ambil semua item          | 200 OK |
| GET    | /items/{id}    | Ambil item berdasarkan ID | 200 OK |
|        |                | Jika ID tidak ditemukan   | 404    |
