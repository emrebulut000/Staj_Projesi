
import sys
from datetime import datetime, timedelta, date
from PySide6.QtWidgets import *
from PySide6.QtCore import Qt, QDate, QTime, QTimer
from PySide6.QtGui import QFont, QColor
from sqlalchemy.orm import sessionmaker
from models import Base, User, Menu, Attendance, OvertimeRequest, engine
from passlib.context import CryptContext
import pandas as pd

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

STYLE = """
QMainWindow, QWidget {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #f8f9fc, stop:0.3 #f5f7fa, stop:1 #eef2f7);
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    color: #333;
    
    font-size: 15px;
}
#Header {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #667eea, stop:1 #764ba2);
    color: white;
    padding: 20px 30px;
    font-size: 24px;
    font-weight: bold;
    border-bottom-left-radius: 18px;
    border-bottom-right-radius: 18px;
    min-height: 60px;
}
QTabWidget::pane {
    border: none;
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #f8f9fc, stop:1 #eef2f7);
    border-radius: 0 0 15px 15px;
}
QTabWidget::tab-bar {
    left: 5px;
}
QTabBar::tab {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #8b7bd1, stop:1 #9c88d4);
    color: white;
    padding: 12px 24px;
    border-radius: 8px 8px 0 0;
    font-size: 14px;
    font-weight: 600;
    border: none;
    margin-right: 4px;
    margin-top: 5px;
}
QTabBar::tab:selected {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #667eea, stop:1 #764ba2);
    color: white;
    border-bottom: none;
}
QTabBar::tab:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #7b6ed6, stop:1 #8a7bd8);
}
QPushButton {
    border: none;
    border-radius: 8px;
    font-size: 15px;
    font-weight: 600;
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #667eea, stop:1 #764ba2);
    color: white;
    padding: 10px 22px;
}
QPushButton:hover {
    background: #5649c7;
    color: #fff;
}
QFrame#Card {
    background: white;
    border-radius: 15px;
    padding: 30px 34px;
    box-shadow: 0 8px 22px 0 rgba(44,62,80,.09);
    margin-bottom: 26px;
}
QLineEdit, QDateEdit, QTimeEdit, QTextEdit {
    background: #f9fafb;
    border: 2px solid #e1e1e1;
    border-radius: 8px;
    padding: 12px 15px;
    font-size: 15px;
}
QLineEdit:focus, QDateEdit:focus, QTimeEdit:focus, QTextEdit:focus {
    border: 2px solid #667eea;
}
QTableWidget {
    background: white;
    border-radius: 10px;
    font-size: 15px;
    color: #333;
    gridline-color: transparent;
    border: none;
    outline: none;
    min-height: 200px;  /* Minimum tablo yüksekliği */
}
QTableWidget::item {
    border: none;
    padding: 8px;
    background-color: transparent;
}
QTableWidget::item:selected {
    background-color: rgba(102, 126, 234, 0.1);
    border: none;
}
QHeaderView::section {
    background: #f8f9fa;
    font-weight: bold;
    font-size: 14px;
    border: none;
    padding: 10px;
}
"""

class MainApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🍽️ Yemekhane Sistemi (Modern Masaüstü)")
        self.setMinimumSize(1400, 900)
        self.resize(1600, 1000)  # Başlangıç boyutu
        self.setStyleSheet(STYLE)
        self.stacked = QStackedWidget()
        self.setCentralWidget(self.stacked)
        self.login_screen = LoginScreen(self.login_success, self)
        self.stacked.addWidget(self.login_screen)

    def login_success(self, user, username, is_admin, login_type="user"):
        # Giriş tipine göre panel belirle
        if is_admin and login_type == "admin":
            # Admin paneli
            self.admin_panel = AdminPanel(user, self.back_to_login)
            self.stacked.addWidget(self.admin_panel)
            self.stacked.setCurrentWidget(self.admin_panel)
        elif self.is_manager(user) and login_type == "admin":
            # Admin panelinden giriş yapan yönetici -> Yönetici paneli
            self.manager_panel = ManagerPanel(user, self.back_to_login)
            self.stacked.addWidget(self.manager_panel)
            self.stacked.setCurrentWidget(self.manager_panel)
        else:
            # Kullanıcı paneli (normal kullanıcı veya kullanıcı girişi yapan yönetici)
            self.user_panel = UserPanel(user, self.back_to_login)
            self.stacked.addWidget(self.user_panel)
            self.stacked.setCurrentWidget(self.user_panel)
    
    def is_manager(self, user):
        """Kullanıcının departman yöneticisi olup olmadığını kontrol et"""
        try:
            db = SessionLocal()
            try:
                # Bu kullanıcının yönetici olduğu başka kullanıcılar var mı?
                managed_users = db.query(User).filter_by(manager_id=user.id).first()
                return managed_users is not None
            finally:
                db.close()
        except:
            return False
    
    def back_to_login(self):
        """Login ekranına geri dön"""
        # Mevcut paneli temizle
        current_widget = self.stacked.currentWidget()
        if current_widget != self.login_screen:
            self.stacked.removeWidget(current_widget)
            current_widget.deleteLater()
        
        # Login ekranına dön ve form alanlarını temizle
        self.login_screen.user_username.clear()
        self.login_screen.user_password.clear()
        self.login_screen.admin_username.clear()
        self.login_screen.admin_password.clear()
        self.login_screen.msg.clear()
        self.stacked.setCurrentWidget(self.login_screen)

class LoginScreen(QWidget):
    def __init__(self, login_success, main_window):
        super().__init__()
        self.login_success = login_success
        self.main_window = main_window
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header wrapper
        header_frame = QFrame()
        header_frame.setObjectName("Header")
        header_layout = QVBoxLayout(header_frame)
        header_layout.setContentsMargins(30, 30, 30, 30)
        
        header = QLabel("🍽️ Yemek Listesi\nGiriş Yap")
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet("color: white; font-size: 24px; font-weight: bold; line-height: 1.2; background: transparent;")
        header_layout.addWidget(header)
        layout.addWidget(header_frame)

        tab_widget = QTabWidget()
        tab_widget.setTabBarAutoHide(False)
        layout.addWidget(tab_widget)

        # Kullanıcı girişi tabı
        user_tab = QWidget()
        user_form = QFormLayout(user_tab)
        self.user_username = QLineEdit()
        self.user_password = QLineEdit()
        self.user_password.setEchoMode(QLineEdit.Password)
        # Enter tuşu ile giriş yapma
        self.user_username.returnPressed.connect(lambda: self.do_login(False))
        self.user_password.returnPressed.connect(lambda: self.do_login(False))
        user_form.addRow("Kullanıcı Adı:", self.user_username)
        user_form.addRow("Şifre:", self.user_password)
        user_btn = QPushButton("Giriş Yap")
        user_btn.clicked.connect(lambda: self.do_login(False))
        user_form.addRow(user_btn)
        tab_widget.addTab(user_tab, "👤 Kullanıcı")

        # Admin girişi tabı
        admin_tab = QWidget()
        admin_form = QFormLayout(admin_tab)
        self.admin_username = QLineEdit()
        self.admin_password = QLineEdit()
        self.admin_password.setEchoMode(QLineEdit.Password)
        # Enter tuşu ile admin girişi yapma
        self.admin_username.returnPressed.connect(lambda: self.do_login(True))
        self.admin_password.returnPressed.connect(lambda: self.do_login(True))
        admin_form.addRow("Admin Adı:", self.admin_username)
        admin_form.addRow("Şifre:", self.admin_password)
        admin_btn = QPushButton("Admin Girişi")
        admin_btn.clicked.connect(lambda: self.do_login(True))
        admin_form.addRow(admin_btn)
        tab_widget.addTab(admin_tab, "👨‍💼 Admin/Yönetici")

        # Spacer ekle - mesaj label'ini yukarıya taşımak için
        layout.addStretch(2)

        self.msg = QLabel("")
        self.msg.setAlignment(Qt.AlignCenter)
        self.msg.setStyleSheet("margin-bottom: 80px; padding: 15px; font-size: 16px;")
        layout.addWidget(self.msg)
        
        # Alt spacer ekle
        layout.addStretch(1)

    def do_login(self, is_admin):
        uname = self.admin_username.text().strip() if is_admin else self.user_username.text().strip()
        upass = self.admin_password.text() if is_admin else self.user_password.text()
        
        if not uname or not upass:
            self.msg.setText("❌ Kullanıcı adı ve şifre zorunlu!")
            self.msg.setStyleSheet("color: red; font-weight: bold;")
            return
            
        try:
            db = SessionLocal()
            try:
                user = db.query(User).filter(User.username == uname).first()
                if not user:
                    self.msg.setText("❌ Kullanıcı bulunamadı!")
                    self.msg.setStyleSheet("color: red; font-weight: bold;")
                    return
                    
                if not pwd_context.verify(upass, user.hashed_password):
                    self.msg.setText("❌ Şifre hatalı!")
                    self.msg.setStyleSheet("color: red; font-weight: bold;")
                    return
                    
                if is_admin and not user.is_admin and not self.main_window.is_manager(user):
                    self.msg.setText("❌ Bu kullanıcının admin/yönetici yetkisi yok!")
                    self.msg.setStyleSheet("color: red; font-weight: bold;")
                    return
                    
                # Başarılı giriş
                self.msg.setText("✅ Giriş başarılı!")
                self.msg.setStyleSheet("color: green; font-weight: bold;")
                # Login tipini belirle
                login_type = "admin" if is_admin else "user"
                # Doğrudan veritabanı erişiminde token yok, kullanıcıyı nesne olarak ileteceğiz
                self.login_success(user, uname, user.is_admin, login_type)
            finally:
                db.close()
        except Exception as e:
            self.msg.setText(f"❌ Giriş sırasında hata oluştu: {e}")
            self.msg.setStyleSheet("color: red; font-weight: bold;")

class UserPanel(QWidget):
    def __init__(self, user, back_to_login_callback):
        super().__init__()
        self.user = user
        self.username = user.username
        self.back_to_login_callback = back_to_login_callback
        self.active_view = 'daily'
        self.current_date = date.today()
        self.current_menus = []
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        header_frame = QFrame()
        header_frame.setObjectName("Header")
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(30, 20, 30, 20)  # Sol, üst, sağ, alt margin
        header_layout.setSpacing(15)  # Widget'lar arası boşluk
        title = QLabel("🍽️ Kullanıcı Paneli")
        title.setFont(QFont("Segoe UI", 20, QFont.Bold))
        title.setStyleSheet("color: white; background: transparent;")
        header_layout.addWidget(title)
        header_layout.addStretch()
        user_label = QLabel(f"{self.username}")
        user_label.setStyleSheet("font-weight: 600; color: white; font-size: 17px; background: transparent;")
        logout_btn = QPushButton("🚪 Çıkış")
        logout_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 rgba(239, 68, 68, 0.8), stop: 1 rgba(220, 38, 38, 0.9));
                color: white;
                border: none;
                padding: 12px 20px;
                border-radius: 8px;
                font-size: 14px;
                font-weight: 600;
                min-width: 80px;
                min-height: 20px;
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 rgba(220, 38, 38, 0.9), stop: 1 rgba(185, 28, 28, 1.0));
            }
            QPushButton:pressed {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 rgba(185, 28, 28, 1.0), stop: 1 rgba(153, 27, 27, 1.0));
            }
        """)
        logout_btn.clicked.connect(self.logout)
        header_layout.addWidget(user_label)
        header_layout.addWidget(logout_btn)
        layout.addWidget(header_frame)

        # Ana Tablar
        self.tabs = QTabWidget()
        self.tabs.setTabBarAutoHide(False)
        self.tabs.addTab(self.menu_tab_ui(), "🍽️ Yemekhane Menüsü")
        self.tabs.addTab(self.mesai_tab_ui(), "🕒 Fazla Mesai Taleplerim")
        
        layout.addWidget(self.tabs)

    def menu_tab_ui(self):
        widget = QWidget()
        vbox = QVBoxLayout(widget)

        # Gün/Hafta/Ay view butonları
        btn_layout = QHBoxLayout()
        self.daily_btn = QPushButton("Günlük")
        self.weekly_btn = QPushButton("Haftalık")
        self.monthly_btn = QPushButton("Aylık")
        for btn, view in [(self.daily_btn, 'daily'), (self.weekly_btn, 'weekly'), (self.monthly_btn, 'monthly')]:
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, v=view: self.set_active_view(v))
            btn_layout.addWidget(btn)
        vbox.addLayout(btn_layout)
        self.daily_btn.setChecked(True)
        self.set_view_btn_styles()

        # Filtre seçenekleri ekle
        filter_frame = QFrame()
        filter_frame.setStyleSheet("background-color: #f8f9fa; border-radius: 8px; padding: 15px; margin: 10px 0;")
        filter_layout = QVBoxLayout(filter_frame)
        
        filter_title = QLabel("🔍 Görünüm Filtreleri:")
        filter_title.setStyleSheet("font-weight: bold; color: #374151; margin-bottom: 10px;")
        filter_layout.addWidget(filter_title)
        
        filter_checkboxes = QHBoxLayout()
        self.hide_weekends_cb = QCheckBox("🏖️ Hafta sonlarını gizle")
        self.hide_empty_days_cb = QCheckBox("📋 Boş günleri gizle")
        self.hide_past_days_cb = QCheckBox("⏰ Geçmiş günleri gizle")
        
        # Checkbox stilleri
        checkbox_style = """
        QCheckBox {
            font-size: 13px;
            color: #374151;
            spacing: 8px;
        }
        QCheckBox::indicator {
            width: 16px;
            height: 16px;
            border: 2px solid #d1d5db;
            border-radius: 3px;
            background-color: white;
        }
        QCheckBox::indicator:checked {
            background-color: #667eea;
            border-color: #667eea;
            image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iMTIiIHZpZXdCb3g9IjAgMCAxMiAxMiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTEwIDNMNC41IDguNUwyIDYiIHN0cm9rZT0id2hpdGUiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIi8+Cjwvc3ZnPgo=);
        }
        QCheckBox::indicator:hover {
            border-color: #667eea;
        }
        """
        for cb in [self.hide_weekends_cb, self.hide_empty_days_cb, self.hide_past_days_cb]:
            cb.setStyleSheet(checkbox_style)
            cb.stateChanged.connect(self.apply_filters)
            filter_checkboxes.addWidget(cb)
        
        filter_checkboxes.addStretch()
        filter_layout.addLayout(filter_checkboxes)
        vbox.addWidget(filter_frame)

        # Tarih/navigasyon
        nav_layout = QHBoxLayout()
        self.prev_btn = QPushButton("← Önceki")
        self.next_btn = QPushButton("Sonraki →")
        self.period_label = QLabel("")
        nav_layout.addWidget(self.prev_btn)
        nav_layout.addStretch()
        nav_layout.addWidget(self.period_label)
        nav_layout.addStretch()
        nav_layout.addWidget(self.next_btn)
        vbox.addLayout(nav_layout)

        self.prev_btn.clicked.connect(lambda: self.navigate_date(-1))
        self.next_btn.clicked.connect(lambda: self.navigate_date(1))

        # Takvim görünümü için scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                background-color: #f1f5f9;
                width: 12px;
                border-radius: 6px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background-color: #667eea;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #5a67d8;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
            }
            QScrollBar:horizontal {
                background-color: #f1f5f9;
                height: 12px;
                border-radius: 6px;
                margin: 0px;
            }
            QScrollBar::handle:horizontal {
                background-color: #667eea;
                border-radius: 6px;
                min-width: 20px;
            }
            QScrollBar::handle:horizontal:hover {
                background-color: #5a67d8;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                border: none;
                background: none;
            }
        """)
        
        # Menü kartlarını gösterecek ana widget
        self.menu_container = QWidget()
        self.menu_layout = QGridLayout(self.menu_container)
        self.menu_layout.setSpacing(15)
        self.menu_layout.setContentsMargins(15, 15, 15, 15)
        
        # Grid layout için daha iyi boyutlandırma
        self.menu_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        scroll_area.setWidget(self.menu_container)
        vbox.addWidget(scroll_area)

        # Bilgi mesajı
        info_label = QLabel("💡 Seçimleriniz anında kaydedilir. Evet/Hayır butonlarına tıklayarak yemek katılım durumunuzu belirleyebilirsiniz.")
        info_label.setStyleSheet("color: #6b7280; font-style: italic; padding: 10px; background-color: #f9fafb; border-radius: 8px; margin: 10px 0;")
        info_label.setWordWrap(True)
        vbox.addWidget(info_label)

        # Menüleri yükle
        self.load_menu_data()

        return widget

    def set_active_view(self, view):
        self.active_view = view
        self.daily_btn.setChecked(view == 'daily')
        self.weekly_btn.setChecked(view == 'weekly')
        self.monthly_btn.setChecked(view == 'monthly')
        self.set_view_btn_styles()
        self.load_menu_data()

    def set_view_btn_styles(self):
        for btn in [self.daily_btn, self.weekly_btn, self.monthly_btn]:
            if btn.isChecked():
                btn.setStyleSheet("background: #4f46e5; color: white;")
            else:
                btn.setStyleSheet("background: white; color: #4b5563;")

    def navigate_date(self, direction):
        if self.active_view == 'daily':
            self.current_date += timedelta(days=direction)
        elif self.active_view == 'weekly':
            self.current_date += timedelta(days=7 * direction)
        elif self.active_view == 'monthly':
            # Aylık navigasyonda daha güvenli tarih hesaplama
            try:
                if direction > 0:
                    # Sonraki ay
                    if self.current_date.month == 12:
                        self.current_date = self.current_date.replace(year=self.current_date.year + 1, month=1, day=1)
                    else:
                        self.current_date = self.current_date.replace(month=self.current_date.month + 1, day=1)
                else:
                    # Önceki ay
                    if self.current_date.month == 1:
                        self.current_date = self.current_date.replace(year=self.current_date.year - 1, month=12, day=1)
                    else:
                        self.current_date = self.current_date.replace(month=self.current_date.month - 1, day=1)
            except ValueError:
                # Hata durumunda bugünün tarihini kullan
                self.current_date = date.today().replace(day=1)
        self.load_menu_data()

    def get_period(self):
        today = self.current_date
        if self.active_view == 'daily':
            return today, today
        elif self.active_view == 'weekly':
            start = today - timedelta(days=today.weekday())
            end = start + timedelta(days=6)
            return start, end
        elif self.active_view == 'monthly':
            start = today.replace(day=1)
            if today.month == 12:
                end = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                end = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
            return start, end

    def load_menu_data(self):
        start, end = self.get_period()
        try:
            db = SessionLocal()
            try:
                menus = db.query(Menu).filter(Menu.date >= start, Menu.date <= end).order_by(Menu.date).all()
                self.current_menus = menus
                self.render_menu_cards(start, end, menus, db)
                self.update_period_label(start, end)
            finally:
                db.close()
        except Exception as e:
            QMessageBox.warning(self, "Hata", f"Menüler alınamadı: {e}")

    def clear_layout(self, layout):
        """Layout içindeki tüm widget'ları temizle"""
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def render_menu_cards(self, start_date, end_date, menus, db):
        """Takvim formatında menü kartlarını oluştur"""
        # Eski kartları temizle
        self.clear_layout(self.menu_layout)
        
        # Görünüme göre grid spacing ayarları
        if self.active_view == 'daily':
            self.menu_layout.setSpacing(20)
            self.menu_layout.setContentsMargins(50, 20, 50, 20)
        elif self.active_view == 'weekly':
            self.menu_layout.setSpacing(0)  # Kartlar birbirine yapışık
            self.menu_layout.setContentsMargins(0, 0, 0, 0)
        else:  # monthly
            self.menu_layout.setSpacing(0)  # Kartlar birbirine yapışık
            self.menu_layout.setContentsMargins(0, 0, 0, 0)
        
        # Menüleri tarih bazında indeksle
        menu_dict = {menu.date: menu for menu in menus}
        
        current_date = start_date
        today = date.today()
        row, col = 0, 0
        visible_day_count = 0
        
        # Grid sütun sayısını görünüme göre ayarla
        if self.active_view == 'daily':
            max_cols = 1
        elif self.active_view == 'weekly':
            max_cols = 7
        else:  # monthly
            max_cols = 7
        
        while current_date <= end_date:
            day_of_week = current_date.weekday()  # 0=Pazartesi, 6=Pazar
            is_weekend = day_of_week >= 5  # Cumartesi ve Pazar
            is_past = current_date < today
            is_today = current_date == today
            
            # Menü varlığını kontrol et
            menu_data = menu_dict.get(current_date)
            items = menu_data.menu_items if menu_data else {}
            has_menu = bool(items.get("Corbasi") or items.get("Ana_Yemek") or 
                          items.get("Yan_Yemek") or items.get("Tatli"))
            
            # Filtre kontrolü
            if hasattr(self, 'hide_weekends_cb') and self.hide_weekends_cb.isChecked() and is_weekend:
                current_date += timedelta(days=1)
                continue
            if hasattr(self, 'hide_empty_days_cb') and self.hide_empty_days_cb.isChecked() and not has_menu:
                current_date += timedelta(days=1)
                continue
            if hasattr(self, 'hide_past_days_cb') and self.hide_past_days_cb.isChecked() and is_past:
                current_date += timedelta(days=1)
                continue
            
            # Mevcut yemek katılım durumunu kontrol et
            attendance = db.query(Attendance).filter_by(user_id=self.user.id, date=current_date).first()
            
            # Menü kartı oluştur
            card = self.create_menu_card(current_date, menu_data, attendance, is_today, is_weekend, is_past, has_menu)
            
            # Grid'e ekle
            self.menu_layout.addWidget(card, row, col)
            visible_day_count += 1
            
            # Sonraki pozisyon
            col += 1
            if col >= max_cols:
                col = 0
                row += 1
            
            current_date += timedelta(days=1)
        
        # Eğer hiç görünür gün yoksa mesaj göster
        if visible_day_count == 0:
            no_data_label = QLabel("Seçilen filtrelere uygun gün bulunamadı.\nFiltre ayarlarını değiştirmeyi deneyin.")
            no_data_label.setAlignment(Qt.AlignCenter)
            no_data_label.setStyleSheet("color: #6b7280; font-size: 16px; padding: 40px;")
            self.menu_layout.addWidget(no_data_label, 0, 0, 1, max_cols)

    def create_menu_card(self, date_obj, menu_data, attendance, is_today, is_weekend, is_past, has_menu):
        """Tek bir menü kartı oluştur"""
        card = QFrame()
        
        # Görünüme göre dinamik boyutlandırma
        if self.active_view == 'weekly':
            card.setMinimumSize(160, 220)  # Haftalık için daha dar
            card.setMaximumSize(200, 260)
        elif self.active_view == 'monthly':
            card.setMinimumSize(140, 180)  # Aylık için en dar
            card.setMaximumSize(180, 220)
        else:  # daily
            card.setMinimumSize(300, 300)  # Günlük için geniş
            card.setMaximumSize(400, 400)
        
        # Kart stilini belirle
        if self.active_view in ['weekly', 'monthly']:
            # Haftalık ve aylık görünümde margin kaldırıldı
            card_style = """
                QFrame {
                    background-color: white;
                    border: 2px solid #e5e7eb;
                    border-radius: 0px;
                    padding: 8px;
                    margin: 0px;
                }
            """
        else:
            # Günlük görünümde eski stil korundu
            card_style = """
                QFrame {
                    background-color: white;
                    border: 2px solid #e5e7eb;
                    border-radius: 10px;
                    padding: 8px;
                    margin: 3px;
                }
            """
        
        # Yemek katılım durumuna göre renklendirme
        if attendance:
            if attendance.will_attend:
                card_style = card_style.replace("border: 2px solid #e5e7eb;", "border: 2px solid #10b981; background-color: #ecfdf5;")
            else:
                card_style = card_style.replace("border: 2px solid #e5e7eb;", "border: 2px solid #ef4444; background-color: #fef2f2;")
        
        # Bugün vurgusu
        if is_today:
            card_style = card_style.replace("border: 2px solid", "border: 3px solid; box-shadow: 0 0 0 2px #3b82f6; border: 2px solid")
        
        # Hafta sonu rengi
        if is_weekend:
            card_style = card_style.replace("background-color: white;", "background-color: #f9fafb;")
        
        card.setStyleSheet(card_style)
        
        layout = QVBoxLayout(card)
        layout.setSpacing(4)  # Elementler arası boşluk azaltıldı
        
        # Tarih başlığı - Görünüme göre ayarlanmış
        days = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
        days_short = ["Pzt", "Sal", "Çar", "Per", "Cum", "Cmt", "Paz"]
        months = ["", "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran",
                 "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
        months_short = ["", "Oca", "Şub", "Mar", "Nis", "May", "Haz", "Tem", "Ağu", "Eyl", "Eki", "Kas", "Ara"]
        
        day_name = days[date_obj.weekday()]
        month_name = months[date_obj.month]
        
        # Görünüme göre tarih formatı
        if self.active_view == 'daily':
            date_title = f"{day_name}\n{date_obj.day} {month_name}"
            title_font_size = "11px"  # Küçültüldü
        elif self.active_view == 'weekly':
            date_title = f"{days_short[date_obj.weekday()]}\n{date_obj.day} {months_short[date_obj.month]}"
            title_font_size = "9px"   # Küçültüldü
        else:  # monthly
            date_title = f"{days_short[date_obj.weekday()]}\n{date_obj.day}"
            title_font_size = "8px"   # Küçültüldü
        
        title_label = QLabel(date_title)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet(f"font-weight: bold; font-size: {title_font_size}; color: #374151; border-bottom: 1px solid #e5e7eb; padding-bottom: 2px; line-height: 1.2;")
        layout.addWidget(title_label)
        
        # Menü içeriği - Görünüme göre ayarlanmış
        if has_menu and menu_data:
            items = menu_data.menu_items
            menu_text = ""
            
            # Görünüme göre karakter limiti ve prefix
            if self.active_view == 'daily':
                char_limit = 40
                prefixes = ["🍲 ", "🍽️ ", "🥗 ", "🍰 "]
                menu_font_size = "14px"  # Büyütüldü
            elif self.active_view == 'weekly':
                char_limit = 15
                prefixes = ["🍲", "🍽️", "🥗", "🍰"]
                menu_font_size = "11px"  # Büyütüldü
            else:  # monthly
                char_limit = 10
                prefixes = ["🍲", "🍽️", "🥗", "🍰"]
                menu_font_size = "10px"  # Büyütüldü
            
            menu_items = [
                (prefixes[0], items.get("Corbasi", "")),
                (prefixes[1], items.get("Ana_Yemek", "")),
                (prefixes[2], items.get("Yan_Yemek", "")),
                (prefixes[3], items.get("Tatli", ""))
            ]
            
            for prefix, text in menu_items:
                if text:
                    if len(text) > char_limit:
                        menu_text += f"{prefix} {text[:char_limit]}...\n"
                    else:
                        menu_text += f"{prefix} {text}\n"
            
            menu_label = QLabel(menu_text.strip())
            menu_label.setStyleSheet(f"color: #4b5563; font-size: {menu_font_size}; line-height: 1.2; padding: 1px 0;")
            menu_label.setWordWrap(True)
            layout.addWidget(menu_label)
        else:
            no_menu_text = "📋 Menü\nYok" if self.active_view != 'daily' else "📋 Menü\nBelirtilmemiş"
            no_menu_font_size = "13px" if self.active_view == 'daily' else "10px"  # Büyütüldü
            no_menu_label = QLabel(no_menu_text)
            no_menu_label.setAlignment(Qt.AlignCenter)
            no_menu_label.setStyleSheet(f"color: #9ca3af; font-size: {no_menu_font_size}; padding: 1px 0;")
            layout.addWidget(no_menu_label)
        
        # layout.addStretch() kaldırıldı - menü içeriği butonlara daha yakın olsun
        
        # Evet/Hayır butonları (sadece geçmiş olmayan, menü olan ve hafta içi günlerde)
        if not is_past and has_menu and not is_weekend:
            button_layout = QHBoxLayout()
            
            # Görünüme göre buton metni ve boyutu
            if self.active_view == 'daily':
                yes_btn = QPushButton("✓ Evet")
                no_btn = QPushButton("✗ Hayır")
                btn_style = "QPushButton { padding: 10px 15px; border-radius: 8px; font-weight: bold; font-size: 13px; min-width: 60px; min-height: 36px; }"
            elif self.active_view == 'weekly':
                yes_btn = QPushButton("✓")
                no_btn = QPushButton("✗")
                btn_style = "QPushButton { padding: 6px 8px; border-radius: 6px; font-weight: bold; font-size: 11px; min-width: 30px; min-height: 24px; }"
            else:  # monthly
                yes_btn = QPushButton("✓")
                no_btn = QPushButton("✗")
                btn_style = "QPushButton { padding: 4px 6px; border-radius: 4px; font-weight: bold; font-size: 10px; min-width: 24px; min-height: 20px; }"
            
            # Mevcut seçime göre stil
            if attendance and attendance.will_attend:
                yes_btn.setStyleSheet(btn_style + "background-color: #10b981; color: white;")
                no_btn.setStyleSheet(btn_style + "background-color: #e5e7eb; color: #6b7280;")
            elif attendance and not attendance.will_attend:
                yes_btn.setStyleSheet(btn_style + "background-color: #e5e7eb; color: #6b7280;")
                no_btn.setStyleSheet(btn_style + "background-color: #ef4444; color: white;")
            else:
                yes_btn.setStyleSheet(btn_style + "background-color: #e5e7eb; color: #6b7280;")
                no_btn.setStyleSheet(btn_style + "background-color: #e5e7eb; color: #6b7280;")
            
            # Buton olayları
            date_str = str(date_obj)
            yes_btn.clicked.connect(lambda: self.handle_attendance_change(date_str, True))
            no_btn.clicked.connect(lambda: self.handle_attendance_change(date_str, False))
            
            button_layout.addWidget(yes_btn)
            button_layout.addWidget(no_btn)
            layout.addLayout(button_layout)
        
        return card

    def update_period_label(self, start, end):
        # Türkçe tarih formatları için dil desteği
        months = {
            1: "Ocak", 2: "Şubat", 3: "Mart", 4: "Nisan", 5: "Mayıs", 6: "Haziran",
            7: "Temmuz", 8: "Ağustos", 9: "Eylül", 10: "Ekim", 11: "Kasım", 12: "Aralık"
        }
        days = {
            0: "Pazartesi", 1: "Salı", 2: "Çarşamba", 3: "Perşembe", 
            4: "Cuma", 5: "Cumartesi", 6: "Pazar"
        }
        
        if self.active_view == "monthly":
            month_name = months.get(start.month, start.strftime("%B"))
            self.period_label.setText(f"{month_name} {start.year}")
        elif self.active_view == "weekly":
            start_month = months.get(start.month, start.strftime("%b"))
            end_month = months.get(end.month, end.strftime("%b"))
            self.period_label.setText(f"{start.day} {start_month} - {end.day} {end_month} {end.year}")
        else:
            day_name = days.get(start.weekday(), start.strftime("%A"))
            month_name = months.get(start.month, start.strftime("%B"))
            self.period_label.setText(f"{day_name}, {start.day} {month_name} {start.year}")

    def handle_attendance_change(self, date_str, will_attend):
        """Yemek katılım durumu değişikliğini anında kaydet"""
        try:
            # String tarihi date nesnesine dönüştür
            if isinstance(date_str, str):
                from datetime import datetime
                date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
            else:
                date_obj = date_str
                
            db = SessionLocal()
            try:
                # Mevcut kaydı kontrol et
                attendance = db.query(Attendance).filter_by(user_id=self.user.id, date=date_obj).first()
                
                if attendance:
                    attendance.will_attend = will_attend
                else:
                    attendance = Attendance(user_id=self.user.id, date=date_obj, will_attend=will_attend)
                    db.add(attendance)
                
                db.commit()
                
                # Tabloyu güncelle
                self.load_menu_data()
                
                # Kullanıcıya geri bildirim
                status = "katılacak" if will_attend else "katılmayacak"
                QMessageBox.information(self, "Başarılı", f"{date_str} tarihi için '{status}' seçimi kaydedildi!")
                
            except Exception as e:
                db.rollback()
                raise e
            finally:
                db.close()
        except Exception as e:
            QMessageBox.warning(self, "Hata", f"Kayıt sırasında hata oluştu: {e}")

    def apply_filters(self):
        """Filtreleme değişikliğinde menüleri yeniden yükle"""
        self.load_menu_data()

    def mesai_tab_ui(self):
        widget = QWidget()
        layout = QHBoxLayout(widget)
        # Sol: Yeni talep
        left = QVBoxLayout()
        left.addWidget(QLabel("Yeni Fazla Mesai Talebi", self))
        self.overtime_date = QDateEdit(QDate.currentDate())
        self.overtime_start = QTimeEdit(QTime(9, 0))
        self.overtime_end = QTimeEdit(QTime(17, 0))
        self.overtime_reason = QTextEdit()
        self.overtime_reason.setPlaceholderText("Yapılan işin açıklaması...")

        left.addWidget(QLabel("Tarih:"))
        left.addWidget(self.overtime_date)
        left.addWidget(QLabel("Başlangıç:"))
        left.addWidget(self.overtime_start)
        left.addWidget(QLabel("Bitiş:"))
        left.addWidget(self.overtime_end)
        left.addWidget(QLabel("Açıklama:"))
        left.addWidget(self.overtime_reason)
        send_btn = QPushButton("Talep Gönder")
        send_btn.clicked.connect(self.send_overtime)
        left.addWidget(send_btn)
        left.addStretch()
        layout.addLayout(left)

        # Sağ: Geçmiş talepler
        right = QVBoxLayout()
        right.addWidget(QLabel("Mevcut Taleplerim", self))
        self.overtime_table = QTableWidget()
        self.overtime_table.setColumnCount(3)
        self.overtime_table.setHorizontalHeaderLabels(["Tarih", "Saatler", "Durum"])
        
        # Sütun boyutlandırma stratejisi
        header = self.overtime_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Tarih
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Saatler
        header.setSectionResizeMode(2, QHeaderView.Stretch)           # Durum
        
        # Tablo boyutlandırma
        self.overtime_table.setMinimumHeight(200)
        self.overtime_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        right.addWidget(self.overtime_table)
        layout.addLayout(right)
        self.load_overtimes()
        return widget

    def send_overtime(self):
        # Girilen verilerin geçerliliğini kontrol et
        if not self.overtime_reason.toPlainText().strip():
            QMessageBox.warning(self, "Uyarı", "Açıklama alanı boş bırakılamaz!")
            return
            
        start_time = self.overtime_start.time().toPython()
        end_time = self.overtime_end.time().toPython()
        
        if start_time >= end_time:
            QMessageBox.warning(self, "Uyarı", "Bitiş saati başlangıç saatinden sonra olmalıdır!")
            return
            
        try:
            db = SessionLocal()
            try:
                new_request = OvertimeRequest(
                    user_id=self.user.id,
                    date=self.overtime_date.date().toPython(),
                    start_time=start_time,
                    end_time=end_time,
                    reason=self.overtime_reason.toPlainText().strip(),
                    department=self.user.department or "",
                    status="Yönetici Onayı Bekliyor"
                )
                db.add(new_request)
                db.commit()
                QMessageBox.information(self, "Talep", "Fazla mesai talebiniz başarıyla gönderildi!")
                self.overtime_reason.clear()
                self.load_overtimes()
            except Exception as e:
                db.rollback()
                raise e
            finally:
                db.close()
        except Exception as e:
            QMessageBox.warning(self, "Hata", f"Talep sırasında hata oluştu: {e}")

    def load_overtimes(self):
        try:
            db = SessionLocal()
            try:
                overt = db.query(OvertimeRequest).filter_by(user_id=self.user.id).order_by(OvertimeRequest.date.desc()).all()
                self.overtime_table.setRowCount(len(overt))
                for i, row in enumerate(overt):
                    self.overtime_table.setItem(i, 0, QTableWidgetItem(str(row.date)))
                    self.overtime_table.setItem(i, 1, QTableWidgetItem(f"{row.start_time} - {row.end_time}"))
                    self.overtime_table.setItem(i, 2, QTableWidgetItem(row.status))
            finally:
                db.close()
        except Exception as e:
            QMessageBox.warning(self, "Hata", f"Fazla mesai talepleri alınamadı: {e}")

    def logout(self):
        if QMessageBox.question(self, "Çıkış", "Çıkış yapmak istiyor musunuz?", QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            # Login ekranına dön
            self.back_to_login_callback()

class ManagerPanel(QWidget):
    def __init__(self, user, back_to_login_callback):
        super().__init__()
        self.user = user
        self.username = user.username
        self.back_to_login_callback = back_to_login_callback
        
        # Mesai talepleri için checkbox group
        self.manager_overtime_checkboxes = []  # Checkbox'ları takip etmek için
        self.manager_selected_overtime_id = None  # Seçili talep ID'si
        
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        header_frame = QFrame()
        header_frame.setObjectName("Header")
        header_frame.setStyleSheet("""
            QFrame#Header {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #667eea, stop:1 #764ba2);
                border: none;
                min-height: 80px;
            }
        """)
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(30, 20, 30, 20)  # Sol, üst, sağ, alt margin
        header_layout.setSpacing(15)  # Widget'lar arası boşluk
        title = QLabel("🏢 Departman Yöneticisi Paneli")
        title.setFont(QFont("Segoe UI", 20, QFont.Bold))
        title.setStyleSheet("color: white; background: transparent;")
        header_layout.addWidget(title)
        header_layout.addStretch()
        user_label = QLabel(f"{self.username}")
        user_label.setStyleSheet("font-weight: 600; color: white; font-size: 17px; background: transparent;")
        logout_btn = QPushButton("🚪 Çıkış")
        logout_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 rgba(239, 68, 68, 0.8), stop: 1 rgba(220, 38, 38, 0.9));
                color: white;
                border: none;
                padding: 12px 20px;
                border-radius: 8px;
                font-size: 14px;
                font-weight: 600;
                min-width: 100px;
                min-height: 20px;
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 rgba(220, 38, 38, 0.9), stop: 1 rgba(185, 28, 28, 1.0));
            }
            QPushButton:pressed {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 rgba(185, 28, 28, 1.0), stop: 1 rgba(153, 27, 27, 1.0));
            }
        """)
        logout_btn.clicked.connect(self.logout)
        header_layout.addWidget(user_label)
        header_layout.addWidget(logout_btn)
        layout.addWidget(header_frame)

        # Ana Tablar
        self.tabs = QTabWidget()
        self.tabs.addTab(self.manager_dashboard_tab_ui(), "📊 Dashboard")
        self.tabs.addTab(self.manager_overtime_tab_ui(), "🕒 Mesai Talepleri")
        self.tabs.addTab(self.manager_reports_tab_ui(), "📋 Ekip Raporları")
        layout.addWidget(self.tabs)

    def manager_dashboard_tab_ui(self):
        # Ana widget
        main_widget = QWidget()
        main_widget.setStyleSheet("""
            QWidget {
                background-color: #f8fafc;
            }
        """)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                background-color: #f1f5f9;
                width: 12px;
                border-radius: 6px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background-color: #667eea;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #5a67d8;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
            }
        """)
        
        # İçerik widget'ı
        widget = QWidget()
        widget.setStyleSheet("""
            QWidget {
                background-color: #f8fafc;
            }
        """)
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(25)
        
        # Başlık
        title_label = QLabel("📊 Ekip Dashboard")
        title_label.setFont(QFont("Segoe UI", 24, QFont.Bold))
        title_label.setStyleSheet("""
            QLabel {
                color: #1e293b;
                padding: 20px;
                background: white;
                border-radius: 15px;
                border: 1px solid #e2e8f0;
                margin-bottom: 10px;
            }
        """)
        layout.addWidget(title_label)
        
        # İstatistik tablosu
        stats_frame = QFrame()
        stats_frame.setStyleSheet("""
            QFrame {
                background: white;
                border-radius: 15px;
                border: 1px solid #e2e8f0;
                padding: 30px;
                margin-bottom: 20px;
            }
        """)
        stats_layout = QVBoxLayout(stats_frame)
        
        stats_title = QLabel("📈 Ekip İstatistikleri")
        stats_title.setFont(QFont("Segoe UI", 18, QFont.Bold))
        stats_title.setStyleSheet("color: #1e293b; margin-bottom: 15px;")
        stats_layout.addWidget(stats_title)
        
        # Dashboard tablosu
        self.manager_dashboard_table = QTableWidget()
        self.manager_dashboard_table.setColumnCount(2)
        self.manager_dashboard_table.setHorizontalHeaderLabels(["Metric", "Value"])
        self.manager_dashboard_table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                gridline-color: #f1f5f9;
                font-size: 14px;
                selection-background-color: transparent;
            }
            QTableWidget::item {
                padding: 8px 6px;
                border-bottom: 1px solid #f1f5f9;
                color: #374151;
            }
            QHeaderView::section {
                background-color: #f8fafc;
                color: #374151;
                padding: 8px 6px;
                border: none;
                border-bottom: 2px solid #e5e7eb;
                font-weight: 600;
                font-size: 13px;
            }
        """)
        
        # Tablo ayarları
        self.manager_dashboard_table.setSelectionMode(QAbstractItemView.NoSelection)
        self.manager_dashboard_table.setFocusPolicy(Qt.NoFocus)
        self.manager_dashboard_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.manager_dashboard_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        
        # Tablo boyutunu daha esnek hale getir
        self.manager_dashboard_table.setMinimumHeight(120)
        self.manager_dashboard_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        
        # Dikey header'ı gizle
        self.manager_dashboard_table.verticalHeader().setVisible(False)
        
        stats_layout.addWidget(self.manager_dashboard_table)
        layout.addWidget(stats_frame)
        
        layout.addStretch()
        
        # İçerik widget'ını scroll area'ya ekle
        scroll_area.setWidget(widget)
        
        # Scroll area'yı main layout'a ekle
        main_layout.addWidget(scroll_area)
        
        # Dashboard verilerini yükle
        QTimer.singleShot(200, self.load_manager_dashboard)
        
        return main_widget

    def load_manager_dashboard(self):
        try:
            db = SessionLocal()
            try:
                # Ekip üyelerini al
                team_members = db.query(User).filter_by(manager_id=self.user.id).all()
                team_count = len(team_members)
                
                # Bugünkü yemek katılım
                today = date.today()
                attending_today = db.query(Attendance).filter(
                    Attendance.date == today,
                    Attendance.user_id.in_([u.id for u in team_members]),
                    Attendance.will_attend == True
                ).count()
                
                # Bekleyen mesai talepleri
                pending_overtime = db.query(OvertimeRequest).filter(
                    OvertimeRequest.user_id.in_([u.id for u in team_members]),
                    OvertimeRequest.status == "Yönetici Onayı Bekliyor"
                ).count()
                
                # Tabloya verileri ekle
                data = [
                    ("👥 Toplam Ekip Üyesi", str(team_count)),
                    ("🍽️ Yemek Katılımı", str(attending_today)),
                    ("🕒 Bekleyen Mesai Talepleri", str(pending_overtime))
                ]
                
                self.manager_dashboard_table.setRowCount(len(data))
                for i, (metric, value) in enumerate(data):
                    metric_item = QTableWidgetItem(metric)
                    value_item = QTableWidgetItem(value)
                    value_item.setTextAlignment(Qt.AlignCenter)
                    
                    self.manager_dashboard_table.setItem(i, 0, metric_item)
                    self.manager_dashboard_table.setItem(i, 1, value_item)
                    self.manager_dashboard_table.setRowHeight(i, 35)
                    
            finally:
                db.close()
        except Exception as e:
            QMessageBox.warning(self, "Hata", f"Dashboard verileri yüklenirken hata: {e}")

    def manager_overtime_tab_ui(self):
        return self.overtime_tab_ui()  # Mevcut overtime tab'ını kullan

    def manager_reports_tab_ui(self):
        return self.reports_tab_ui()  # Mevcut reports tab'ını kullan

    # Mevcut overtime ve reports fonksiyonlarını kopyala
    def overtime_tab_ui(self):
        # Ana widget
        main_widget = QWidget()
        main_widget.setStyleSheet("""
            QWidget {
                background-color: #f8fafc;
            }
        """)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Scroll area oluştur
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                background-color: #f1f5f9;
                width: 12px;
                border-radius: 6px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background-color: #667eea;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #5a67d8;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
            }
            QScrollBar:horizontal {
                background-color: #f1f5f9;
                height: 12px;
                border-radius: 6px;
                margin: 0px;
            }
            QScrollBar::handle:horizontal {
                background-color: #667eea;
                border-radius: 6px;
                min-width: 20px;
            }
            QScrollBar::handle:horizontal:hover {
                background-color: #5a67d8;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                border: none;
                background: none;
            }
        """)
        
        # İçerik widget'ı
        widget = QWidget()
        widget.setStyleSheet("""
            QWidget {
                background-color: #f8fafc;
            }
        """)
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(25)
        
        # Ana container
        main_container = QFrame()
        main_container.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 15px;
                border: 1px solid #e2e8f0;
                padding: 30px;
            }
        """)
        main_container_layout = QVBoxLayout(main_container)
        main_container_layout.setSpacing(25)
        
        # Başlık
        title_label = QLabel("🕒 Ekip Fazla Mesai Talepleri")
        title_label.setFont(QFont("Segoe UI", 24, QFont.Bold))
        title_label.setStyleSheet("""
            QLabel {
                color: #1e293b;
                padding: 0px 0px 15px 0px;
                border-bottom: 3px solid #667eea;
                margin-bottom: 20px;
            }
        """)
        main_container_layout.addWidget(title_label)
        
        # Filtre container
        filter_container = QFrame()
        filter_container.setStyleSheet("""
            QFrame {
                background-color: #f1f5f9;
                border-radius: 12px;
                padding: 20px;
                border: 1px solid #e2e8f0;
            }
        """)
        filter_layout = QHBoxLayout(filter_container)
        filter_layout.setContentsMargins(20, 15, 20, 15)
        filter_layout.setSpacing(20)
        
        # Durum filtresi
        status_label = QLabel("📊 Duruma Göre:")
        status_label.setFont(QFont("Segoe UI", 14, QFont.Weight.Medium))
        status_label.setStyleSheet("QLabel { color: #475569; font-weight: 600; }")
        
        self.manager_overtime_status_filter = QComboBox()
        self.manager_overtime_status_filter.addItems([
            "Tümü",
            "Yönetici Onayı Bekliyor", 
            "İK Onayı Bekliyor",
            "Onaylandı",
            "Reddedildi"
        ])
        self.manager_overtime_status_filter.setStyleSheet("""
            QComboBox {
                padding: 12px 15px;
                border: 2px solid #cbd5e1;
                border-radius: 10px;
                font-size: 14px;
                min-width: 180px;
                background-color: white;
                color: #1e293b;
                font-weight: 500;
            }
            QComboBox:focus {
                border-color: #667eea;
                background-color: #fefefe;
            }
            QComboBox:hover {
                border-color: #94a3b8;
            }
            QComboBox::drop-down {
                border: none;
                width: 30px;
                background: transparent;
            }
            QComboBox::down-arrow {
                image: none;
                border: none;
                width: 0px;
            }
        """)
        
        # Filtrele butonu
        filter_btn = QPushButton("🔍 Filtrele")
        filter_btn.setFont(QFont("Segoe UI", 14, QFont.Bold))
        filter_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 #667eea, stop:1 #764ba2);
                color: white;
                border: none;
                padding: 12px 25px;
                border-radius: 12px;
                font-size: 14px;
                font-weight: 700;
                min-width: 140px;
                text-align: center;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 #5a67d8, stop:1 #6b46a8);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 #4c51bf, stop:1 #553c9a);
            }
        """)
        filter_btn.clicked.connect(self.load_manager_overtime_requests)
        
        filter_layout.addWidget(status_label)
        filter_layout.addWidget(self.manager_overtime_status_filter)
        filter_layout.addWidget(filter_btn)
        filter_layout.addStretch()
        
        main_container_layout.addWidget(filter_container)
        
        # Tablo container
        table_container = QFrame()
        table_container.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 15px;
                border: 1px solid #e2e8f0;
                padding: 25px;
                margin-top: 10px;
            }
        """)
        table_layout = QVBoxLayout(table_container)
        table_layout.setSpacing(20)
        
        # Tablo başlığı
        table_title = QLabel("📋 Ekip Mesai Talepleri")
        table_title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        table_title.setStyleSheet("""
            QLabel {
                color: #1e293b;
                padding: 15px;
                background-color: #f8fafc;
                border-radius: 10px;
                border-left: 4px solid #667eea;
                margin-bottom: 15px;
            }
        """)
        table_layout.addWidget(table_title)
        
        # Tablo
        self.manager_overtime_table = QTableWidget()
        self.manager_overtime_table.setColumnCount(8)  # Seç sütunu eklendi
        self.manager_overtime_table.setHorizontalHeaderLabels([
            "Seç", "ID", "Personel", "Departman", "Tarih", "Saatler", "Açıklama", "Durum"
        ])
        self.manager_overtime_table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                gridline-color: #f1f5f9;
                font-size: 14px;
                selection-background-color: transparent;
            }
            QTableWidget::item {
                padding: 12px 8px;
                border-bottom: 1px solid #f1f5f9;
                color: #374151;
            }
            QTableWidget::item:selected {
                background-color: #f3f4f6;
                color: #1f2937;
            }
            QHeaderView::section {
                background-color: #f8fafc;
                color: #374151;
                padding: 12px 8px;
                border: none;
                border-bottom: 2px solid #e5e7eb;
                font-weight: 600;
                font-size: 14px;
            }
        """)
        
        # Sütun genişlikleri
        header = self.manager_overtime_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Fixed)             # Seç
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # ID
        header.setSectionResizeMode(2, QHeaderView.Stretch)           # Personel
        header.setSectionResizeMode(3, QHeaderView.Stretch)           # Departman
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Tarih
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # Saatler
        header.setSectionResizeMode(6, QHeaderView.Stretch)           # Açıklama
        header.setSectionResizeMode(7, QHeaderView.ResizeToContents)  # Durum
        
        # Seç sütunu genişliği
        self.manager_overtime_table.setColumnWidth(0, 50)
        
        # Tabloya seçim politikası
        self.manager_overtime_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.manager_overtime_table.setSelectionMode(QAbstractItemView.SingleSelection)
        
        table_layout.addWidget(self.manager_overtime_table)
        
        # Buton container
        button_container = QFrame()
        button_container.setStyleSheet("QFrame { background: transparent; }")
        button_layout = QHBoxLayout(button_container)
        button_layout.setSpacing(15)
        button_layout.setContentsMargins(0, 15, 0, 0)
        
        # Onayla butonu
        approve_btn = QPushButton("✅ Seçili Talebi Onayla")
        approve_btn.setFont(QFont("Segoe UI", 14, QFont.Bold))
        approve_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 #10b981, stop:1 #059669);
                color: white;
                border: none;
                padding: 12px 25px;
                border-radius: 12px;
                font-size: 14px;
                font-weight: 700;
                min-width: 180px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 #059669, stop:1 #047857);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 #047857, stop:1 #065f46);
            }
        """)
        approve_btn.clicked.connect(lambda: self.handle_manager_overtime_action("Onaylandı"))
        
        # Reddet butonu
        reject_btn = QPushButton("❌ Seçili Talebi Reddet")
        reject_btn.setFont(QFont("Segoe UI", 14, QFont.Bold))
        reject_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 #ef4444, stop:1 #dc2626);
                color: white;
                border: none;
                padding: 12px 25px;
                border-radius: 12px;
                font-size: 14px;
                font-weight: 700;
                min-width: 180px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 #dc2626, stop:1 #b91c1c);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 #b91c1c, stop:1 #991b1b);
            }
        """)
        reject_btn.clicked.connect(lambda: self.handle_manager_overtime_action("Reddedildi"))
        
        button_layout.addWidget(approve_btn)
        button_layout.addWidget(reject_btn)
        button_layout.addStretch()
        
        table_layout.addWidget(button_container)
        main_container_layout.addWidget(table_container)
        
        layout.addWidget(main_container)
        layout.addStretch()
        
        # İçerik widget'ını scroll area'ya ekle
        scroll_area.setWidget(widget)
        
        # Scroll area'yı main layout'a ekle
        main_layout.addWidget(scroll_area)
        
        # Sayfa açılır açılmaz talepleri yükle
        QTimer.singleShot(200, self.load_manager_overtime_requests)
        
        return main_widget

    def load_manager_overtime_requests(self):
        try:
            # Önceki checkbox'ları temizle
            self.manager_overtime_checkboxes.clear()
            self.manager_selected_overtime_id = None
            
            db = SessionLocal()
            try:
                # Filtreye göre durum belirle
                status_filter = self.manager_overtime_status_filter.currentText()
                
                # Yöneticinin ekibindeki kullanıcıların id'leri
                sub_ids = [u.id for u in db.query(User).filter_by(manager_id=self.user.id).all()]
                if not sub_ids:
                    self.manager_overtime_table.setRowCount(0)
                    return
                query = db.query(OvertimeRequest).filter(OvertimeRequest.user_id.in_(sub_ids))
                
                # Durum filtresini uygula
                if status_filter != "Tümü":
                    query = query.filter(OvertimeRequest.status == status_filter)
                    
                overt = query.order_by(OvertimeRequest.date.desc()).all()
                        
                self.manager_overtime_table.setRowCount(len(overt))
                for i, row in enumerate(overt):
                    user = db.query(User).filter_by(id=row.user_id).first()
                    
                    # Checkbox (Seç sütunu)
                    checkbox = QCheckBox()
                    checkbox.setStyleSheet("""
                        QCheckBox {
                            spacing: 5px;
                            font-size: 14px;
                        }
                        QCheckBox::indicator {
                            width: 16px;
                            height: 16px;
                            border: 2px solid #d1d5db;
                            border-radius: 3px;
                            background-color: white;
                        }
                        QCheckBox::indicator:checked {
                            background-color: #667eea;
                            border-color: #667eea;
                            image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iMTIiIHZpZXdCb3g9IjAgMCAxMiAxMiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTEwIDNMNC41IDguNUwyIDYiIHN0cm9rZT0id2hpdGUiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIi8+Cjwvc3ZnPgo=);
                        }
                        QCheckBox::indicator:hover {
                            border-color: #667eea;
                        }
                    """)
                    
                    # Checkbox'a veri ekle (talep ID'si)
                    checkbox.setProperty("overtime_id", row.id)
                    checkbox.clicked.connect(self.on_manager_checkbox_clicked)
                    
                    # Checkbox'u listeye ekle
                    self.manager_overtime_checkboxes.append(checkbox)
                    
                    # Checkbox'u tabloya ekle
                    checkbox_widget = QWidget()
                    checkbox_layout = QHBoxLayout(checkbox_widget)
                    checkbox_layout.addWidget(checkbox)
                    checkbox_layout.setAlignment(Qt.AlignCenter)
                    checkbox_layout.setContentsMargins(0, 0, 0, 0)
                    self.manager_overtime_table.setCellWidget(i, 0, checkbox_widget)
                    
                    # ID
                    id_item = QTableWidgetItem(str(row.id))
                    id_item.setTextAlignment(Qt.AlignCenter)
                    self.manager_overtime_table.setItem(i, 1, id_item)
                    
                    # Personel
                    user_item = QTableWidgetItem(user.username if user else "Bilinmeyen")
                    self.manager_overtime_table.setItem(i, 2, user_item)
                    
                    # Departman
                    dept_item = QTableWidgetItem(user.department if user and user.department else "Belirtilmemiş")
                    self.manager_overtime_table.setItem(i, 3, dept_item)
                    
                    # Tarih
                    date_item = QTableWidgetItem(str(row.date))
                    date_item.setTextAlignment(Qt.AlignCenter)
                    self.manager_overtime_table.setItem(i, 4, date_item)
                    
                    # Saatler
                    time_item = QTableWidgetItem(f"{row.start_time} - {row.end_time}")
                    time_item.setTextAlignment(Qt.AlignCenter)
                    self.manager_overtime_table.setItem(i, 5, time_item)
                    
                    # Açıklama
                    desc_item = QTableWidgetItem(row.reason or "Açıklama yok")
                    self.manager_overtime_table.setItem(i, 6, desc_item)
                    
                    # Durum - Renkli badge
                    status_item = QTableWidgetItem(row.status)
                    status_item.setTextAlignment(Qt.AlignCenter)
                    
                    # Duruma göre renk
                    if row.status == "Yönetici Onayı Bekliyor":
                        status_item.setBackground(QColor("#fef3c7"))  # Sarı arka plan
                        status_item.setForeground(QColor("#92400e"))  # Kahve yazı
                    elif row.status == "İK Onayı Bekliyor":
                        status_item.setBackground(QColor("#dbeafe"))  # Mavi arka plan
                        status_item.setForeground(QColor("#1e40af"))  # Mavi yazı
                    elif row.status == "Onaylandı":
                        status_item.setBackground(QColor("#d1fae5"))  # Yeşil arka plan
                        status_item.setForeground(QColor("#065f46"))  # Koyu yeşil yazı
                    elif row.status == "Reddedildi":
                        status_item.setBackground(QColor("#fee2e2"))  # Kırmızı arka plan
                        status_item.setForeground(QColor("#991b1b"))  # Koyu kırmızı yazı
                    
                    self.manager_overtime_table.setItem(i, 7, status_item)
                    
                # Satır yüksekliklerini ayarla
                for i in range(len(overt)):
                    self.manager_overtime_table.setRowHeight(i, 50)
                    
            finally:
                db.close()
        except Exception as e:
            QMessageBox.warning(self, "Hata", f"Mesai talepleri alınamadı: {e}")

    def on_manager_checkbox_clicked(self):
        """Manager checkbox tıklandığında çalışır - sadece bir tane seçili olmasını sağlar"""
        sender = self.sender()  # Tıklanan checkbox
        overtime_id = sender.property("overtime_id")
        
        if sender.isChecked():
            # Bu checkbox seçildiyse, diğerlerini kapat
            for cb in self.manager_overtime_checkboxes:
                if cb != sender and cb.isChecked():
                    cb.setChecked(False)
            
            self.manager_selected_overtime_id = overtime_id
        else:
            # Checkbox kapatıldıysa, seçili ID'yi temizle
            self.manager_selected_overtime_id = None

    def handle_manager_overtime_action(self, status):
        # Checkbox'tan seçilen ID'yi kullan
        if not self.manager_selected_overtime_id:
            QMessageBox.warning(self, "Uyarı", "Lütfen işlem yapmak istediğiniz talebi seçin!")
            return
            
        try:
            # Seçili talep bilgilerini al
            selected_user_name = None
            selected_date_str = None
            
            # Tabloda seçili talebi bul
            for i in range(self.manager_overtime_table.rowCount()):
                id_item = self.manager_overtime_table.item(i, 1)  # ID sütunu şimdi 1. sütun
                if id_item and int(id_item.text()) == self.manager_selected_overtime_id:
                    selected_user_name = self.manager_overtime_table.item(i, 2).text()  # Personel sütunu
                    selected_date_str = self.manager_overtime_table.item(i, 4).text()   # Tarih sütunu
                    break
            
            if not selected_user_name:
                QMessageBox.warning(self, "Hata", "Seçili talep bilgileri alınamadı!")
                return
            
            # Onay iste
            reply = QMessageBox.question(
                self, 
                "Onay", 
                f"{selected_user_name} kullanıcısının {selected_date_str} tarihli fazla mesai talebini '{status}' yapmak istediğinizden emin misiniz?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply != QMessageBox.Yes:
                return
            
            db = SessionLocal()
            try:
                req = db.query(OvertimeRequest).filter_by(id=self.manager_selected_overtime_id).first()
                if req:
                    if req.status not in ["Yönetici Onayı Bekliyor", "İK Onayı Bekliyor"]:
                        QMessageBox.warning(self, "Uyarı", "Bu talep zaten işlem görmüş!")
                        return
                    
                    # Yönetici ise bir sonraki aşamaya geçir
                    if status == "Onaylandı" and req.status == "Yönetici Onayı Bekliyor":
                        req.status = "İK Onayı Bekliyor"
                        success_msg = f"Talep İK onayına gönderildi."
                    else:
                        req.status = status
                        success_msg = f"Talep '{status}' olarak güncellendi."
                    
                    db.commit()
                    QMessageBox.information(self, "✅ Başarılı", success_msg)
                    
                    # Seçimi temizle ve tabloyu yeniden yükle
                    self.manager_selected_overtime_id = None
                    self.load_manager_overtime_requests()
                else:
                    QMessageBox.warning(self, "Hata", "Talep bulunamadı!")
            except Exception as e:
                db.rollback()
                raise e
            finally:
                db.close()
        except Exception as e:
            QMessageBox.warning(self, "Hata", f"Talep güncellenirken hata: {e}")

    def reports_tab_ui(self):
        # Ana widget
        main_widget = QWidget()
        main_widget.setStyleSheet("""
            QWidget {
                background-color: #f8fafc;
            }
        """)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Scroll area oluştur
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                background-color: #f1f5f9;
                width: 12px;
                border-radius: 6px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background-color: #667eea;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #5a67d8;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
            }
            QScrollBar:horizontal {
                background-color: #f1f5f9;
                height: 12px;
                border-radius: 6px;
                margin: 0px;
            }
            QScrollBar::handle:horizontal {
                background-color: #667eea;
                border-radius: 6px;
                min-width: 20px;
            }
            QScrollBar::handle:horizontal:hover {
                background-color: #5a67d8;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                border: none;
                background: none;
            }
        """)
        
        # İçerik widget'ı
        widget = QWidget()
        widget.setStyleSheet("""
            QWidget {
                background-color: #f8fafc;
            }
        """)
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(25)
        
        # Ana container
        main_container = QFrame()
        main_container.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 15px;
                border: 1px solid #e2e8f0;
                padding: 30px;
            }
        """)
        main_container_layout = QVBoxLayout(main_container)
        main_container_layout.setSpacing(25)
        
        # Başlık
        title_label = QLabel("📋 Ekip Yemek Katılım Raporları")
        title_label.setFont(QFont("Segoe UI", 24, QFont.Bold))
        title_label.setStyleSheet("""
            QLabel {
                color: #1e293b;
                padding: 0px 0px 15px 0px;
                border-bottom: 3px solid #667eea;
                margin-bottom: 20px;
            }
        """)
        main_container_layout.addWidget(title_label)
        
        # Tarih seçimi ve rapor butonu container
        date_container = QFrame()
        date_container.setStyleSheet("""
            QFrame {
                background-color: #f1f5f9;
                border-radius: 12px;
                padding: 20px;
                border: 1px solid #e2e8f0;
            }
        """)
        date_layout = QHBoxLayout(date_container)
        date_layout.setContentsMargins(20, 15, 20, 15)
        date_layout.setSpacing(20)
        
        date_label = QLabel("📅 Rapor Tarihi:")
        date_label.setFont(QFont("Segoe UI", 14, QFont.Weight.Medium))
        date_label.setStyleSheet("""
            QLabel {
                color: #475569;
                font-weight: 600;
            }
        """)
        
        self.manager_report_date = QDateEdit()
        self.manager_report_date.setDate(QDate.currentDate())
        self.manager_report_date.setCalendarPopup(True)
        self.manager_report_date.setStyleSheet("""
            QDateEdit {
                padding: 12px 15px;
                border: 2px solid #cbd5e1;
                border-radius: 10px;
                font-size: 14px;
                min-width: 180px;
                background-color: white;
                color: #1e293b;
                font-weight: 500;
            }
            QDateEdit:focus {
                border-color: #667eea;
                background-color: #fefefe;
            }
            QDateEdit:hover {
                border-color: #94a3b8;
            }
            QDateEdit::drop-down {
                border: none;
                width: 30px;
            }
            QDateEdit::down-arrow {
                image: none;
                border: none;
                width: 0px;
            }
        """)
        
        self.show_manager_report_btn = QPushButton("📊 Ekip Raporu Göster")
        self.show_manager_report_btn.setFont(QFont("Segoe UI", 14, QFont.Bold))
        self.show_manager_report_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 #667eea, stop:1 #764ba2);
                color: white;
                border: none;
                padding: 12px 25px;
                border-radius: 12px;
                font-size: 14px;
                font-weight: 700;
                min-width: 160px;
                text-align: center;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 #5a67d8, stop:1 #6b46a8);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 #4c51bf, stop:1 #553c9a);
            }
        """)
        self.show_manager_report_btn.clicked.connect(self.load_manager_attendance_report)
        
        date_layout.addWidget(date_label)
        date_layout.addWidget(self.manager_report_date)
        date_layout.addWidget(self.show_manager_report_btn)
        date_layout.addStretch()
        
        main_container_layout.addWidget(date_container)
        
        # Rapor sonuçları - her zaman görünür
        self.manager_report_results = QFrame()
        self.manager_report_results.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 15px;
                border: 1px solid #e2e8f0;
                padding: 25px;
                margin-top: 10px;
            }
        """)
        results_layout = QVBoxLayout(self.manager_report_results)
        results_layout.setSpacing(20)
        
        # Rapor başlığı
        self.manager_report_title_label = QLabel("📊 Tarih seçip 'Ekip Raporu Göster' butonuna basın")
        self.manager_report_title_label.setFont(QFont("Segoe UI", 16, QFont.Bold))
        self.manager_report_title_label.setStyleSheet("""
            QLabel {
                color: #1e293b;
                padding: 15px;
                background-color: #f8fafc;
                border-radius: 10px;
                border-left: 4px solid #667eea;
                margin-bottom: 15px;
            }
        """)
        results_layout.addWidget(self.manager_report_title_label)
        
        # İki sütunlu düzen (Gelecekler / Gelmeyecekler)
        columns_container = QFrame()
        columns_container.setStyleSheet("QFrame { background: transparent; }")
        columns_layout = QHBoxLayout(columns_container)
        columns_layout.setSpacing(20)
        columns_layout.setContentsMargins(0, 0, 0, 0)
        
        # Sol sütun - Gelecek personeller
        attending_frame = QFrame()
        attending_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #f0fdf4, stop:1 #dcfce7);
                border-radius: 15px;
                border: 2px solid #bbf7d0;
                padding: 15px;
                min-height: 400px;
            }
        """)
        attending_layout = QVBoxLayout(attending_frame)
        attending_layout.setContentsMargins(10, 10, 10, 10)
        attending_layout.setSpacing(10)
        
        self.manager_attending_title = QLabel("✅ Gelecek Ekip Üyeleri (0)")
        self.manager_attending_title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        self.manager_attending_title.setStyleSheet("""
            QLabel {
                color: #166534;
                padding: 8px 12px;
                background-color: rgba(220, 252, 231, 0.8);
                border-radius: 6px;
                border: 1px solid #bbf7d0;
                font-weight: bold;
                min-height: 20px;
            }
        """)
        self.manager_attending_title.setAlignment(Qt.AlignCenter)
        attending_layout.addWidget(self.manager_attending_title)
        
        self.manager_attending_list = QListWidget()
        self.manager_attending_list.setStyleSheet("""
            QListWidget {
                border: none;
                background-color: rgba(255, 255, 255, 0.9);
                border-radius: 8px;
                font-size: 13px;
                padding: 8px;
                color: #1f2937;
                outline: none;
            }
            QListWidget::item {
                padding: 6px 10px;
                margin: 1px 0px;
                border-radius: 4px;
                color: #1f2937;
                font-weight: 500;
                background-color: transparent;
                border: none;
                outline: none;
            }
            QListWidget::item:hover {
                background-color: rgba(34, 197, 94, 0.1);
            }
            QListWidget::item:selected {
                background-color: rgba(34, 197, 94, 0.15);
                border: none;
                outline: none;
            }
        """)
        self.manager_attending_list.setMinimumHeight(250)
        self.manager_attending_list.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        attending_layout.addWidget(self.manager_attending_list)
        
        # Sağ sütun - Gelmeyecek personeller
        not_attending_frame = QFrame()
        not_attending_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #fef2f2, stop:1 #fee2e2);
                border-radius: 15px;
                border: 2px solid #fecaca;
                padding: 15px;
                min-height: 400px;
            }
        """)
        not_attending_layout = QVBoxLayout(not_attending_frame)
        not_attending_layout.setContentsMargins(10, 10, 10, 10)
        not_attending_layout.setSpacing(10)
        
        self.manager_not_attending_title = QLabel("❌ Gelmeyecek Ekip Üyeleri (0)")
        self.manager_not_attending_title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        self.manager_not_attending_title.setStyleSheet("""
            QLabel {
                color: #dc2626;
                padding: 8px 12px;
                background-color: rgba(254, 226, 226, 0.8);
                border-radius: 6px;
                border: 1px solid #fecaca;
                font-weight: bold;
                min-height: 20px;
            }
        """)
        self.manager_not_attending_title.setAlignment(Qt.AlignCenter)
        not_attending_layout.addWidget(self.manager_not_attending_title)
        
        self.manager_not_attending_list = QListWidget()
        self.manager_not_attending_list.setStyleSheet("""
            QListWidget {
                border: none;
                background-color: rgba(255, 255, 255, 0.9);
                border-radius: 8px;
                font-size: 13px;
                padding: 8px;
                color: #1f2937;
                outline: none;
            }
            QListWidget::item {
                padding: 6px 10px;
                margin: 1px 0px;
                border-radius: 4px;
                color: #1f2937;
                font-weight: 500;
                background-color: transparent;
                border: none;
                outline: none;
            }
            QListWidget::item:hover {
                background-color: rgba(239, 68, 68, 0.1);
            }
            QListWidget::item:selected {
                background-color: rgba(239, 68, 68, 0.15);
                border: none;
                outline: none;
            }
        """)
        self.manager_not_attending_list.setMinimumHeight(250)
        self.manager_not_attending_list.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        not_attending_layout.addWidget(self.manager_not_attending_list)
        
        columns_layout.addWidget(attending_frame)
        columns_layout.addWidget(not_attending_frame)
        results_layout.addWidget(columns_container)
        
        main_container_layout.addWidget(self.manager_report_results)
        main_container_layout.addStretch()
        
        layout.addWidget(main_container)
        layout.addStretch()
        
        # İçerik widget'ını scroll area'ya ekle
        scroll_area.setWidget(widget)
        
        # Scroll area'yı main layout'a ekle
        main_layout.addWidget(scroll_area)
        
        # Sayfa açılır açılmaz bugünkü raporu otomatik yükle
        QTimer.singleShot(200, self.load_manager_attendance_report)
        
        return main_widget

    def load_manager_attendance_report(self):
        try:
            selected_date = self.manager_report_date.date().toPython()
            db = SessionLocal()
            try:
                # Ekip üyelerini al
                team_members = db.query(User).filter_by(manager_id=self.user.id).all()
                
                if not team_members:
                    self.manager_report_title_label.setText("📊 Henüz ekip üyeniz bulunmuyor")
                    self.manager_attending_list.clear()
                    self.manager_not_attending_list.clear()
                    self.manager_attending_title.setText("✅ Gelecek Ekip Üyeleri (0)")
                    self.manager_not_attending_title.setText("❌ Gelmeyecek Ekip Üyeleri (0)")
                    return
                
                team_member_ids = [u.id for u in team_members]
                
                # O tarih için yemek katılım verilerini al
                attendances = db.query(Attendance).filter(
                    Attendance.date == selected_date,
                    Attendance.user_id.in_(team_member_ids)
                ).all()
                
                # Listeleri temizle
                self.manager_attending_list.clear()
                self.manager_not_attending_list.clear()
                
                attending_count = 0
                not_attending_count = 0
                
                # Kullanıcı bazında kontrol et
                for user in team_members:
                    attendance = next((a for a in attendances if a.user_id == user.id), None)
                    
                    if attendance and attendance.will_attend == True:
                        self.manager_attending_list.addItem(f"👤 {user.username}")
                        attending_count += 1
                    else:
                        self.manager_not_attending_list.addItem(f"👤 {user.username}")
                        not_attending_count += 1
                
                # Başlıkları güncelle
                self.manager_report_title_label.setText(f"📊 {selected_date.strftime('%d.%m.%Y')} Tarihli Ekip Yemek Katılım Raporu")
                self.manager_attending_title.setText(f"✅ Gelecek Ekip Üyeleri ({attending_count})")
                self.manager_not_attending_title.setText(f"❌ Gelmeyecek Ekip Üyeleri ({not_attending_count})")
                
            finally:
                db.close()
        except Exception as e:
            QMessageBox.warning(self, "Hata", f"Rapor yüklenirken hata: {e}")

    def logout(self):
        if QMessageBox.question(self, "Çıkış", "Çıkış yapmak istiyor musunuz?", QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            # Login ekranına dön
            self.back_to_login_callback()

class AdminPanel(QWidget):
    def __init__(self, user, back_to_login_callback):
        super().__init__()
        self.user = user
        self.username = user.username
        self.back_to_login_callback = back_to_login_callback
        
        # Mesai talepleri için checkbox group
        self.overtime_checkboxes = []  # Checkbox'ları takip etmek için
        self.selected_overtime_id = None  # Seçili talep ID'si
        
        self.init_ui()

    def init_ui(self):
        # Ana dış layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header (üst bar)
        header_frame = QFrame()
        header_frame.setObjectName("Header")
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(30, 20, 30, 20)  # Sol, üst, sağ, alt margin
        header_layout.setSpacing(15)  # Widget'lar arası boşluk
        title = QLabel("👨‍💼 Admin Paneli")
        title.setFont(QFont("Segoe UI", 20, QFont.Bold))
        title.setStyleSheet("color: white; background: transparent;")
        header_layout.addWidget(title)
        header_layout.addStretch()
        user_label = QLabel(f"{self.username}")
        user_label.setStyleSheet("font-weight: 600; color: white; font-size: 17px; background: transparent;")
        logout_btn = QPushButton("🚪 Çıkış")
        logout_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 rgba(239, 68, 68, 0.8), stop: 1 rgba(220, 38, 38, 0.9));
                color: white;
                border: none;
                padding: 12px 20px;
                border-radius: 8px;
                font-size: 14px;
                font-weight: 600;
                min-width: 80px;
                min-height: 20px;
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 rgba(220, 38, 38, 0.9), stop: 1 rgba(185, 28, 28, 1.0));
            }
            QPushButton:pressed {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 rgba(185, 28, 28, 1.0), stop: 1 rgba(153, 27, 27, 1.0));
            }
        """)
        logout_btn.clicked.connect(self.logout)
        header_layout.addWidget(user_label)
        header_layout.addWidget(logout_btn)
        layout.addWidget(header_frame)

        # Ana Tablar
        self.tabs = QTabWidget()
        self.tabs.addTab(self.dashboard_tab_ui(), "📊 Dashboard")
        self.tabs.addTab(self.menu_plan_tab_ui(), "📅 Menü Planlama")
        self.tabs.addTab(self.overtime_tab_ui(), "🕒 Mesai Talepleri")
        self.tabs.addTab(self.user_management_tab_ui(), "👥 Kullanıcı Yönetimi")
        self.tabs.addTab(self.reports_tab_ui(), "📋 Yemek Katılım Raporları")
        
        layout.addWidget(self.tabs)
    def user_management_tab_ui(self):
        # Ana scroll widget'ı oluştur
        main_widget = QWidget()
        main_widget.setStyleSheet("QWidget { background-color: #f8fafc; }")
        
        # Scroll area oluştur
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: #f8fafc;
                border: none;
            }
            QScrollBar:vertical {
                background-color: #f1f5f9;
                width: 12px;
                border-radius: 6px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background-color: #cbd5e1;
                border-radius: 6px;
                min-height: 20px;
                margin: 2px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #94a3b8;
            }
            QScrollBar::handle:vertical:pressed {
                background-color: #64748b;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)
        
        # Ana layout
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll_area)
        
        # İçerik widget'ı
        widget = QWidget()
        widget.setStyleSheet("""
            QWidget {
                background-color: #f8fafc;
            }
        """)
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(25)
        
        # Ana container
        main_container = QFrame()
        main_container.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 15px;
                border: 1px solid #e2e8f0;
                padding: 30px;
            }
        """)
        container_layout = QVBoxLayout(main_container)
        container_layout.setSpacing(25)
        
        # Başlık
        title_label = QLabel("👥 Kullanıcı Yönetimi")
        title_label.setFont(QFont("Segoe UI", 24, QFont.Bold))
        title_label.setStyleSheet("""
            QLabel {
                color: #1e293b;
                padding: 0px 0px 15px 0px;
                border-bottom: 3px solid #667eea;
                margin-bottom: 20px;
            }
        """)
        container_layout.addWidget(title_label)
        
        # Üst buton container
        top_button_container = QFrame()
        top_button_container.setStyleSheet("QFrame { background: transparent; }")
        top_button_layout = QHBoxLayout(top_button_container)
        top_button_layout.setContentsMargins(0, 0, 0, 15)
        
        # Yeni Kullanıcı Ekle butonu
        add_user_btn = QPushButton("➕ Yeni Kullanıcı Ekle")
        add_user_btn.setFont(QFont("Segoe UI", 14, QFont.Bold))
        add_user_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 #10b981, stop:1 #059669);
                color: white;
                border: none;
                padding: 12px 25px;
                border-radius: 12px;
                font-size: 14px;
                font-weight: 700;
                min-width: 180px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 #059669, stop:1 #047857);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 #047857, stop:1 #065f46);
            }
        """)
        add_user_btn.clicked.connect(self.open_add_user_dialog)
        
        top_button_layout.addWidget(add_user_btn)
        top_button_layout.addStretch()
        container_layout.addWidget(top_button_container)
        
        # Tablo container
        table_container = QFrame()
        table_container.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 15px;
                border: 1px solid #e2e8f0;
                padding: 25px;
                margin-top: 10px;
            }
        """)
        table_layout = QVBoxLayout(table_container)
        table_layout.setSpacing(20)
        
        # Tablo başlığı
        table_title = QLabel("📋 Mevcut Kullanıcılar")
        table_title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        table_title.setStyleSheet("""
            QLabel {
                color: #1e293b;
                padding: 15px;
                background-color: #f8fafc;
                border-radius: 10px;
                border-left: 4px solid #667eea;
                margin-bottom: 15px;
            }
        """)
        table_layout.addWidget(table_title)
        
        # Kullanıcı tablosu
        self.user_table = QTableWidget()
        self.user_table.setColumnCount(6)  # İşlemler sütunu eklendi
        self.user_table.setHorizontalHeaderLabels(["ID", "Kullanıcı Adı", "E-posta", "Departman", "Yönetici", "İşlemler"])
        self.user_table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                gridline-color: #f1f5f9;
                font-size: 14px;
                selection-background-color: transparent;
            }
            QTableWidget::item {
                padding: 12px 8px;
                border-bottom: 1px solid #f1f5f9;
                color: #374151;
            }
            QTableWidget::item:selected {
                background-color: #f3f4f6;
                color: #1f2937;
            }
            QHeaderView::section {
                background-color: #f8fafc;
                color: #374151;
                padding: 12px 8px;
                border: none;
                border-bottom: 2px solid #e5e7eb;
                font-weight: 600;
                font-size: 14px;
            }
        """)
        
        # Sütun boyutlandırma stratejisi
        header = self.user_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # ID
        header.setSectionResizeMode(1, QHeaderView.Stretch)           # Kullanıcı Adı
        header.setSectionResizeMode(2, QHeaderView.Stretch)           # E-posta
        header.setSectionResizeMode(3, QHeaderView.Stretch)           # Departman
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Yönetici
        header.setSectionResizeMode(5, QHeaderView.Fixed)             # İşlemler
        
        # İşlemler sütunu genişliği
        self.user_table.setColumnWidth(5, 160)
        
        # Tablo boyutlandırma
        self.user_table.setMinimumHeight(400)
        self.user_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # Tabloya seçim politikası
        self.user_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.user_table.setSelectionMode(QAbstractItemView.SingleSelection)
        
        table_layout.addWidget(self.user_table)
        container_layout.addWidget(table_container)
        
        layout.addWidget(main_container)
        layout.addStretch()
        
        # Scroll area'ya widget'ı ekle
        scroll_area.setWidget(widget)
        
        # Kullanıcıları yükle
        self.load_users()
        return main_widget

    def load_users(self):
        try:
            db = SessionLocal()
            try:
                users = db.query(User).all()
                self.user_table.setRowCount(len(users))
                for i, user in enumerate(users):
                    manager = db.query(User).filter_by(id=user.manager_id).first() if user.manager_id else None
                    
                    # ID
                    id_item = QTableWidgetItem(str(user.id))
                    id_item.setTextAlignment(Qt.AlignCenter)
                    self.user_table.setItem(i, 0, id_item)
                    
                    # Kullanıcı adı
                    self.user_table.setItem(i, 1, QTableWidgetItem(user.username))
                    
                    # E-posta
                    self.user_table.setItem(i, 2, QTableWidgetItem(user.email or ""))
                    
                    # Departman
                    self.user_table.setItem(i, 3, QTableWidgetItem(user.department or ""))
                    
                    # Yönetici
                    manager_item = QTableWidgetItem(manager.username if manager else "-")
                    manager_item.setTextAlignment(Qt.AlignCenter)
                    self.user_table.setItem(i, 4, manager_item)
                    
                    # İşlemler - Düzenle ve Sil butonları
                    edit_btn = QPushButton("✏️")
                    edit_btn.setToolTip("Düzenle")
                    edit_btn.setStyleSheet("""
                        QPushButton {
                            background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                                stop:0 #667eea, stop:1 #764ba2);
                            color: white;
                            border: none;
                            padding: 8px;
                            border-radius: 6px;
                            font-size: 14px;
                            font-weight: 600;
                            min-width: 35px;
                            max-width: 35px;
                        }
                        QPushButton:hover {
                            background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                                stop:0 #5a67d8, stop:1 #6b46a8);
                        }
                    """)
                    
                    delete_btn = QPushButton("🗑️")
                    delete_btn.setToolTip("Sil")
                    delete_btn.setStyleSheet("""
                        QPushButton {
                            background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                                stop:0 #ef4444, stop:1 #dc2626);
                            color: white;
                            border: none;
                            padding: 8px;
                            border-radius: 6px;
                            font-size: 14px;
                            font-weight: 600;
                            min-width: 35px;
                            max-width: 35px;
                        }
                        QPushButton:hover {
                            background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                                stop:0 #dc2626, stop:1 #b91c1c);
                        }
                    """)
                    
                    # Butonlara kullanıcı ID'sini ekle
                    edit_btn.setProperty("user_id", user.id)
                    edit_btn.clicked.connect(self.on_edit_user_clicked)
                    
                    delete_btn.setProperty("user_id", user.id)
                    delete_btn.clicked.connect(self.on_delete_user_clicked)
                    
                    # Butonları tabloya ekle
                    button_widget = QWidget()
                    button_layout = QHBoxLayout(button_widget)
                    button_layout.addWidget(edit_btn)
                    button_layout.addWidget(delete_btn)
                    button_layout.setAlignment(Qt.AlignCenter)
                    button_layout.setContentsMargins(5, 0, 5, 0)
                    button_layout.setSpacing(5)
                    self.user_table.setCellWidget(i, 5, button_widget)
                    
                    # Satır yüksekliğini ayarla
                    self.user_table.setRowHeight(i, 50)
                    
            finally:
                db.close()
        except Exception as e:
            QMessageBox.warning(self, "Hata", f"Kullanıcı listesi alınamadı: {e}")

    def on_edit_user_clicked(self):
        """Düzenle butonuna tıklandığında çalışır"""
        sender = self.sender()  # Tıklanan buton
        user_id = sender.property("user_id")
        
        try:
            db = SessionLocal()
            try:
                user = db.query(User).filter_by(id=user_id).first()
                if user:
                    self.open_user_dialog(user)
                else:
                    QMessageBox.warning(self, "Hata", "Kullanıcı bulunamadı!")
            finally:
                db.close()
        except Exception as e:
            QMessageBox.warning(self, "Hata", f"Kullanıcı bilgileri alınamadı: {e}")

    def on_delete_user_clicked(self):
        """Sil butonuna tıklandığında çalışır"""
        sender = self.sender()  # Tıklanan buton
        user_id = sender.property("user_id")
        
        # Onay iste
        reply = QMessageBox.question(
            self,
            "⚠️ Kullanıcı Silme Onayı",
            "Bu kullanıcıyı silmek istediğinizden emin misiniz?\n\n"
            "⚠️ DİKKAT: Bu işlem geri alınamaz!\n"
            "• Kullanıcının tüm verisi silinecek\n"
            "• Mesai talepleri ve yemek katılım kayıtları silinecek",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        try:
            db = SessionLocal()
            try:
                user = db.query(User).filter_by(id=user_id).first()
                if user:
                    username = user.username
                    
                    # İlişkili verileri de sil
                    # Önce bu kullanıcının astlarının manager_id'sini temizle
                    subordinates = db.query(User).filter_by(manager_id=user_id).all()
                    for sub in subordinates:
                        sub.manager_id = None
                    
                    # Kullanıcının mesai taleplerini sil
                    db.query(OvertimeRequest).filter_by(user_id=user_id).delete()
                    
                    # Kullanıcının yemek katılım kayıtlarını sil
                    db.query(Attendance).filter_by(user_id=user_id).delete()
                    
                    # Kullanıcıyı sil
                    db.delete(user)
                    db.commit()
                    
                    QMessageBox.information(self, "✅ Başarılı", f"'{username}' kullanıcısı başarıyla silindi!")
                    self.load_users()
                else:
                    QMessageBox.warning(self, "Hata", "Kullanıcı bulunamadı!")
            except Exception as e:
                db.rollback()
                raise e
            finally:
                db.close()
        except Exception as e:
            QMessageBox.warning(self, "Hata", f"Kullanıcı silinirken hata oluştu: {e}")

    def open_add_user_dialog(self):
        self.open_user_dialog()

    def open_user_dialog(self, user=None):
        dialog = QDialog(self)
        dialog.setWindowTitle("Kullanıcı Düzenle" if user else "Yeni Kullanıcı Ekle")
        dialog.setMinimumSize(500, 400)
        dialog.setStyleSheet("""
            QDialog {
                background-color: #f8fafc;
            }
            QLabel {
                font-size: 14px;
                font-weight: 600;
                color: #374151;
                margin-bottom: 5px;
            }
            QLineEdit, QComboBox {
                padding: 12px 15px;
                border: 2px solid #e1e5e9;
                border-radius: 8px;
                font-size: 14px;
                background-color: white;
                margin-bottom: 15px;
            }
            QLineEdit:focus, QComboBox:focus {
                border-color: #667eea;
                background-color: #fefefe;
            }
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 #667eea, stop:1 #764ba2);
                color: white;
                border: none;
                padding: 12px 25px;
                border-radius: 8px;
                font-size: 14px;
                font-weight: 600;
                min-width: 120px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 #5a67d8, stop:1 #6b46a8);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 #4c51bf, stop:1 #553c9a);
            }
        """)
        
        # Ana layout
        main_layout = QVBoxLayout(dialog)
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(20)
        
        # Başlık
        title_label = QLabel("✏️ Kullanıcı Düzenle" if user else "➕ Yeni Kullanıcı Ekle")
        title_label.setFont(QFont("Segoe UI", 18, QFont.Bold))
        title_label.setStyleSheet("""
            QLabel {
                color: #1e293b;
                padding: 15px;
                background-color: white;
                border-radius: 10px;
                border-left: 4px solid #667eea;
                margin-bottom: 20px;
            }
        """)
        main_layout.addWidget(title_label)
        
        # Form container
        form_container = QFrame()
        form_container.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 15px;
                border: 1px solid #e2e8f0;
                padding: 25px;
            }
        """)
        form_layout = QFormLayout(form_container)
        form_layout.setSpacing(15)
        form_layout.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
        
        # Form alanları
        username_edit = QLineEdit(user.username if user else "")
        username_edit.setPlaceholderText("Kullanıcı adını girin...")
        
        email_edit = QLineEdit(user.email if user else "")
        email_edit.setPlaceholderText("E-posta adresini girin...")
        
        dept_edit = QLineEdit(user.department if user else "")
        dept_edit.setPlaceholderText("Departman adını girin...")
        
        pwd_edit = QLineEdit()
        pwd_edit.setEchoMode(QLineEdit.Password)
        pwd_edit.setPlaceholderText("Şifre girin..." if not user else "Değiştirmek için yeni şifre girin...")
        
        # Yönetici seçimi
        db = SessionLocal()
        all_users = db.query(User).all()
        db.close()
        
        manager_combo = QComboBox()
        manager_combo.addItem("Yönetici Yok", None)
        for u in all_users:
            if not user or u.id != user.id:
                manager_combo.addItem(f"👤 {u.username}", u.id)
        
        if user and user.manager_id:
            idx = manager_combo.findData(user.manager_id)
            if idx >= 0:
                manager_combo.setCurrentIndex(idx)
        
        # Admin yetkisi checkbox
        admin_checkbox = QCheckBox("🔐 Admin Yetkisi Ver")
        admin_checkbox.setStyleSheet("""
            QCheckBox {
                font-size: 14px;
                font-weight: 600;
                color: #374151;
                spacing: 10px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 3px;
                border: 2px solid #cbd5e1;
                background-color: white;
            }
            QCheckBox::indicator:checked {
                background-color: #667eea;
                border-color: #667eea;
            }
        """)
        if user and user.is_admin:
            admin_checkbox.setChecked(True)
        
        # Form alanlarını ekle
        form_layout.addRow("👤 Kullanıcı Adı:", username_edit)
        form_layout.addRow("📧 E-posta:", email_edit)
        form_layout.addRow("🏢 Departman:", dept_edit)
        form_layout.addRow("🔒 Şifre:", pwd_edit)
        form_layout.addRow("👨‍💼 Yönetici:", manager_combo)
        form_layout.addRow("", admin_checkbox)
        
        main_layout.addWidget(form_container)
        
        # Buton container
        button_container = QFrame()
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(0, 15, 0, 0)
        
        cancel_btn = QPushButton("❌ İptal")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background: #e5e7eb;
                color: #374151;
                border: 1px solid #d1d5db;
            }
            QPushButton:hover {
                background: #d1d5db;
            }
        """)
        cancel_btn.clicked.connect(dialog.reject)
        
        save_btn = QPushButton("💾 Kaydet")
        
        button_layout.addStretch()
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(save_btn)
        
        main_layout.addWidget(button_container)

        def save_user():
            # Form verilerinin geçerliliğini kontrol et
            username = username_edit.text().strip()
            email = email_edit.text().strip()
            
            if not username:
                QMessageBox.warning(dialog, "⚠️ Uyarı", "Kullanıcı adı boş bırakılamaz!")
                return
                
            if not user and not pwd_edit.text():
                QMessageBox.warning(dialog, "⚠️ Uyarı", "Yeni kullanıcı için şifre gereklidir!")
                return
                
            try:
                db = SessionLocal()
                try:
                    if user:
                        # Mevcut kullanıcıyı güncelle
                        user.username = username
                        user.email = email
                        user.department = dept_edit.text().strip()
                        if pwd_edit.text():
                            user.hashed_password = pwd_context.hash(pwd_edit.text())
                        user.manager_id = manager_combo.currentData()
                        user.is_admin = admin_checkbox.isChecked()
                        success_msg = f"'{username}' kullanıcısı başarıyla güncellendi!"
                    else:
                        # Yeni kullanıcı oluştur
                        new_user = User(
                            username=username,
                            email=email,
                            department=dept_edit.text().strip(),
                            hashed_password=pwd_context.hash(pwd_edit.text()),
                            is_admin=admin_checkbox.isChecked(),
                            manager_id=manager_combo.currentData()
                        )
                        db.add(new_user)
                        success_msg = f"'{username}' kullanıcısı başarıyla oluşturuldu!"
                    
                    db.commit()
                    QMessageBox.information(dialog, "✅ Başarılı", success_msg)
                    dialog.accept()
                    self.load_users()
                except Exception as e:
                    db.rollback()
                    raise e
                finally:
                    db.close()
            except Exception as e:
                QMessageBox.warning(dialog, "❌ Hata", f"Kullanıcı kaydedilirken hata oluştu: {e}")
        
        save_btn.clicked.connect(save_user)
        dialog.exec()

    # --- Dashboard TAB ---
    def dashboard_tab_ui(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # Başlık
        title = QLabel("📊 Dashboard")
        title.setFont(QFont("Segoe UI", 20, QFont.Bold))
        title.setStyleSheet("color: #1e293b; margin-bottom: 20px;")
        layout.addWidget(title)
        
        # İstatistik tablosu
        self.stats_table = QTableWidget(2, 2)  # 2 satır, 2 sütun
        self.stats_table.setHorizontalHeaderLabels(["İstatistik", "Değer"])
        self.stats_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.stats_table.setMinimumHeight(120)
        self.stats_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        
        # Tablo stilini ayarla
        self.stats_table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                border-radius: 10px;
                font-size: 16px;
                gridline-color: #e5e7eb;
                selection-background-color: #f3f4f6;
            }
            QTableWidget::item {
                padding: 15px;
                border-bottom: 1px solid #e5e7eb;
            }
            QTableWidget::item:nth-child(2) {
                color: #667eea;
                font-weight: bold;
            }
            QHeaderView::section {
                background-color: #f8f9fa;
                padding: 12px;
                border: none;
                font-weight: bold;
                font-size: 14px;
            }
        """)
        
        # Tablo verilerini doldur
        try:
            db = SessionLocal()
            try:
                user_count = db.query(User).count()
                today = date.today()
                today_attendance = db.query(Attendance).filter(Attendance.date == today, Attendance.will_attend == True).count()
                
                # Satır 1: Kullanıcı Sayısı
                user_item = QTableWidgetItem("👥 Kullanıcı Sayısı")
                user_item.setFont(QFont("Segoe UI", 14, QFont.Bold))
                self.stats_table.setItem(0, 0, user_item)
                
                user_count_item = QTableWidgetItem(str(user_count))
                user_count_item.setFont(QFont("Segoe UI", 16, QFont.Bold))
                self.stats_table.setItem(0, 1, user_count_item)
                
                # Satır 2: Bugünkü Yemek Katılım
                attendance_item = QTableWidgetItem("✅ Bugünkü Yemek Katılım")
                attendance_item.setFont(QFont("Segoe UI", 14, QFont.Bold))
                self.stats_table.setItem(1, 0, attendance_item)
                
                attendance_count_item = QTableWidgetItem(str(today_attendance))
                attendance_count_item.setFont(QFont("Segoe UI", 16, QFont.Bold))
                self.stats_table.setItem(1, 1, attendance_count_item)
                
            finally:
                db.close()
        except Exception as e:
            # Hata durumunda
            error_item = QTableWidgetItem(f"❌ Hata: {str(e)}")
            error_item.setFont(QFont("Segoe UI", 12))
            self.stats_table.setItem(0, 0, error_item)
            self.stats_table.setSpan(0, 0, 2, 2)  # Hata mesajını tüm tabloya yay
        
        layout.addWidget(self.stats_table)
        layout.addStretch()
        
        return widget

    # --- Menü Planlama TAB ---
    def menu_plan_tab_ui(self):
        # Ana widget
        main_widget = QWidget()
        main_widget.setStyleSheet("""
            QWidget {
                background-color: #f8fafc;
            }
        """)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Scroll area oluştur
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                background-color: #f1f5f9;
                width: 12px;
                border-radius: 6px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background-color: #667eea;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #5a67d8;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
            }
            QScrollBar:horizontal {
                background-color: #f1f5f9;
                height: 12px;
                border-radius: 6px;
                margin: 0px;
            }
            QScrollBar::handle:horizontal {
                background-color: #667eea;
                border-radius: 6px;
                min-width: 20px;
            }
            QScrollBar::handle:horizontal:hover {
                background-color: #5a67d8;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                border: none;
                background: none;
            }
        """)
        
        # İçerik widget'ı
        widget = QWidget()
        widget.setStyleSheet("""
            QWidget {
                background-color: #f8fafc;
            }
        """)
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Excel İçe Aktarma Bölümü
        excel_frame = QFrame()
        excel_frame.setStyleSheet("""
            QFrame {
                background-color: #f8fafc;
                border-radius: 12px;
                border: 2px solid #e2e8f0;
                padding: 20px;
                margin-bottom: 20px;
            }
        """)
        excel_layout = QVBoxLayout(excel_frame)
        
        excel_title = QLabel("📊 Excel'den Menü İçe Aktarma")
        excel_title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        excel_title.setStyleSheet("color: #1e293b; margin-bottom: 10px;")
        excel_layout.addWidget(excel_title)
        
        excel_info = QLabel("""
📝 Excel Dosyası Formatı:
• Sütun A: Tarih (YYYY-MM-DD formatında, örn: 2025-08-07)
• Sütun B: Çorba
• Sütun C: Ana Yemek  
• Sütun D: Yan Yemek
• Sütun E: Tatlı
• İlk satır başlık olmalıdır
        """)
        excel_info.setStyleSheet("color: #475569; font-size: 13px; padding: 10px; background-color: #f1f5f9; border-radius: 8px;")
        excel_layout.addWidget(excel_info)
        
        excel_btn_layout = QHBoxLayout()
        self.import_excel_btn = QPushButton("📂 Excel Dosyası Seç ve İçe Aktar")
        self.import_excel_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #10b981, stop:1 #059669);
                color: white;
                font-weight: bold;
                padding: 12px 20px;
                border-radius: 8px;
                font-size: 14px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #059669, stop:1 #047857);
            }
        """)
        self.import_excel_btn.clicked.connect(self.import_menu_from_excel)
        
        self.download_template_btn = QPushButton("📋 Excel Şablonu İndir")
        self.download_template_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #3b82f6, stop:1 #2563eb);
                color: white;
                font-weight: bold;
                padding: 12px 20px;
                border-radius: 8px;
                font-size: 14px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #2563eb, stop:1 #1d4ed8);
            }
        """)
        self.download_template_btn.clicked.connect(self.download_excel_template)
        
        excel_btn_layout.addWidget(self.download_template_btn)
        excel_btn_layout.addWidget(self.import_excel_btn)
        excel_layout.addLayout(excel_btn_layout)
        
        layout.addWidget(excel_frame)
        
        # Mevcut Manuel Menü Ekleme Bölümü
        manual_frame = QFrame()
        manual_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 12px;
                border: 1px solid #e2e8f0;
                padding: 20px;
            }
        """)
        manual_layout = QVBoxLayout(manual_frame)
        
        manual_title = QLabel("✏️ Manuel Menü Ekleme")
        manual_title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        manual_title.setStyleSheet("color: #1e293b; margin-bottom: 15px;")
        manual_layout.addWidget(manual_title)
        
        form = QFormLayout()
        self.menu_date = QDateEdit(QDate.currentDate())
        self.soup = QLineEdit()
        self.main = QLineEdit()
        self.side = QLineEdit()
        self.dessert = QLineEdit()
        
        # Placeholder'lar ekle
        self.soup.setPlaceholderText("Örn: Mercimek Çorbası")
        self.main.setPlaceholderText("Örn: Tavuk Schnitzel")
        self.side.setPlaceholderText("Örn: Pilav")
        self.dessert.setPlaceholderText("Örn: Muhallebi")
        
        form.addRow("Tarih:", self.menu_date)
        form.addRow("Çorba:", self.soup)
        form.addRow("Ana Yemek:", self.main)
        form.addRow("Yan Yemek:", self.side)
        form.addRow("Tatlı:", self.dessert)
        manual_layout.addLayout(form)
        
        add_btn = QPushButton("➕ Menü Ekle")
        add_btn.clicked.connect(self.add_menu)
        manual_layout.addWidget(add_btn)
        
        layout.addWidget(manual_frame)
        
        # Mevcut Menüleri Görüntüleme ve Silme Bölümü
        existing_frame = QFrame()
        existing_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 12px;
                border: 1px solid #e2e8f0;
                padding: 20px;
                margin-top: 20px;
            }
        """)
        existing_layout = QVBoxLayout(existing_frame)
        
        existing_title = QLabel("📋 Mevcut Menüler")
        existing_title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        existing_title.setStyleSheet("color: #1e293b; margin-bottom: 15px;")
        existing_layout.addWidget(existing_title)
        
        # Tarih aralığı seçimi
        date_range_layout = QHBoxLayout()
        date_range_layout.addWidget(QLabel("Başlangıç:"))
        self.start_date = QDateEdit(QDate.currentDate())
        date_range_layout.addWidget(self.start_date)
        
        date_range_layout.addWidget(QLabel("Bitiş:"))
        self.end_date = QDateEdit(QDate.currentDate().addDays(30))
        date_range_layout.addWidget(self.end_date)
        
        load_menus_btn = QPushButton("🔍 Menüleri Listele")
        load_menus_btn.clicked.connect(self.load_existing_menus)
        date_range_layout.addWidget(load_menus_btn)
        date_range_layout.addStretch()
        
        existing_layout.addLayout(date_range_layout)
        
        # Menü listesi tablosu
        self.menu_table = QTableWidget()
        self.menu_table.setColumnCount(6)
        self.menu_table.setHorizontalHeaderLabels(["Tarih", "Çorba", "Ana Yemek", "Yan Yemek", "Tatlı", "İşlemler"])
        
        # Sütun boyutlandırma stratejisi
        header = self.menu_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Tarih
        header.setSectionResizeMode(1, QHeaderView.Stretch)           # Çorba
        header.setSectionResizeMode(2, QHeaderView.Stretch)           # Ana Yemek
        header.setSectionResizeMode(3, QHeaderView.Stretch)           # Yan Yemek
        header.setSectionResizeMode(4, QHeaderView.Stretch)           # Tatlı
        header.setSectionResizeMode(5, QHeaderView.Fixed)             # İşlemler
        self.menu_table.setColumnWidth(5, 120)
        
        # Tablo boyutlandırma
        self.menu_table.setMinimumHeight(300)
        self.menu_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        existing_layout.addWidget(self.menu_table)
        
        layout.addWidget(existing_frame)
        
        # İçerik widget'ını scroll area'ya ekle
        scroll_area.setWidget(widget)
        
        # Scroll area'yı main layout'a ekle
        main_layout.addWidget(scroll_area)
        
        return main_widget

    def add_menu(self):
        # Form verilerinin geçerliliğini kontrol et
        soup = self.soup.text().strip()
        main = self.main.text().strip()
        side = self.side.text().strip()
        dessert = self.dessert.text().strip()
        
        if not any([soup, main, side, dessert]):
            QMessageBox.warning(self, "Uyarı", "En az bir yemek girmelisiniz!")
            return
            
        try:
            db = SessionLocal()
            try:
                # Aynı tarihte menü var mı kontrol et
                existing_menu = db.query(Menu).filter_by(date=self.menu_date.date().toPython()).first()
                if existing_menu:
                    reply = QMessageBox.question(self, "Menü Var", 
                                               "Bu tarihte zaten bir menü var. Üzerine yazmak istiyor musunuz?",
                                               QMessageBox.Yes | QMessageBox.No)
                    if reply == QMessageBox.No:
                        return
                    # Mevcut menüyü güncelle
                    existing_menu.menu_items = {
                        "Corbasi": soup,
                        "Ana_Yemek": main,
                        "Yan_Yemek": side,
                        "Tatli": dessert
                    }
                else:
                    # Yeni menü ekle
                    menu = Menu(
                        date=self.menu_date.date().toPython(),
                        meal_type="Öğle Yemeği",
                        menu_items={
                            "Corbasi": soup,
                            "Ana_Yemek": main,
                            "Yan_Yemek": side,
                            "Tatli": dessert
                        }
                    )
                    db.add(menu)
                
                db.commit()
                QMessageBox.information(self, "Menü", "Menü başarıyla kaydedildi!")
                # Formu temizle
                self.soup.clear()
                self.main.clear()
                self.side.clear()
                self.dessert.clear()
                # Tarihi bir gün ilerlet
                current_date = self.menu_date.date()
                self.menu_date.setDate(current_date.addDays(1))
            except Exception as e:
                db.rollback()
                raise e
            finally:
                db.close()
        except Exception as e:
            QMessageBox.warning(self, "Hata", f"Menü eklerken hata: {e}")

    def download_excel_template(self):
        """Excel şablonu indir"""
        try:
            # Şablon verisi oluştur
            template_data = {
                'Tarih': [
                    '2025-08-07',
                    '2025-08-08', 
                    '2025-08-09',
                    '2025-08-10',
                    '2025-08-11'
                ],
                'Çorba': [
                    'Mercimek Çorbası',
                    'Domates Çorbası',
                    'Yayla Çorbası', 
                    'Ezogelin Çorbası',
                    'Tarhana Çorbası'
                ],
                'Ana Yemek': [
                    'Tavuk Schnitzel',
                    'Köfte',
                    'Balık',
                    'Tavuk Sote',
                    'Mantı'
                ],
                'Yan Yemek': [
                    'Pilav',
                    'Makarna',
                    'Bulgur Pilavı',
                    'Patates Püresi',
                    'Nohut'
                ],
                'Tatlı': [
                    'Muhallebi',
                    'Sütlaç',
                    'Kazandibi',
                    'Baklava',
                    'Künefe'
                ]
            }
            
            # DataFrame oluştur
            df = pd.DataFrame(template_data)
            
            # Dosya kaydetme dialog'u
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Excel Şablonu Kaydet",
                "menu_template.xlsx",
                "Excel Files (*.xlsx);;All Files (*)"
            )
            
            if file_path:
                # Excel dosyasını kaydet
                df.to_excel(file_path, index=False, engine='openpyxl')
                QMessageBox.information(
                    self, 
                    "Başarılı", 
                    f"Excel şablonu başarıyla kaydedildi:\n{file_path}"
                )
                
        except Exception as e:
            QMessageBox.warning(self, "Hata", f"Şablon oluşturulurken hata: {e}")

    def import_menu_from_excel(self):
        """Excel'den menü içe aktar"""
        try:
            # Dosya seçme dialog'u
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Excel Dosyası Seç",
                "",
                "Excel Files (*.xlsx *.xls);;All Files (*)"
            )
            
            if not file_path:
                return
                
            # Excel dosyasını oku
            try:
                df = pd.read_excel(file_path, engine='openpyxl')
            except Exception as e:
                QMessageBox.warning(self, "Hata", f"Excel dosyası okunamadı: {e}")
                return
            
            # Sütun isimlerini kontrol et
            required_columns = ['Tarih', 'Çorba', 'Ana Yemek', 'Yan Yemek', 'Tatlı']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                QMessageBox.warning(
                    self, 
                    "Hata", 
                    f"Eksik sütunlar: {', '.join(missing_columns)}\n\n"
                    "Gerekli sütunlar: Tarih, Çorba, Ana Yemek, Yan Yemek, Tatlı"
                )
                return
            
            # Veri doğrulama ve işleme
            imported_count = 0
            skipped_count = 0
            error_rows = []
            
            db = SessionLocal()
            try:
                for index, row in df.iterrows():
                    try:
                        # Tarih işleme
                        date_value = row['Tarih']
                        if pd.isna(date_value):
                            error_rows.append(f"Satır {index + 2}: Tarih boş")
                            continue
                            
                        # Tarih formatını parse et
                        if isinstance(date_value, str):
                            menu_date = pd.to_datetime(date_value).date()
                        else:
                            menu_date = date_value.date() if hasattr(date_value, 'date') else date_value
                        
                        # Mevcut menüyü kontrol et
                        existing_menu = db.query(Menu).filter_by(date=menu_date).first()
                        
                        menu_items = {
                            "Corbasi": str(row['Çorba']) if not pd.isna(row['Çorba']) else "",
                            "Ana_Yemek": str(row['Ana Yemek']) if not pd.isna(row['Ana Yemek']) else "",
                            "Yan_Yemek": str(row['Yan Yemek']) if not pd.isna(row['Yan Yemek']) else "",
                            "Tatli": str(row['Tatlı']) if not pd.isna(row['Tatlı']) else ""
                        }
                        
                        # En az bir yemek var mı kontrol et
                        if not any(menu_items.values()):
                            error_rows.append(f"Satır {index + 2}: Hiç yemek belirtilmemiş")
                            continue
                        
                        if existing_menu:
                            # Mevcut menüyü güncelle
                            existing_menu.menu_items = menu_items
                            skipped_count += 1
                        else:
                            # Yeni menü ekle
                            new_menu = Menu(
                                date=menu_date,
                                meal_type="Öğle Yemeği",
                                menu_items=menu_items
                            )
                            db.add(new_menu)
                            imported_count += 1
                            
                    except Exception as e:
                        error_rows.append(f"Satır {index + 2}: {str(e)}")
                        continue
                
                db.commit()
                
                # Sonuç mesajı
                result_msg = f"✅ İçe aktarma tamamlandı!\n\n"
                result_msg += f"📥 Yeni eklenen: {imported_count} menü\n"
                result_msg += f"🔄 Güncellenen: {skipped_count} menü\n"
                
                if error_rows:
                    result_msg += f"\n⚠️ Hatalar ({len(error_rows)}):\n"
                    result_msg += "\n".join(error_rows[:5])  # İlk 5 hatayı göster
                    if len(error_rows) > 5:
                        result_msg += f"\n... ve {len(error_rows) - 5} hata daha"
                
                QMessageBox.information(self, "İçe Aktarma Sonucu", result_msg)
                
            except Exception as e:
                db.rollback()
                raise e
            finally:
                db.close()
                
        except Exception as e:
            QMessageBox.warning(self, "Hata", f"İçe aktarma sırasında hata: {e}")

    # --- Mesai Talepleri TAB ---
    def overtime_tab_ui(self):
        # Ana widget
        main_widget = QWidget()
        main_widget.setStyleSheet("""
            QWidget {
                background-color: #f8fafc;
            }
        """)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Scroll area oluştur
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                background-color: #f1f5f9;
                width: 12px;
                border-radius: 6px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background-color: #667eea;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #5a67d8;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
            }
            QScrollBar:horizontal {
                background-color: #f1f5f9;
                height: 12px;
                border-radius: 6px;
                margin: 0px;
            }
            QScrollBar::handle:horizontal {
                background-color: #667eea;
                border-radius: 6px;
                min-width: 20px;
            }
            QScrollBar::handle:horizontal:hover {
                background-color: #5a67d8;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                border: none;
                background: none;
            }
        """)
        
        # İçerik widget'ı
        widget = QWidget()
        widget.setStyleSheet("""
            QWidget {
                background-color: #f8fafc;
            }
        """)
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(25)
        
        # Ana container
        main_container = QFrame()
        main_container.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 15px;
                border: 1px solid #e2e8f0;
                padding: 30px;
            }
        """)
        main_container_layout = QVBoxLayout(main_container)
        main_container_layout.setSpacing(25)
        
        # Başlık
        title_label = QLabel("🕒 Fazla Mesai Talepleri")
        title_label.setFont(QFont("Segoe UI", 24, QFont.Bold))
        title_label.setStyleSheet("""
            QLabel {
                color: #1e293b;
                padding: 0px 0px 15px 0px;
                border-bottom: 3px solid #667eea;
                margin-bottom: 20px;
            }
        """)
        main_container_layout.addWidget(title_label)
        
        # Filtre container
        filter_container = QFrame()
        filter_container.setStyleSheet("""
            QFrame {
                background-color: #f1f5f9;
                border-radius: 12px;
                padding: 20px;
                border: 1px solid #e2e8f0;
            }
        """)
        filter_layout = QHBoxLayout(filter_container)
        filter_layout.setContentsMargins(20, 15, 20, 15)
        filter_layout.setSpacing(20)
        
        # Durum filtresi
        status_label = QLabel("📊 Duruma Göre:")
        status_label.setFont(QFont("Segoe UI", 14, QFont.Weight.Medium))
        status_label.setStyleSheet("QLabel { color: #475569; font-weight: 600; }")
        
        self.overtime_status_filter = QComboBox()
        self.overtime_status_filter.addItems([
            "Tümü",
            "Yönetici Onayı Bekliyor", 
            "İK Onayı Bekliyor",
            "Onaylandı",
            "Reddedildi"
        ])
        self.overtime_status_filter.setStyleSheet("""
            QComboBox {
                padding: 12px 15px;
                border: 2px solid #cbd5e1;
                border-radius: 10px;
                font-size: 14px;
                min-width: 180px;
                background-color: white;
                color: #1e293b;
                font-weight: 500;
            }
            QComboBox:focus {
                border-color: #667eea;
                background-color: #fefefe;
            }
            QComboBox:hover {
                border-color: #94a3b8;
            }
            QComboBox::drop-down {
                border: none;
                width: 30px;
                background: transparent;
            }
            QComboBox::down-arrow {
                image: none;
                border: none;
                width: 0px;
            }
        """)
        
        # Filtrele butonu
        filter_btn = QPushButton("🔍 Filtrele")
        filter_btn.setFont(QFont("Segoe UI", 14, QFont.Bold))
        filter_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 #667eea, stop:1 #764ba2);
                color: white;
                border: none;
                padding: 12px 25px;
                border-radius: 12px;
                font-size: 14px;
                font-weight: 700;
                min-width: 140px;
                text-align: center;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 #5a67d8, stop:1 #6b46a8);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 #4c51bf, stop:1 #553c9a);
            }
        """)
        filter_btn.clicked.connect(self.load_overtime_requests)
        
        filter_layout.addWidget(status_label)
        filter_layout.addWidget(self.overtime_status_filter)
        filter_layout.addWidget(filter_btn)
        filter_layout.addStretch()
        
        main_container_layout.addWidget(filter_container)
        
        # Tablo container
        table_container = QFrame()
        table_container.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 15px;
                border: 1px solid #e2e8f0;
                padding: 25px;
                margin-top: 10px;
            }
        """)
        table_layout = QVBoxLayout(table_container)
        table_layout.setSpacing(20)
        
        # Tablo başlığı
        table_title = QLabel("📋 Mesai Talepleri Listesi")
        table_title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        table_title.setStyleSheet("""
            QLabel {
                color: #1e293b;
                padding: 15px;
                background-color: #f8fafc;
                border-radius: 10px;
                border-left: 4px solid #667eea;
                margin-bottom: 15px;
            }
        """)
        table_layout.addWidget(table_title)
        
        # Tablo
        self.overtime_table = QTableWidget()
        self.overtime_table.setColumnCount(8)  # Seç sütunu eklendi
        self.overtime_table.setHorizontalHeaderLabels([
            "Seç", "ID", "Personel", "Departman", "Tarih", "Saatler", "Açıklama", "Durum"
        ])
        self.overtime_table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                gridline-color: #f1f5f9;
                font-size: 14px;
                selection-background-color: transparent;
            }
            QTableWidget::item {
                padding: 12px 8px;
                border-bottom: 1px solid #f1f5f9;
                color: #374151;
            }
            QTableWidget::item:selected {
                background-color: #f3f4f6;
                color: #1f2937;
            }
            QHeaderView::section {
                background-color: #f8fafc;
                color: #374151;
                padding: 12px 8px;
                border: none;
                border-bottom: 2px solid #e5e7eb;
                font-weight: 600;
                font-size: 14px;
            }
        """)
        
        # Sütun genişlikleri
        header = self.overtime_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Fixed)             # Seç
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # ID
        header.setSectionResizeMode(2, QHeaderView.Stretch)           # Personel
        header.setSectionResizeMode(3, QHeaderView.Stretch)           # Departman
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Tarih
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # Saatler
        header.setSectionResizeMode(6, QHeaderView.Stretch)           # Açıklama
        header.setSectionResizeMode(7, QHeaderView.ResizeToContents)  # Durum
        
        # Seç sütunu genişliği
        self.overtime_table.setColumnWidth(0, 50)
        
        # Tabloya seçim politikası
        self.overtime_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.overtime_table.setSelectionMode(QAbstractItemView.SingleSelection)
        
        # Tablo boyutlandırma
        self.overtime_table.setMinimumHeight(300)
        self.overtime_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        table_layout.addWidget(self.overtime_table)
        
        # Buton container
        button_container = QFrame()
        button_container.setStyleSheet("QFrame { background: transparent; }")
        button_layout = QHBoxLayout(button_container)
        button_layout.setSpacing(15)
        button_layout.setContentsMargins(0, 15, 0, 0)
        
        # Onayla butonu
        approve_btn = QPushButton("✅ Seçili Talebi Onayla")
        approve_btn.setFont(QFont("Segoe UI", 14, QFont.Bold))
        approve_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 #10b981, stop:1 #059669);
                color: white;
                border: none;
                padding: 12px 25px;
                border-radius: 12px;
                font-size: 14px;
                font-weight: 700;
                min-width: 180px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 #059669, stop:1 #047857);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 #047857, stop:1 #065f46);
            }
        """)
        approve_btn.clicked.connect(lambda: self.handle_overtime_action("Onaylandı"))
        
        # Reddet butonu
        reject_btn = QPushButton("❌ Seçili Talebi Reddet")
        reject_btn.setFont(QFont("Segoe UI", 14, QFont.Bold))
        reject_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 #ef4444, stop:1 #dc2626);
                color: white;
                border: none;
                padding: 12px 25px;
                border-radius: 12px;
                font-size: 14px;
                font-weight: 700;
                min-width: 180px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 #dc2626, stop:1 #b91c1c);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 #b91c1c, stop:1 #991b1b);
            }
        """)
        reject_btn.clicked.connect(lambda: self.handle_overtime_action("Reddedildi"))
        
        button_layout.addWidget(approve_btn)
        button_layout.addWidget(reject_btn)
        button_layout.addStretch()
        
        table_layout.addWidget(button_container)
        main_container_layout.addWidget(table_container)
        
        layout.addWidget(main_container)
        layout.addStretch()
        
        # İçerik widget'ını scroll area'ya ekle
        scroll_area.setWidget(widget)
        
        # Scroll area'yı main layout'a ekle
        main_layout.addWidget(scroll_area)
        
        # Sayfa açılır açılmaz talepleri yükle
        QTimer.singleShot(200, self.load_overtime_requests)
        
        return main_widget

    def load_overtime_requests(self):
        try:
            # Önceki checkbox'ları temizle
            self.overtime_checkboxes.clear()
            self.selected_overtime_id = None
            
            db = SessionLocal()
            try:
                # Filtreye göre durum belirle
                status_filter = self.overtime_status_filter.currentText()
                
                # Eğer admin ise tüm talepleri, yönetici ise sadece kendi ekibinin taleplerini görsün
                if self.user.is_admin:
                    query = db.query(OvertimeRequest)
                else:
                    # Yöneticinin ekibindeki kullanıcıların id'leri
                    sub_ids = [u.id for u in db.query(User).filter_by(manager_id=self.user.id).all()]
                    if not sub_ids:
                        self.overtime_table.setRowCount(0)
                        return
                    query = db.query(OvertimeRequest).filter(OvertimeRequest.user_id.in_(sub_ids))
                
                # Durum filtresini uygula
                if status_filter != "Tümü":
                    query = query.filter(OvertimeRequest.status == status_filter)
                    
                overt = query.order_by(OvertimeRequest.date.desc()).all()
                        
                self.overtime_table.setRowCount(len(overt))
                for i, row in enumerate(overt):
                    user = db.query(User).filter_by(id=row.user_id).first()
                    
                    # Checkbox (Seç sütunu)
                    checkbox = QCheckBox()
                    checkbox.setStyleSheet("""
                        QCheckBox {
                            spacing: 5px;
                            font-size: 14px;
                        }
                        QCheckBox::indicator {
                            width: 16px;
                            height: 16px;
                            border: 2px solid #d1d5db;
                            border-radius: 3px;
                            background-color: white;
                        }
                        QCheckBox::indicator:checked {
                            background-color: #667eea;
                            border-color: #667eea;
                            image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iMTIiIHZpZXdCb3g9IjAgMCAxMiAxMiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTEwIDNMNC41IDguNUwyIDYiIHN0cm9rZT0id2hpdGUiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIi8+Cjwvc3ZnPgo=);
                        }
                        QCheckBox::indicator:hover {
                            border-color: #667eea;
                        }
                    """)
                    
                    # Checkbox'a veri ekle (talep ID'si)
                    checkbox.setProperty("overtime_id", row.id)
                    checkbox.clicked.connect(self.on_checkbox_clicked)
                    
                    # Checkbox'u listeye ekle
                    self.overtime_checkboxes.append(checkbox)
                    
                    # Checkbox'u tabloya ekle
                    checkbox_widget = QWidget()
                    checkbox_layout = QHBoxLayout(checkbox_widget)
                    checkbox_layout.addWidget(checkbox)
                    checkbox_layout.setAlignment(Qt.AlignCenter)
                    checkbox_layout.setContentsMargins(0, 0, 0, 0)
                    self.overtime_table.setCellWidget(i, 0, checkbox_widget)
                    
                    # ID
                    id_item = QTableWidgetItem(str(row.id))
                    id_item.setTextAlignment(Qt.AlignCenter)
                    self.overtime_table.setItem(i, 1, id_item)
                    
                    # Personel
                    user_item = QTableWidgetItem(user.username if user else "Bilinmeyen")
                    self.overtime_table.setItem(i, 2, user_item)
                    
                    # Departman
                    dept_item = QTableWidgetItem(user.department if user and user.department else "Belirtilmemiş")
                    self.overtime_table.setItem(i, 3, dept_item)
                    
                    # Tarih
                    date_item = QTableWidgetItem(str(row.date))
                    date_item.setTextAlignment(Qt.AlignCenter)
                    self.overtime_table.setItem(i, 4, date_item)
                    
                    # Saatler
                    time_item = QTableWidgetItem(f"{row.start_time} - {row.end_time}")
                    time_item.setTextAlignment(Qt.AlignCenter)
                    self.overtime_table.setItem(i, 5, time_item)
                    
                    # Açıklama
                    desc_item = QTableWidgetItem(row.reason or "Açıklama yok")
                    self.overtime_table.setItem(i, 6, desc_item)
                    
                    # Durum - Renkli badge
                    status_item = QTableWidgetItem(row.status)
                    status_item.setTextAlignment(Qt.AlignCenter)
                    
                    # Duruma göre renk
                    if row.status == "Yönetici Onayı Bekliyor":
                        status_item.setBackground(QColor("#fef3c7"))  # Sarı arka plan
                        status_item.setForeground(QColor("#92400e"))  # Kahve yazı
                    elif row.status == "İK Onayı Bekliyor":
                        status_item.setBackground(QColor("#dbeafe"))  # Mavi arka plan
                        status_item.setForeground(QColor("#1e40af"))  # Mavi yazı
                    elif row.status == "Onaylandı":
                        status_item.setBackground(QColor("#d1fae5"))  # Yeşil arka plan
                        status_item.setForeground(QColor("#065f46"))  # Koyu yeşil yazı
                    elif row.status == "Reddedildi":
                        status_item.setBackground(QColor("#fee2e2"))  # Kırmızı arka plan
                        status_item.setForeground(QColor("#991b1b"))  # Koyu kırmızı yazı
                    
                    self.overtime_table.setItem(i, 7, status_item)
                    
                # Satır yüksekliklerini ayarla
                for i in range(len(overt)):
                    self.overtime_table.setRowHeight(i, 50)
                    
            finally:
                db.close()
        except Exception as e:
            QMessageBox.warning(self, "Hata", f"Mesai talepleri alınamadı: {e}")

    def on_checkbox_clicked(self):
        """Checkbox tıklandığında çalışır - sadece bir tane seçili olmasını sağlar"""
        sender = self.sender()  # Tıklanan checkbox
        overtime_id = sender.property("overtime_id")
        
        if sender.isChecked():
            # Bu checkbox seçildiyse, diğerlerini kapat
            for cb in self.overtime_checkboxes:
                if cb != sender and cb.isChecked():
                    cb.setChecked(False)
            
            self.selected_overtime_id = overtime_id
        else:
            # Checkbox kapatıldıysa, seçili ID'yi temizle
            self.selected_overtime_id = None

    def handle_overtime_action(self, status):
        # Checkbox'tan seçilen ID'yi kullan
        if not self.selected_overtime_id:
            QMessageBox.warning(self, "Uyarı", "Lütfen işlem yapmak istediğiniz talebi seçin!")
            return
            
        try:
            # Seçili talep bilgilerini al
            selected_user_name = None
            selected_date_str = None
            
            # Tabloda seçili talebi bul
            for i in range(self.overtime_table.rowCount()):
                id_item = self.overtime_table.item(i, 1)  # ID sütunu şimdi 1. sütun
                if id_item and int(id_item.text()) == self.selected_overtime_id:
                    selected_user_name = self.overtime_table.item(i, 2).text()  # Personel sütunu
                    selected_date_str = self.overtime_table.item(i, 4).text()   # Tarih sütunu
                    break
            
            if not selected_user_name:
                QMessageBox.warning(self, "Hata", "Seçili talep bilgileri alınamadı!")
                return
            
            # Onay iste
            reply = QMessageBox.question(
                self, 
                "Onay", 
                f"{selected_user_name} kullanıcısının {selected_date_str} tarihli fazla mesai talebini '{status}' yapmak istediğinizden emin misiniz?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply != QMessageBox.Yes:
                return
            
            db = SessionLocal()
            try:
                req = db.query(OvertimeRequest).filter_by(id=self.selected_overtime_id).first()
                if req:
                    if req.status not in ["Yönetici Onayı Bekliyor", "İK Onayı Bekliyor"]:
                        QMessageBox.warning(self, "Uyarı", "Bu talep zaten işlem görmüş!")
                        return
                    
                    # Yönetici ise bir sonraki aşamaya geçir
                    if status == "Onaylandı" and req.status == "Yönetici Onayı Bekliyor":
                        req.status = "İK Onayı Bekliyor"
                        success_msg = f"Talep İK onayına gönderildi."
                    else:
                        req.status = status
                        success_msg = f"Talep '{status}' olarak güncellendi."
                    
                    db.commit()
                    QMessageBox.information(self, "✅ Başarılı", success_msg)
                    
                    # Seçimi temizle ve tabloyu yeniden yükle
                    self.selected_overtime_id = None
                    self.load_overtime_requests()
                else:
                    QMessageBox.warning(self, "Hata", "Talep bulunamadı!")
            except Exception as e:
                db.rollback()
                raise e
            finally:
                db.close()
        except Exception as e:
            QMessageBox.warning(self, "Hata", f"Talep güncellenirken hata: {e}")

    # --- Raporlar TAB ---
    def reports_tab_ui(self):
        # Ana scroll widget'ı oluştur
        main_widget = QWidget()
        main_widget.setStyleSheet("QWidget { background-color: #f8fafc; }")
        
        # Scroll area oluştur
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: #f8fafc;
                border: none;
            }
            QScrollBar:vertical {
                background-color: #f1f5f9;
                width: 12px;
                border-radius: 6px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background-color: #cbd5e1;
                border-radius: 6px;
                min-height: 20px;
                margin: 2px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #94a3b8;
            }
            QScrollBar::handle:vertical:pressed {
                background-color: #64748b;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)
        
        # Ana layout
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll_area)
        
        widget = QWidget()
        widget.setStyleSheet("""
            QWidget {
                background-color: #f8fafc;
            }
        """)
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(25)
        
        # Ana container
        main_container = QFrame()
        main_container.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 15px;
                border: 1px solid #e2e8f0;
                padding: 30px;
            }
        """)
        main_layout = QVBoxLayout(main_container)
        main_layout.setSpacing(25)
        
        # Başlık
        title_label = QLabel("📋 Yemek Katılım Raporları")
        title_label.setFont(QFont("Segoe UI", 24, QFont.Bold))
        title_label.setStyleSheet("""
            QLabel {
                color: #1e293b;
                padding: 0px 0px 15px 0px;
                border-bottom: 3px solid #667eea;
                margin-bottom: 20px;
            }
        """)
        main_layout.addWidget(title_label)
        
        # Tarih seçimi ve rapor butonu container
        date_container = QFrame()
        date_container.setStyleSheet("""
            QFrame {
                background-color: #f1f5f9;
                border-radius: 12px;
                padding: 20px;
                border: 1px solid #e2e8f0;
            }
        """)
        date_layout = QHBoxLayout(date_container)
        date_layout.setContentsMargins(20, 15, 20, 15)
        date_layout.setSpacing(20)
        
        date_label = QLabel("📅 Rapor Tarihi:")
        date_label.setFont(QFont("Segoe UI", 14, QFont.Weight.Medium))
        date_label.setStyleSheet("""
            QLabel {
                color: #475569;
                font-weight: 600;
            }
        """)
        
        self.report_date = QDateEdit()
        self.report_date.setDate(QDate.currentDate())
        self.report_date.setCalendarPopup(True)
        self.report_date.setStyleSheet("""
            QDateEdit {
                padding: 12px 15px;
                border: 2px solid #cbd5e1;
                border-radius: 10px;
                font-size: 14px;
                min-width: 180px;
                background-color: white;
                color: #1e293b;
                font-weight: 500;
            }
            QDateEdit:focus {
                border-color: #667eea;
                background-color: #fefefe;
            }
            QDateEdit:hover {
                border-color: #94a3b8;
            }
            QDateEdit::drop-down {
                border: none;
                width: 30px;
            }
            QDateEdit::down-arrow {
                image: none;
                border: none;
                width: 0px;
            }
        """)
        
        self.show_report_btn = QPushButton("📊 Raporu Göster")
        self.show_report_btn.setFont(QFont("Segoe UI", 14, QFont.Bold))
        self.show_report_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 #667eea, stop:1 #764ba2);
                color: white;
                border: none;
                padding: 12px 25px;
                border-radius: 12px;
                font-size: 14px;
                font-weight: 700;
                min-width: 160px;
                text-align: center;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 #5a67d8, stop:1 #6b46a8);
                transform: translateY(-1px);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 #4c51bf, stop:1 #553c9a);
                transform: translateY(1px);
            }
        """)
        self.show_report_btn.clicked.connect(self.load_attendance_report)
        
        date_layout.addWidget(date_label)
        date_layout.addWidget(self.report_date)
        date_layout.addWidget(self.show_report_btn)
        date_layout.addStretch()
        
        main_layout.addWidget(date_container)
        
        # Rapor sonuçları - her zaman görünür
        self.report_results = QFrame()
        self.report_results.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 15px;
                border: 1px solid #e2e8f0;
                padding: 25px;
                margin-top: 10px;
            }
        """)
        results_layout = QVBoxLayout(self.report_results)
        results_layout.setSpacing(20)
        
        # Rapor başlığı
        self.report_title_label = QLabel("📊 Tarih seçip 'Raporu Göster' butonuna basın")
        self.report_title_label.setFont(QFont("Segoe UI", 16, QFont.Bold))
        self.report_title_label.setStyleSheet("""
            QLabel {
                color: #1e293b;
                padding: 15px;
                background-color: #f8fafc;
                border-radius: 10px;
                border-left: 4px solid #667eea;
                margin-bottom: 15px;
            }
        """)
        results_layout.addWidget(self.report_title_label)
        
        # İki sütunlu düzen (Gelecekler / Gelmeyecekler)
        columns_container = QFrame()
        columns_container.setStyleSheet("QFrame { background: transparent; }")
        columns_layout = QHBoxLayout(columns_container)
        columns_layout.setSpacing(20)
        columns_layout.setContentsMargins(0, 0, 0, 0)
        
        # Sol sütun - Gelecek personeller
        attending_frame = QFrame()
        attending_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #f0fdf4, stop:1 #dcfce7);
                border-radius: 15px;
                border: 2px solid #bbf7d0;
                padding: 15px;
                min-height: 400px;
            }
        """)
        attending_layout = QVBoxLayout(attending_frame)
        attending_layout.setContentsMargins(10, 10, 10, 10)
        attending_layout.setSpacing(10)
        
        self.attending_title = QLabel("✅ Gelecek Personeller (0)")
        self.attending_title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        self.attending_title.setStyleSheet("""
            QLabel {
                color: #166534;
                padding: 8px 12px;
                background-color: rgba(220, 252, 231, 0.8);
                border-radius: 6px;
                border: 1px solid #bbf7d0;
                font-weight: bold;
                min-height: 20px;
            }
        """)
        self.attending_title.setAlignment(Qt.AlignCenter)
        attending_layout.addWidget(self.attending_title)
        
        self.attending_list = QListWidget()
        self.attending_list.setStyleSheet("""
            QListWidget {
                border: none;
                background-color: rgba(255, 255, 255, 0.9);
                border-radius: 8px;
                font-size: 13px;
                padding: 8px;
                color: #1f2937;
                outline: none;
            }
            QListWidget::item {
                padding: 6px 10px;
                margin: 1px 0px;
                border-radius: 4px;
                color: #1f2937;
                font-weight: 500;
                background-color: transparent;
                border: none;
                outline: none;
            }
            QListWidget::item:hover {
                background-color: rgba(34, 197, 94, 0.1);
            }
            QListWidget::item:selected {
                background-color: rgba(34, 197, 94, 0.15);
                border: none;
                outline: none;
            }
        """)
        self.attending_list.setMinimumHeight(250)
        self.attending_list.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        attending_layout.addWidget(self.attending_list)
        
        # Sağ sütun - Gelmeyecek personeller
        not_attending_frame = QFrame()
        not_attending_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #fef2f2, stop:1 #fee2e2);
                border-radius: 15px;
                border: 2px solid #fecaca;
                padding: 15px;
                min-height: 400px;
            }
        """)
        not_attending_layout = QVBoxLayout(not_attending_frame)
        not_attending_layout.setContentsMargins(10, 10, 10, 10)
        not_attending_layout.setSpacing(10)
        
        self.not_attending_title = QLabel("❌ Gelmeyecek Personeller (0)")
        self.not_attending_title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        self.not_attending_title.setStyleSheet("""
            QLabel {
                color: #dc2626;
                padding: 8px 12px;
                background-color: rgba(254, 226, 226, 0.8);
                border-radius: 6px;
                border: 1px solid #fecaca;
                font-weight: bold;
                min-height: 20px;
            }
        """)
        self.not_attending_title.setAlignment(Qt.AlignCenter)
        not_attending_layout.addWidget(self.not_attending_title)
        
        self.not_attending_list = QListWidget()
        self.not_attending_list.setStyleSheet("""
            QListWidget {
                border: none;
                background-color: rgba(255, 255, 255, 0.9);
                border-radius: 8px;
                font-size: 13px;
                padding: 8px;
                color: #1f2937;
                outline: none;
            }
            QListWidget::item {
                padding: 6px 10px;
                margin: 1px 0px;
                border-radius: 4px;
                color: #1f2937;
                font-weight: 500;
                background-color: transparent;
                border: none;
                outline: none;
            }
            QListWidget::item:hover {
                background-color: rgba(239, 68, 68, 0.1);
            }
            QListWidget::item:selected {
                background-color: rgba(239, 68, 68, 0.15);
                border: none;
                outline: none;
            }
        """)
        self.not_attending_list.setMinimumHeight(250)
        self.not_attending_list.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        not_attending_layout.addWidget(self.not_attending_list)
        
        columns_layout.addWidget(attending_frame)
        columns_layout.addWidget(not_attending_frame)
        results_layout.addWidget(columns_container)
        
        main_layout.addWidget(self.report_results)
        main_layout.addStretch()
        
        layout.addWidget(main_container)
        layout.addStretch()
        
        # Scroll area'ya widget'ı ekle
        scroll_area.setWidget(widget)
        
        # Sayfa açılır açılmaz bugünkü raporu otomatik yükle
        QTimer.singleShot(200, self.load_attendance_report)
        
        return main_widget

    def load_attendance_report(self):
        try:
            selected_date = self.report_date.date().toString("yyyy-MM-dd")
            
            db = SessionLocal()
            try:
                # Seçilen tarihteki yemek katılım kayıtlarını al
                attendances = db.query(Attendance).filter_by(date=selected_date).all()
                
                # Listeleri temizle
                self.attending_list.clear()
                self.not_attending_list.clear()
                
                attending_count = 0
                not_attending_count = 0
                
                if attendances:
                    for attendance in attendances:
                        user = db.query(User).filter_by(id=attendance.user_id).first()
                        if user:
                            user_text = f"{user.username} ({user.department or 'N/A'})"
                            
                            if attendance.will_attend:
                                self.attending_list.addItem(user_text)
                                attending_count += 1
                            else:
                                self.not_attending_list.addItem(user_text)
                                not_attending_count += 1
                else:
                    # Hiç yemek katılım kaydı yoksa bilgilendirme
                    no_data_msg = f"Bu tarih için henüz yemek katılım kaydı yok"
                    self.attending_list.addItem(no_data_msg)
                    self.not_attending_list.addItem(no_data_msg)
                
                # Başlıkları güncelle
                self.attending_title.setText(f"✅ Gelecek Personeller ({attending_count})")
                self.not_attending_title.setText(f"❌ Gelmeyecek Personeller ({not_attending_count})")
                
                # Rapor başlığını güncelle
                from datetime import datetime
                date_obj = datetime.strptime(selected_date, "%Y-%m-%d")
                formatted_date = date_obj.strftime("%d.%m.%Y")
                self.report_title_label.setText(f"📊 {formatted_date} Tarihli Yemek Katılım Raporu")
                
            finally:
                db.close()
                
        except Exception as e:
            QMessageBox.warning(self, "Hata", f"Rapor yüklenirken hata oluştu: {e}")

    def load_existing_menus(self):
        """Mevcut menüleri tarih aralığına göre yükle"""
        try:
            start_date = self.start_date.date().toPython()
            end_date = self.end_date.date().toPython()
            
            db = SessionLocal()
            try:
                menus = db.query(Menu).filter(
                    Menu.date >= start_date,
                    Menu.date <= end_date
                ).order_by(Menu.date).all()
                
                self.menu_table.setRowCount(len(menus))
                
                for i, menu in enumerate(menus):
                    # Tarih
                    date_item = QTableWidgetItem(menu.date.strftime("%d/%m/%Y (%A)"))
                    self.menu_table.setItem(i, 0, date_item)
                    
                    # Menü öğeleri
                    items = menu.menu_items or {}
                    self.menu_table.setItem(i, 1, QTableWidgetItem(items.get("Corbasi", "-")))
                    self.menu_table.setItem(i, 2, QTableWidgetItem(items.get("Ana_Yemek", "-")))
                    self.menu_table.setItem(i, 3, QTableWidgetItem(items.get("Yan_Yemek", "-")))
                    self.menu_table.setItem(i, 4, QTableWidgetItem(items.get("Tatli", "-")))
                    
                    # Silme butonu
                    delete_btn = QPushButton("🗑️ Sil")
                    delete_btn.setStyleSheet("""
                        QPushButton {
                            background-color: #dc2626;
                            color: white;
                            border-radius: 4px;
                            padding: 6px 12px;
                            font-weight: bold;
                        }
                        QPushButton:hover {
                            background-color: #b91c1c;
                        }
                    """)
                    delete_btn.clicked.connect(lambda checked, menu_id=menu.id, menu_date=menu.date: self.delete_menu(menu_id, menu_date))
                    self.menu_table.setCellWidget(i, 5, delete_btn)
                    
            finally:
                db.close()
                
        except Exception as e:
            QMessageBox.warning(self, "Hata", f"Menüler yüklenirken hata: {e}")

    def delete_menu(self, menu_id, menu_date):
        """Menü sil"""
        date_str = menu_date.strftime("%d/%m/%Y (%A)")
        reply = QMessageBox.question(
            self, 
            "Menü Sil",
            f"{date_str} tarihli menüyü silmek istediğinizden emin misiniz?\n\n"
            "Bu işlem geri alınamaz ve ilgili yemek katılım kayıtları da silinecektir.",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.No:
            return
            
        try:
            db = SessionLocal()
            try:
                # Menüyü bul ve sil
                menu = db.query(Menu).filter(Menu.id == menu_id).first()
                if not menu:
                    QMessageBox.warning(self, "Hata", "Menü bulunamadı!")
                    return
                
                # İlgili yemek katılım kayıtlarını sil (sadece tarihe göre)
                deleted_attendance = db.query(Attendance).filter(
                    Attendance.date == menu.date
                ).delete(synchronize_session=False)
                
                # Menüyü sil
                db.delete(menu)
                
                # Değişiklikleri veritabanına kesin olarak kaydet
                db.commit()
                
                # Transaction'ın tamamlandığından emin olmak için flush
                db.flush()
                
                QMessageBox.information(
                    self, 
                    "Başarılı", 
                    f"Menü başarıyla silindi!\n\n"
                    f"Silinen menü: {date_str}\n"
                    f"Silinen yemek katılım kaydı: {deleted_attendance} adet"
                )
                
                # Kısa bir bekleyip listeyi yenile (veritabanı commit'inin tamamlanması için)
                QTimer.singleShot(200, self.load_existing_menus)
                
            except Exception as e:
                db.rollback()
                QMessageBox.critical(self, "Veritabanı Hatası", f"Menü silinirken veritabanı hatası: {str(e)}")
                raise e
            finally:
                db.close()
                
        except Exception as e:
            QMessageBox.warning(self, "Hata", f"Menü silinirken hata: {str(e)}")

    def logout(self):
        if QMessageBox.question(self, "Çıkış", "Çıkış yapmak istiyor musunuz?", QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            # Login ekranına dön
            self.back_to_login_callback()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MainApp()
    win.show()
    sys.exit(app.exec())
