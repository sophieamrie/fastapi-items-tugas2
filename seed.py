from database import SessionLocal, engine
import models

models.Base.metadata.create_all(bind=engine)
db = SessionLocal()

items = [
    models.Item(name='Laptop', description='Laptop gaming 16GB RAM', price=15000000.0, is_available=True),
    models.Item(name='Mouse', description='Mouse wireless ergonomis', price=250000.0, is_available=True),
    models.Item(name='Keyboard', description='Mechanical keyboard TKL', price=800000.0, is_available=False),
]

db.add_all(items)
db.commit()
db.close()
print('Data berhasil ditambahkan!')