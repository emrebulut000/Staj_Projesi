import os
from datetime import datetime, date
import json
from models import Base, User, Category, Meal, Menu, Attendance, engine
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

# Şifreleme için
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Veritabanı dosyasının yolu
db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "instance", "site.db")

# Eğer veritabanı dosyası varsa sil
if os.path.exists(db_path):
    try:
        os.remove(db_path)
        print("Eski veritabanı başarıyla silindi.")
    except PermissionError:
        print("Eski veritabanı silinemedi: İzin hatası. Lütfen programın veritabanı dosyasına erişim izni olduğundan emin olun.")
    except Exception as e:
        print(f"Eski veritabanı silinirken bir hata oluştu: {str(e)}")

# Instance dizini yoksa oluştur
os.makedirs(os.path.dirname(db_path), exist_ok=True)

# Veritabanını oluştur
Base.metadata.create_all(bind=engine)

# Session oluştur
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

# Demo veritabanını oluştur
def create_demo_data():
    try:
        # Admin kullanıcısı oluştur
        admin_user = User(
            username="admin",
            email="admin@example.com",
            hashed_password=pwd_context.hash("admin123"),
            is_admin=True
        )
        db.add(admin_user)

        # Normal kullanıcı oluştur
        test_user = User(
            username="test",
            email="test@example.com",
            hashed_password=pwd_context.hash("test123"),
            is_admin=False
        )
        db.add(test_user)

        # Kategoriler
        categories = [
            Category(name="Ana Yemek", description="Et ve sebze yemekleri"),
            Category(name="Çorba", description="Çeşitli çorbalar"),
            Category(name="Yan Yemek", description="Pilav, makarna, vs."),
            Category(name="Tatlı", description="Tatlılar ve İkramlar"),
            Category(name="İçecek", description="Sıcak ve soğuk içecekler")
        ]
        db.add_all(categories)
        
        # Değişiklikleri kaydet (kategorilerin ID'lerini almak için)
        db.commit()

        # Kategorileri veritabanından al
        ana_yemek = db.query(Category).filter_by(name="Ana Yemek").first()
        corba = db.query(Category).filter_by(name="Çorba").first()
        yan_yemek = db.query(Category).filter_by(name="Yan Yemek").first()
        tatli = db.query(Category).filter_by(name="Tatlı").first()
        icecek = db.query(Category).filter_by(name="İçecek").first()

        # Yemekler
        meals = [
            # Ana Yemekler
            Meal(name="Izgara Köfte", category_id=ana_yemek.id, calories=350, 
                 description="Dana kıyma ile hazırlanmış ızgara köfte"),
            Meal(name="Tavuk Şiş", category_id=ana_yemek.id, calories=280,
                 description="Marine edilmiş tavuk göğsü şiş"),
            Meal(name="Karnıyarık", category_id=ana_yemek.id, calories=320,
                 description="Patlıcan üzerine kıymalı karışım"),
            
            # Çorbalar
            Meal(name="Mercimek Çorbası", category_id=corba.id, calories=120,
                 description="Kırmızı mercimek çorbası"),
            Meal(name="Ezogelin Çorbası", category_id=corba.id, calories=130,
                 description="Geleneksel ezogelin çorbası"),
            Meal(name="Yayla Çorbası", category_id=corba.id, calories=140,
                 description="Yoğurtlu yayla çorbası"),
            
            # Yan Yemekler
            Meal(name="Pirinç Pilavı", category_id=yan_yemek.id, calories=200,
                 description="Tereyağlı pirinç pilavı"),
            Meal(name="Bulgur Pilavı", category_id=yan_yemek.id, calories=180,
                 description="Sebzeli bulgur pilavı"),
            Meal(name="Makarna", category_id=yan_yemek.id, calories=220,
                 description="Sade makarna"),
            
            # Tatlılar
            Meal(name="Sütlaç", category_id=tatli.id, calories=280,
                 description="Fırında sütlaç"),
            Meal(name="Baklava", category_id=tatli.id, calories=350,
                 description="Cevizli baklava"),
            Meal(name="Kemalpaşa", category_id=tatli.id, calories=290,
                 description="Şerbetli kemalpaşa tatlısı"),
            
            # İçecekler
            Meal(name="Ayran", category_id=icecek.id, calories=60,
                 description="Taze ayran"),
            Meal(name="Limonata", category_id=icecek.id, calories=80,
                 description="Taze sıkılmış limonata"),
            Meal(name="Çay", category_id=icecek.id, calories=5,
                 description="Demli çay")
        ]
        db.add_all(meals)
        db.commit()

        # Örnek menüler
        today = date.today()
        menu1 = Menu(
            date=today,
            meal_type="Öğle Yemeği",
            menu_items=json.dumps({
                "Corbasi": "Mercimek Çorbası",
                "Ana_Yemek": "Izgara Köfte",
                "Yan_Yemek": "Pirinç Pilavı",
                "Tatli": "Sütlaç"
            }),
            salad_bar=json.dumps({
                "Salatalar": ["Mevsim Salata", "Çoban Salata"],
                "Soslar": ["Zeytinyağı Limon", "Süzme Yoğurt"]
            })
        )

        menu2 = Menu(
            date=today,
            meal_type="Akşam Yemeği",
            menu_items=json.dumps({
                "Corbasi": "Ezogelin Çorbası",
                "Ana_Yemek": "Tavuk Şiş",
                "Yan_Yemek": "Bulgur Pilavı",
                "Tatli": "Baklava"
            }),
            salad_bar=json.dumps({
                "Salatalar": ["Akdeniz Salata", "Gavurdağı Salata"],
                "Soslar": ["Zeytinyağı Limon", "Tahin Sos"]
            })
        )

        db.add_all([menu1, menu2])

        # Örnek katılım kayıtları
        attendance1 = Attendance(
            user_id=test_user.id,
            date=today,
            will_attend=True
        )

        attendance2 = Attendance(
            user_id=admin_user.id,
            date=today,
            will_attend=True
        )

        db.add_all([attendance1, attendance2])

        # Tüm değişiklikleri kaydet
        db.commit()

        print("Veritabanı başarıyla oluşturuldu ve örnek veriler eklendi!")
        print("\nGiriş bilgileri:")
        print("Admin Kullanıcı: admin / admin123")
        print("Test Kullanıcı: test / test123")

    except IntegrityError as e:
        print(f"Veritabanına veri eklerken bir bütünlük hatası oluştu: {e}")
        db.rollback()
    except Exception as e:
        print(f"Genel bir hata oluştu: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_demo_data()