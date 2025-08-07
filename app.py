# app.py - Tüm özellikler ve son düzeltmeleri içeren tam hali
from datetime import datetime, timedelta, date, time
from typing import List, Annotated, Optional
import uvicorn
from fastapi import FastAPI, Depends, HTTPException, status, BackgroundTasks, Query, Response
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import orm
from sqlalchemy.orm import Session
from pydantic import BaseModel, ConfigDict, EmailStr
from models import User, Menu, Attendance, OvertimeRequest, engine
from sqlalchemy.orm import sessionmaker
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig

# EKLENDİ: .env dosyasını okumak için gerekli kütüphaneler
import os
from dotenv import load_dotenv

# EKLENDİ: .env dosyasındaki değişkenleri yükle
load_dotenv()


# --- E-POSTA YAPILANDIRMASI ---
conf = ConnectionConfig(
    MAIL_USERNAME = "emrebulut661@gmail.com",
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD"), # DEĞİŞTİ: Artık .env dosyasından okunuyor
    MAIL_FROM = "emrebulut661@gmail.com",
    MAIL_PORT = 587,
    MAIL_SERVER = "smtp.gmail.com",
    MAIL_STARTTLS = True,
    MAIL_SSL_TLS = False,
    USE_CREDENTIALS = True,
    VALIDATE_CERTS = True
)

# --- JWT Ayarları ---
SECRET_KEY = os.getenv("SECRET_KEY") # DEĞİŞTİ: Artık .env dosyasından okunuyor
if not SECRET_KEY:
    raise ValueError("Lütfen .env dosyasında SECRET_KEY değişkenini ayarlayın!")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

app = FastAPI()

# --- CORS AYARLARI ---
origins = ["http://localhost", "http://localhost:8080", "http://127.0.0.1:5500", "http://127.0.0.1:5501", "null"]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# --- Pydantic Modelleri ---
class Token(BaseModel):
    access_token: str
    token_type: str

class MenuCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    date: date
    meal_type: str
    menu_items: dict

class AttendanceCreate(BaseModel):
    date: date
    will_attend: bool

class ManagerInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    username: str

class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    username: str
    email: str
    department: str | None = None
    manager_id: int | None = None
    manager: Optional[ManagerInfo] = None
    is_admin: bool

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    department: str | None = None
    is_admin: bool = False
    manager_id: int | None = None

class UserUpdate(BaseModel):
    email: EmailStr | None = None
    department: str | None = None
    manager_id: int | None = None

class AttendanceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    will_attend: bool
    user: UserOut

class OvertimeRequestBase(BaseModel):
    date: date
    start_time: time
    end_time: time
    reason: str

class OvertimeRequestCreate(OvertimeRequestBase):
    department: str

class OvertimeRequestOut(OvertimeRequestBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    department: str
    status: str
    user: UserOut

# --- Yardımcı Fonksiyonlar ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None: raise credentials_exception
        user = db.query(User).options(orm.joinedload(User.manager), orm.joinedload(User.subordinates)).filter(User.username == username).first()
        if user is None: raise credentials_exception
        return user
    except JWTError:
        raise credentials_exception

async def get_current_admin_user(current_user: User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin yetkisi gerekli")
    return current_user

async def send_overtime_notification(email_to: List[str], subject: str, body: str):
    if not all(email_to):
        print(f"Uyarı: Gönderilecek e-posta adresi bulunamadı veya geçersiz. Alıcılar: {email_to}")
        return
    message = MessageSchema(subject=subject, recipients=email_to, body=body, subtype="html")
    fm = FastMail(conf)
    try:
        await fm.send_message(message)
    except Exception as e:
        print(f"E-posta gönderilirken hata oluştu: {e}")

# --- API Endpoints ---
@app.post("/token")
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Hatalı kullanıcı adı veya şifre")
    
    access_token = create_access_token(data={"sub": user.username})
    
    # DEĞİŞTİ: Yönetici rolü daha güvenilir bir yöntemle kontrol ediliyor.
    managed_user = db.query(User).filter(User.manager_id == user.id).first()
    is_manager = True if managed_user else False
    
    return {
        "access_token": access_token, 
        "token_type": "bearer", 
        "is_admin": user.is_admin,
        "is_manager": is_manager,
        "username": user.username,
        "department": user.department
    }

@app.post("/api/users/", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate, current_admin: User = Depends(get_current_admin_user), db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Bu kullanıcı adı zaten kullanılıyor.")
    db_email = db.query(User).filter(User.email == user.email).first()
    if db_email:
        raise HTTPException(status_code=400, detail="Bu e-posta adresi zaten kullanılıyor.")
    hashed_password = pwd_context.hash(user.password)
    new_user_data = user.model_dump()
    new_user_data['hashed_password'] = hashed_password
    del new_user_data['password']
    new_user = User(**new_user_data)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.put("/api/users/{user_id}", response_model=UserOut)
async def update_user_details(user_id: int, user_update: UserUpdate, current_admin: User = Depends(get_current_admin_user), db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı.")
    update_data = user_update.model_dump(exclude_unset=True)
    if 'email' in update_data and update_data['email'] != db_user.email:
        existing_email = db.query(User).filter(User.email == update_data['email']).first()
        if existing_email:
            raise HTTPException(status_code=400, detail="Bu e-posta adresi başka bir kullanıcı tarafından kullanılıyor.")
    for key, value in update_data.items():
        setattr(db_user, key, value)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.delete("/api/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: int, current_admin: User = Depends(get_current_admin_user), db: Session = Depends(get_db)):
    db_user = db.query(User).options(orm.joinedload(User.subordinates)).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı.")
    if db_user.subordinates:
        for subordinate in db_user.subordinates:
            subordinate.manager_id = None
            db.add(subordinate)
    db.delete(db_user)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@app.get("/api/users", response_model=List[UserOut])
async def get_all_users(current_admin: User = Depends(get_current_admin_user), db: Session = Depends(get_db)):
    return db.query(User).options(orm.joinedload(User.manager)).order_by(User.username).all()

@app.get("/api/menus", response_model=List[MenuCreate])
async def get_menus_by_date_range(start_date: date, end_date: date, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Menu).filter(Menu.date >= start_date, Menu.date <= end_date).order_by(Menu.date).all()

@app.post("/attendance/")
async def create_or_update_attendance(attendances: List[AttendanceCreate], current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    for attendance_data in attendances:
        db_attendance = db.query(Attendance).filter(Attendance.user_id == current_user.id, Attendance.date == attendance_data.date).first()
        if db_attendance:
            db_attendance.will_attend = attendance_data.will_attend
        else:
            db_attendance = Attendance(user_id=current_user.id, date=attendance_data.date, will_attend=attendance_data.will_attend)
            db.add(db_attendance)
    db.commit()
    return {"message": f"{len(attendances)} adet katılım kaydı başarıyla işlendi."}

@app.post("/api/overtime", status_code=status.HTTP_201_CREATED)
async def create_overtime_request(request: OvertimeRequestCreate, background_tasks: BackgroundTasks, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not current_user.manager:
        raise HTTPException(status_code=400, detail="Atanmış bir yöneticiniz bulunmuyor. Lütfen İK ile iletişime geçin.")
    db_request = OvertimeRequest(**request.model_dump(), user_id=current_user.id, status="Yönetici Onayı Bekliyor")
    db.add(db_request)
    db.commit()
    manager_email = current_user.manager.email
    email_subject = f"Yeni Fazla Mesai Talebi: {current_user.username}"
    email_body = f"<p><b>{current_user.username}</b> adlı personel yeni bir fazla mesai talebinde bulundu. Onayınız için lütfen sisteme giriş yapınız.</p>"
    background_tasks.add_task(send_overtime_notification, [manager_email], email_subject, email_body)
    return db_request

@app.get("/api/overtime/me", response_model=List[OvertimeRequestOut])
async def get_my_overtime_requests(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(OvertimeRequest).options(orm.joinedload(OvertimeRequest.user)).filter(OvertimeRequest.user_id == current_user.id).order_by(OvertimeRequest.date.desc()).all()

@app.get("/api/overtime/manager/pending", response_model=List[OvertimeRequestOut], summary="Yöneticinin Onayını Bekleyen Talepler")
async def get_manager_pending_requests(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    subordinate_ids = [sub.id for sub in current_user.subordinates]
    if not subordinate_ids: return []
    return db.query(OvertimeRequest).options(orm.joinedload(OvertimeRequest.user)).filter(OvertimeRequest.user_id.in_(subordinate_ids), OvertimeRequest.status == "Yönetici Onayı Bekliyor").order_by(OvertimeRequest.date.desc()).all()

@app.get("/api/overtime/manager/all", response_model=List[OvertimeRequestOut], summary="Yöneticinin Ekibine Ait Tüm Talepler")
async def get_manager_all_requests(status: str | None = None, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    subordinate_ids = [sub.id for sub in current_user.subordinates]
    if not subordinate_ids:
        return []
    query = db.query(OvertimeRequest).options(orm.joinedload(OvertimeRequest.user)).filter(OvertimeRequest.user_id.in_(subordinate_ids))
    if status:
        if status == "Beklemede":
            query = query.filter(OvertimeRequest.status.in_(["Yönetici Onayı Bekliyor", "İK Onayı Bekliyor"]))
        elif status == "Reddedildi":
            query = query.filter(OvertimeRequest.status.in_(["Yönetici Tarafından Reddedildi", "Reddedildi"]))
        else:
            query = query.filter(OvertimeRequest.status == status)
    return query.order_by(OvertimeRequest.date.desc()).all()

@app.put("/api/overtime/{request_id}/manager_action", summary="Yöneticinin Talebi Onaylama/Reddetme İşlemi")
async def manager_action_on_request(request_id: int, action: str = Query(..., pattern="^(approve|reject)$"), background_tasks: BackgroundTasks = BackgroundTasks(), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    db_request = db.query(OvertimeRequest).options(orm.joinedload(OvertimeRequest.user)).filter(OvertimeRequest.id == request_id).first()
    if not db_request: raise HTTPException(status_code=404, detail="Talep bulunamadı")
    if db_request.user.manager_id != current_user.id: raise HTTPException(status_code=403, detail="Bu talebi işleme yetkiniz yok")

    hr_email = os.getenv("HR_EMAIL") # DEĞİŞTİ: Artık .env dosyasından okunuyor
    user_email = db_request.user.email
    if action == "approve":
        db_request.status = "İK Onayı Bekliyor"
        email_subject = f"İK Onayına Sunulan Mesai Talebi: {db_request.user.username}"
        email_body = f"<p><b>{db_request.user.username}</b> personelinin fazla mesai talebi yöneticisi tarafından onaylanmış ve İK onayına sunulmuştur.</p>"
        background_tasks.add_task(send_overtime_notification, [hr_email], email_subject, email_body)
    else:
        db_request.status = "Yönetici Tarafından Reddedildi"
        email_subject = "Fazla Mesai Talebiniz Reddedildi"
        email_body = f"<p>Merhaba {db_request.user.username},</p><p>Fazla mesai talebiniz yöneticiniz tarafından reddedilmiştir.</p>"
        background_tasks.add_task(send_overtime_notification, [user_email], email_subject, email_body)
    db.commit()
    return db_request

@app.get("/api/overtime/all", response_model=List[OvertimeRequestOut])
async def get_all_overtime_requests(status: str | None = None, user_id: int | None = None, department: str | None = None, current_admin: User = Depends(get_current_admin_user), db: Session = Depends(get_db)):
    query = db.query(OvertimeRequest).options(orm.joinedload(OvertimeRequest.user))
    if status:
        if status == "Beklemede":
            query = query.filter(OvertimeRequest.status.in_(["Yönetici Onayı Bekliyor", "İK Onayı Bekliyor"]))
        elif status == "Reddedildi":
            query = query.filter(OvertimeRequest.status.in_(["Yönetici Tarafından Reddedildi", "Reddedildi"]))
        else:
            query = query.filter(OvertimeRequest.status == status)
    if user_id: query = query.filter(OvertimeRequest.user_id == user_id)
    if department: query = query.filter(OvertimeRequest.department == department)
    return query.order_by(OvertimeRequest.date.desc()).all()

@app.put("/api/overtime/{request_id}/hr_action")
async def hr_action_on_request(request_id: int, status: str = Query(..., pattern="^(Onaylandı|Reddedildi)$"), background_tasks: BackgroundTasks = BackgroundTasks(), current_admin: User = Depends(get_current_admin_user), db: Session = Depends(get_db)):
    db_request = db.query(OvertimeRequest).options(orm.joinedload(OvertimeRequest.user)).filter(OvertimeRequest.id == request_id).first()
    if not db_request: raise HTTPException(status_code=404, detail="Talep bulunamadı")
    if db_request.status != "İK Onayı Bekliyor": raise HTTPException(status_code=400, detail=f"Bu talep zaten işleme alınmış veya yönetici onayı bekliyor. Mevcut durum: {db_request.status}")
    db_request.status = status
    db.commit()
    user_email = db_request.user.email
    email_subject = f"Fazla Mesai Talebiniz Sonuçlandı"
    email_body = f"<p>Merhaba {db_request.user.username},</p><p>Fazla mesai talebiniz İK departmanı tarafından <b>{status}</b> olarak sonuçlanmıştır.</p>"
    background_tasks.add_task(send_overtime_notification, [user_email], email_subject, email_body)
    return db_request

@app.post("/api/menu")
async def create_menu_plan(menu: MenuCreate, current_user: User = Depends(get_current_admin_user), db: Session = Depends(get_db)):
    existing_menu = db.query(Menu).filter(Menu.date == menu.date, Menu.meal_type == menu.meal_type).first()
    if existing_menu: raise HTTPException(status_code=409, detail="Bu tarih ve öğün türü için zaten bir menü mevcut.")
    db_menu = Menu(**menu.model_dump())
    db.add(db_menu)
    db.commit()
    db.refresh(db_menu)
    return db_menu

@app.get("/api/stats/dashboard")
async def get_dashboard_stats(current_user: User = Depends(get_current_admin_user), db: Session = Depends(get_db)):
    today = datetime.now().date()
    today_selections = db.query(Attendance).filter(Attendance.date == today, Attendance.will_attend == True).count()
    active_users = db.query(User).filter(User.is_active == True).count()
    return {"today_selections": today_selections, "active_users": active_users}

@app.get("/api/attendance/{report_date}", response_model=List[AttendanceOut])
async def get_attendance_report(report_date: date, current_admin: User = Depends(get_current_admin_user), db: Session = Depends(get_db)):
    return db.query(Attendance).options(orm.joinedload(Attendance.user)).filter(Attendance.date == report_date).all()

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)