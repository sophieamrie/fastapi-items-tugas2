import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from main import app, users_db
from database import Base, get_db

# =====================================================================
# DATABASE TEST (SQLite in-memory)
# =====================================================================

TEST_DATABASE_URL = "sqlite:///./test_items.db"
engine_test = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine_test)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

# =====================================================================
# FIXTURES
# =====================================================================

@pytest.fixture(autouse=True)
def reset_db():
    """Reset database dan users sebelum tiap test."""
    Base.metadata.create_all(bind=engine_test)
    users_db.clear()
    yield
    Base.metadata.drop_all(bind=engine_test)

@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c

@pytest.fixture
def admin_token(client):
    """Register dan login sebagai admin."""
    client.post("/register", json={
        "username": "admin_test",
        "password": "adminpass",
        "role": "admin"
    })
    res = client.post("/login", json={
        "username": "admin_test",
        "password": "adminpass"
    })
    return res.json()["token"]

@pytest.fixture
def user_token(client):
    """Register dan login sebagai user biasa."""
    client.post("/register", json={
        "username": "user_test",
        "password": "userpass",
        "role": "user"
    })
    res = client.post("/login", json={
        "username": "user_test",
        "password": "userpass"
    })
    return res.json()["token"]

@pytest.fixture
def sample_item(client, admin_token):
    """Buat satu item sebagai admin."""
    res = client.post(
        "/items/",
        json={"name": "Laptop", "description": "Laptop gaming", "price": 15000000.0, "is_available": True},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    return res.json()

# =====================================================================
# 1. PENGUJIAN AUTENTIKASI (Register & Login)
# =====================================================================

class TestAuth:

    def test_register_berhasil(self, client):
        """Register dengan data valid harus mengembalikan 201."""
        res = client.post("/register", json={
            "username": "user_baru",
            "password": "pass123",
            "role": "user"
        })
        assert res.status_code == 201
        assert "berhasil" in res.json()["message"].lower()

    def test_register_username_duplikat(self, client):
        """Register dengan username yang sudah ada harus mengembalikan 409."""
        client.post("/register", json={"username": "duplikat", "password": "pass"})
        res = client.post("/register", json={"username": "duplikat", "password": "pass2"})
        assert res.status_code == 409

    def test_login_berhasil(self, client):
        """Login dengan kredensial valid harus mengembalikan token dan role."""
        client.post("/register", json={
            "username": "login_user",
            "password": "pass123",
            "role": "user"
        })
        res = client.post("/login", json={
            "username": "login_user",
            "password": "pass123"
        })
        data = res.json()
        assert res.status_code == 200
        assert "token" in data
        assert data["role"] == "user"

    def test_login_password_salah(self, client):
        """Login dengan password salah harus mengembalikan 401."""
        client.post("/register", json={"username": "user_x", "password": "benar"})
        res = client.post("/login", json={"username": "user_x", "password": "salah"})
        assert res.status_code == 401

    def test_login_username_tidak_ada(self, client):
        """Login dengan username tidak terdaftar harus mengembalikan 401."""
        res = client.post("/login", json={"username": "tidak_ada", "password": "pass"})
        assert res.status_code == 401

    def test_akses_tanpa_token(self, client):
        """Akses endpoint tanpa token harus mengembalikan 401 atau 403."""
        res = client.get("/items/")
        assert res.status_code in [401, 403]

    def test_akses_token_invalid(self, client):
        """Akses dengan token palsu harus mengembalikan 401 atau 403."""
        res = client.get("/items/", headers={"Authorization": "Bearer tokenpalsu"})
        assert res.status_code in [401, 403]

# =====================================================================
# 2. PENGUJIAN CRUD OPERASIONAL (Items)
# =====================================================================

class TestCRUD:

    # --- CREATE ---
    def test_create_item_berhasil(self, client, admin_token):
        """Admin dapat membuat item baru, mengembalikan 201."""
        res = client.post(
            "/items/",
            json={"name": "Mouse", "description": "Wireless mouse", "price": 250000.0, "is_available": True},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        data = res.json()
        assert res.status_code == 201
        assert data["name"] == "Mouse"
        assert data["price"] == 250000.0
        assert "id" in data

    def test_create_item_tanpa_nama(self, client, admin_token):
        """Membuat item tanpa field name harus mengembalikan 422."""
        res = client.post(
            "/items/",
            json={"description": "No name", "price": 100000.0},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert res.status_code == 422

    # --- READ ---
    def test_get_all_items(self, client, user_token, sample_item):
        """User dapat mengambil semua items."""
        res = client.get("/items/", headers={"Authorization": f"Bearer {user_token}"})
        assert res.status_code == 200
        assert isinstance(res.json(), list)
        assert len(res.json()) >= 1

    def test_get_item_by_id_berhasil(self, client, user_token, sample_item):
        """User dapat mengambil detail item berdasarkan ID."""
        item_id = sample_item["id"]
        res = client.get(f"/items/{item_id}", headers={"Authorization": f"Bearer {user_token}"})
        assert res.status_code == 200
        assert res.json()["id"] == item_id

    def test_get_item_tidak_ditemukan(self, client, user_token):
        """Mengambil item dengan ID yang tidak ada harus mengembalikan 404."""
        res = client.get("/items/9999", headers={"Authorization": f"Bearer {user_token}"})
        assert res.status_code == 404

    # --- UPDATE ---
    def test_update_item_berhasil(self, client, admin_token, sample_item):
        """Admin dapat mengupdate item, mengembalikan data terbaru."""
        item_id = sample_item["id"]
        res = client.put(
            f"/items/{item_id}",
            json={"name": "Laptop Pro", "price": 20000000.0},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        data = res.json()
        assert res.status_code == 200
        assert data["name"] == "Laptop Pro"
        assert data["price"] == 20000000.0

    def test_update_item_tidak_ditemukan(self, client, admin_token):
        """Update item yang tidak ada harus mengembalikan 404."""
        res = client.put(
            "/items/9999",
            json={"name": "Tidak Ada"},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert res.status_code == 404

    # --- DELETE ---
    def test_delete_item_berhasil(self, client, admin_token, sample_item):
        """Admin dapat menghapus item, mengembalikan pesan sukses."""
        item_id = sample_item["id"]
        res = client.delete(
            f"/items/{item_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert res.status_code == 200
        assert "berhasil" in res.json()["message"].lower()

    def test_delete_item_tidak_ditemukan(self, client, admin_token):
        """Menghapus item yang tidak ada harus mengembalikan 404."""
        res = client.delete(
            "/items/9999",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert res.status_code == 404

# =====================================================================
# 3. PENGUJIAN RBAC (Role-Based Access Control / Access Denied)
# =====================================================================

class TestRBAC:

    def test_user_tidak_bisa_create_item(self, client, user_token):
        """User biasa tidak boleh membuat item — harus 403 Forbidden."""
        res = client.post(
            "/items/",
            json={"name": "Keyboard", "price": 500000.0},
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert res.status_code == 403

    def test_user_tidak_bisa_update_item(self, client, user_token, sample_item):
        """User biasa tidak boleh mengupdate item — harus 403 Forbidden."""
        item_id = sample_item["id"]
        res = client.put(
            f"/items/{item_id}",
            json={"name": "Hacked"},
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert res.status_code == 403

    def test_user_tidak_bisa_delete_item(self, client, user_token, sample_item):
        """User biasa tidak boleh menghapus item — harus 403 Forbidden."""
        item_id = sample_item["id"]
        res = client.delete(
            f"/items/{item_id}",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert res.status_code == 403

    def test_user_bisa_get_items(self, client, user_token, sample_item):
        """User biasa boleh melihat daftar item — harus 200 OK."""
        res = client.get("/items/", headers={"Authorization": f"Bearer {user_token}"})
        assert res.status_code == 200

    def test_user_bisa_get_item_by_id(self, client, user_token, sample_item):
        """User biasa boleh melihat detail item — harus 200 OK."""
        item_id = sample_item["id"]
        res = client.get(f"/items/{item_id}", headers={"Authorization": f"Bearer {user_token}"})
        assert res.status_code == 200

    def test_admin_bisa_create_item(self, client, admin_token):
        """Admin dapat membuat item — harus 201 Created."""
        res = client.post(
            "/items/",
            json={"name": "Monitor", "price": 3000000.0, "is_available": True},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert res.status_code == 201

    def test_admin_bisa_delete_item(self, client, admin_token, sample_item):
        """Admin dapat menghapus item — harus 200 OK."""
        item_id = sample_item["id"]
        res = client.delete(
            f"/items/{item_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert res.status_code == 200