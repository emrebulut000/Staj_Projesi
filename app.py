from datetime import datetime, timedelta, date
from typing import List, Optional, Annotated
import uvicorn
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from pydantic import BaseModel, ConfigDict
from models import User, Menu, Attendance, Category, Meal, engine
from sqlalchemy.orm import sessionmaker
import json

# JWT için gerekli sabitler
SECRET_KEY = "your-secret-key"  # Gerçek uygulamada güvenli bir şekilde saklanmalı
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# FastAPI uygulaması
app = FastAPI()

# CORS ayarları
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Veritabanı oturumu
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Şifreleme için
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Pydantic modelleri
class Token(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    access_token: str
    token_type: str

class TokenData(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    username: str | None = None

class UserBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    username: str
    email: str

class CategoryBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: str
    description: str | None = None

class CategoryCreate(CategoryBase):
    pass

class MealBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: str
    category_id: int
    calories: int | None = None
    description: str | None = None
    image_url: str | None = None
    is_active: bool = True

class MealCreate(MealBase):
    pass

class UserCreate(UserBase):
    model_config = ConfigDict(from_attributes=True)
    password: str
    is_admin: bool = False

class AttendanceCreate(BaseModel):
    date: date
    will_attend: bool

class MenuCreate(BaseModel):
    date: date
    meal_type: str
    menu_items: dict
    salad_bar: dict

# Yardımcı fonksiyonlar
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = db.query(User).filter(User.username == token_data.username).first()
    if user is None:
        raise credentials_exception
    return user

# Admin kontrol fonksiyonu
async def get_current_admin_user(current_user: User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin yetkisi gerekli"
        )
    return current_user

# API Endpoints
@app.get("/api/current-user")
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "is_admin": current_user.is_admin
    }

@app.post("/token")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[Session, Depends(get_db)]
):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer", "is_admin": user.is_admin}

@app.post("/users/", response_model=UserBase)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    hashed_password = get_password_hash(user.password)
    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
        is_admin=user.is_admin
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.post("/menu/")
async def create_menu(menu: MenuCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized")
    db_menu = Menu(
        date=menu.date,
        meal_type=menu.meal_type,
        menu_items=menu.menu_items,
        salad_bar=menu.salad_bar
    )
    db.add(db_menu)
    db.commit()
    db.refresh(db_menu)
    return {"message": "Menu created successfully"}

@app.get("/menu/{date}")
async def get_menu(date: str, db: Session = Depends(get_db)):
    menu_date = datetime.strptime(date, "%Y-%m-%d").date()
    menu = db.query(Menu).filter(Menu.date == menu_date).first()
    if not menu:
        raise HTTPException(status_code=404, detail="Menu not found")
    return menu

@app.post("/attendance/")
async def create_attendance(
    attendance: AttendanceCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_attendance = Attendance(
        user_id=current_user.id,
        date=attendance.date,
        will_attend=attendance.will_attend
    )
    db.add(db_attendance)
    db.commit()
    db.refresh(db_attendance)
    return {"message": "Attendance recorded successfully"}

@app.get("/attendance/")
async def get_user_attendance(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    attendances = db.query(Attendance).filter(Attendance.user_id == current_user.id).all()
    return attendances

# Kategori route'ları
@app.get("/api/categories")
async def get_categories(current_user: User = Depends(get_current_admin_user), db: Session = Depends(get_db)):
    categories = db.query(Category).all()
    return categories

@app.post("/api/categories")
async def create_category(
    category: CategoryCreate,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    db_category = Category(**category.dict())
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category

@app.delete("/api/categories/{category_id}")
async def delete_category(
    category_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Kategori bulunamadı")
    db.delete(category)
    db.commit()
    return {"message": "Kategori başarıyla silindi"}

# Yemek route'ları
@app.get("/api/meals")
async def get_meals(current_user: User = Depends(get_current_admin_user), db: Session = Depends(get_db)):
    meals = db.query(Meal).all()
    return meals

@app.post("/api/meals")
async def create_meal(
    meal: MealCreate,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    db_meal = Meal(**meal.dict())
    db.add(db_meal)
    db.commit()
    db.refresh(db_meal)
    return db_meal

@app.delete("/api/meals/{meal_id}")
async def delete_meal(
    meal_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    meal = db.query(Meal).filter(Meal.id == meal_id).first()
    if not meal:
        raise HTTPException(status_code=404, detail="Yemek bulunamadı")
    meal.is_active = False
    db.commit()
    return {"message": "Yemek başarıyla silindi"}

# Menü route'ları
@app.get("/api/menu")
async def get_all_menus(current_user: User = Depends(get_current_admin_user), db: Session = Depends(get_db)):
    menus = db.query(Menu).all()
    return menus

@app.post("/api/menu")
async def create_menu_plan(
    menu: MenuCreate,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    db_menu = Menu(**menu.dict())
    db.add(db_menu)
    db.commit()
    db.refresh(db_menu)
    return db_menu

@app.delete("/api/menu/{menu_id}")
async def delete_menu(
    menu_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    menu = db.query(Menu).filter(Menu.id == menu_id).first()
    if not menu:
        raise HTTPException(status_code=404, detail="Menü bulunamadı")
    db.delete(menu)
    db.commit()
    return {"message": "Menü başarıyla silindi"}

# İstatistik route'ları
@app.get("/api/stats/dashboard")
async def get_dashboard_stats(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    total_meals = db.query(Meal).filter(Meal.is_active == True).count()
    total_categories = db.query(Category).count()
    today = datetime.now().date()
    today_selections = db.query(Attendance).filter(Attendance.date == today).count()
    active_users = db.query(User).filter(User.is_active == True).count()

    recent_activities = [
        {"time": datetime.now(), "action": "Sistem istatistikleri güncellendi"}
    ]

    # Son 5 menü değişikliği
    recent_menus = db.query(Menu).order_by(Menu.created_at.desc()).limit(5).all()
    for menu in recent_menus:
        recent_activities.append({
            "time": menu.created_at,
            "action": f"Yeni menü eklendi: {menu.date} - {menu.meal_type}"
        })

    return {
        "total_meals": total_meals,
        "total_categories": total_categories,
        "today_selections": today_selections,
        "active_users": active_users,
        "recent_activities": [
            f"{act['time'].strftime('%H:%M:%S')} - {act['action']}"
            for act in sorted(recent_activities, key=lambda x: x['time'], reverse=True)
        ]
    }

# Admin endpoints
@app.get("/admin/attendance/{date}")
async def get_daily_attendance(
    date: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    attendance_date = datetime.strptime(date, "%Y-%m-%d").date()
    attendances = db.query(Attendance).filter(Attendance.date == attendance_date).all()
    return attendances

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
