# init_db.py - Veri tabanını silme işlemi kaldırıldı ve mevcut kullanıcı kontrolü eklendi.

import os
from models import Base, User, engine
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext

# Veritabanı dosyasının yolu
db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "instance", "site.db")

# --- DEĞİŞİKLİK 1: VERİTABANI SİLME KODU KALDIRILDI ---
# if os.path.exists(db_path):
#     os.remove(db_path)
# ---------------------------------------------------------

os.makedirs(os.path.dirname(db_path), exist_ok=True)

# Veritabanını ve tabloları, sadece eğer mevcut değillerse oluştur
Base.metadata.create_all(bind=engine)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_initial_data():
    try:
        # --- DEĞİŞİKLİK 2: KULLANICILARIN MEVCUT OLUP OLMADIĞINI KONTROL ET ---

        # Admin kullanıcısını sadece eğer yoksa oluştur
        admin_exists = db.query(User).filter(User.username == "admin").first()
        if not admin_exists:
            admin_user = User(
                username="admin", 
                email="admin@example.com", 
                hashed_password=pwd_context.hash("admin123"), 
                is_admin=True,
                department="Yönetim"
            )
            db.add(admin_user)
            db.commit()
            print("'admin' kullanıcısı oluşturuldu.")
        else:
            print("'admin' kullanıcısı zaten mevcut.")
            admin_user = admin_exists # Test kullanıcısının yöneticisi olarak atamak için mevcut admin'i al

        # Test kullanıcısını sadece eğer yoksa oluştur
        test_user_exists = db.query(User).filter(User.username == "test").first()
        if not test_user_exists:
            test_user = User(
                username="test", 
                email="test@example.com", 
                hashed_password=pwd_context.hash("test123"), 
                is_admin=False,
                department="IT",
                manager_id=admin_user.id 
            )
            db.add(test_user)
            db.commit()
            print("'test' kullanıcısı oluşturuldu ve yöneticisi atandı.")
        else:
             print("'test' kullanıcısı zaten mevcut.")

        print("\nVeritabanı kontrolü tamamlandı.")

    except Exception as e:
        print(f"Bir hata oluştu: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_initial_data()