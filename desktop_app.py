import sys
import requests
from datetime import datetime, timedelta, date
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QMessageBox, QStackedWidget, QTabWidget,
    QFormLayout, QDateEdit, QTimeEdit, QTextEdit, QTableWidget,
    QTableWidgetItem, QHeaderView, QScrollArea, QFrame, QComboBox, QDialog
)
from PySide6.QtCore import Qt, QDate, QTime, QSize
from PySide6.QtGui import QFont, QIcon

# --- Genel Ayarlar ---
API_URL = "http://127.0.0.1:8000" # FastAPI sunucunuzun adresi

# --- Modern ve Şık bir Arayüz için Stil Tanımları (QSS) ---
STYLE = """
QWidget {
    font-family: 'Segoe UI', sans-serif;
    font-size: 14px;
    color: #333;
}
QMainWindow, QDialog {
    background-color: #f5f7fa;
}
#Card {
    background-color: white;
    border-radius: 12px;
    border: 1px solid #e0e0e0;
}
#Header {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #667eea, stop:1 #764ba2);
    color: white;
    padding: 15px;
    border-radius: 0;
}
#Header QLabel {
    font-size: 22px;
    font-weight: bold;
}
#UserInfoLabel {
    font-size: 14px;
    font-weight: bold;
    color: #ffffff;
    background-color: rgba(255, 255, 255, 0.2);
    padding: 5px 10px;
    border-radius: 15px;
}
QPushButton {
    background-color: #667eea;
    color: white;
    border: none;
    padding: 10px 15px;
    border-radius: 8px;
    font-weight: bold;
}
QPushButton:hover {
    background-color: #5a6fd9;
}
QPushButton:disabled {
    background-color: #d0d0d0;
    color: #888;
}
#LogoutButton {
    background-color: #ef4444;
}
#LogoutButton:hover {
    background-color: #dc2626;
}
QLineEdit, QDateEdit, QTimeEdit, QTextEdit, QComboBox {
    border: 1px solid #ccc;
    border-radius: 5px;
    padding: 8px;
    background-color: #fff;
}
QLineEdit:focus, QDateEdit:focus, QTimeEdit:focus, QTextEdit:focus, QComboBox:focus {
    border-color: #667eea;
}
QTabWidget::pane {
    border-top: 1px solid #e0e0e0;
}
QTabBar::tab {
    background: #f0f2f5;
    color: #555;
    padding: 12px 20px;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    border-bottom: none;
    font-weight: bold;
}
QTabBar::tab:selected {
    background: white;
    color: #667eea;
}
QTableWidget {
    background-color: white;
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    gridline-color: #f0f0f0;
}
QHeaderView::section {
    background-color: #f8f9fa;
    padding: 10px;
    border: none;
    font-weight: bold;
}
"""

# --- Ana Pencere ---
class MainWindow(QMainWindow):
    """Uygulamanın ana penceresi. Giriş ve ana panel arasında geçişi yönetir."""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Yemekhane Yönetim Sistemi")
        self.setMinimumSize(1280, 800)
        self.setStyleSheet(STYLE)

        self.token = None
        self.user_info = {}

        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)

        self.login_screen = LoginScreen()
        self.login_screen.login_successful.connect(self.show_main_panel)
        self.stacked_widget.addWidget(self.login_screen)

    def show_main_panel(self, token, user_info):
        """Giriş başarılı olduğunda ana paneli oluşturur ve gösterir."""
        self.token = token
        self.user_info = user_info
        
        self.main_panel = MainPanel(self.token, self.user_info)
        self.main_panel.logout_requested.connect(self.logout)
        self.stacked_widget.addWidget(self.main_panel)
        self.stacked_widget.setCurrentWidget(self.main_panel)

    def logout(self):
        """Oturumu kapatır ve giriş ekranına döner."""
        self.token = None
        self.user_info = {}
        self.stacked_widget.removeWidget(self.main_panel)
        self.main_panel.deleteLater()
        self.stacked_widget.setCurrentWidget(self.login_screen)
        self.login_screen.clear_fields()

# --- Giriş Ekranı ---
class LoginScreen(QWidget):
    """Kullanıcı adı ve şifre ile giriş yapılmasını sağlayan ekran."""
    from PySide6.QtCore import Signal
    login_successful = Signal(str, dict)

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        login_box = QFrame()
        login_box.setFrameShape(QFrame.StyledPanel)
        login_box.setMaximumWidth(450)
        
        layout = QVBoxLayout(login_box)
        layout.setSpacing(20)

        title = QLabel("🍽️ Yemekhane Sistemi")
        title.setFont(QFont("Segoe UI", 24, QFont.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #667eea;")

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Kullanıcı Adı")
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Şifre")
        self.password_input.setEchoMode(QLineEdit.Password)
        
        self.login_button = QPushButton("Giriş Yap")
        self.login_button.clicked.connect(self.handle_login)
        self.password_input.returnPressed.connect(self.handle_login) # Enter ile giriş

        self.message_label = QLabel("")
        self.message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.message_label.setStyleSheet("color: red;")

        layout.addWidget(title)
        layout.addWidget(self.username_input)
        layout.addWidget(self.password_input)
        layout.addWidget(self.login_button)
        layout.addWidget(self.message_label)
        
        main_layout.addWidget(login_box)

    def handle_login(self):
        """Giriş butonuna tıklandığında API'ye istek gönderir."""
        username = self.username_input.text()
        password = self.password_input.text()

        if not username or not password:
            self.message_label.setText("Kullanıcı adı ve şifre boş bırakılamaz.")
            return

        self.login_button.setEnabled(False)
        self.login_button.setText("Giriş Yapılıyor...")
        self.message_label.setText("")

        try:
            response = requests.post(
                f"{API_URL}/token",
                data={"username": username, "password": password}
            )
            if response.status_code == 200:
                data = response.json()
                self.login_successful.emit(data["access_token"], data)
            else:
                error_data = response.json()
                self.message_label.setText(error_data.get("detail", "Bilinmeyen bir hata oluştu."))
        except requests.exceptions.RequestException as e:
            self.message_label.setText(f"Sunucuya bağlanılamadı: {e}")
        finally:
            self.login_button.setEnabled(True)
            self.login_button.setText("Giriş Yap")
            
    def clear_fields(self):
        """Giriş alanlarını ve mesajı temizler."""
        self.username_input.clear()
        self.password_input.clear()
        self.message_label.clear()

# --- Ana Panel (Giriş sonrası) ---
class MainPanel(QWidget):
    """Kullanıcı veya Admin/Yönetici arayüzünü içeren ana panel."""
    from PySide6.QtCore import Signal
    logout_requested = Signal()

    def __init__(self, token, user_info):
        super().__init__()
        self.token = token
        self.user_info = user_info
        self.is_admin = user_info.get("is_admin", False)
        self.is_manager = user_info.get("is_manager", False)
        self.headers = {"Authorization": f"Bearer {self.token}"}
        
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Üst Başlık (Header)
        header = QWidget()
        header.setObjectName("Header")
        header_layout = QHBoxLayout(header)
        
        panel_title = "Admin Paneli" if self.is_admin else ("Yönetici Paneli" if self.is_manager else "Kullanıcı Paneli")
        title_label = QLabel(f"🍽️ {panel_title}")
        
        user_info_label = QLabel(self.user_info.get("username"))
        user_info_label.setObjectName("UserInfoLabel")
        
        logout_button = QPushButton("Çıkış")
        logout_button.setObjectName("LogoutButton")
        logout_button.clicked.connect(self.logout)

        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(user_info_label)
        header_layout.addWidget(logout_button)
        layout.addWidget(header)

        # Tablar
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        # Kullanıcı tipine göre tabları oluştur
        if self.is_admin or self.is_manager:
            self.create_admin_manager_tabs()
        else:
            self.create_user_tabs()

    def create_user_tabs(self):
        """Standart kullanıcı için tabları oluşturur."""
        self.user_menu_tab = UserMenuTab(self.headers)
        self.tabs.addTab(self.user_menu_tab, "📅 Yemekhane Menüsü")
        
        self.user_overtime_tab = UserOvertimeTab(self.headers, self.user_info.get("department"))
        self.tabs.addTab(self.user_overtime_tab, "🕒 Fazla Mesai Taleplerim")
        
    def create_admin_manager_tabs(self):
        """Admin ve Yönetici için tabları oluşturur."""
        # Yöneticiler ve Adminler mesai taleplerini görür
        self.overtime_management_tab = OvertimeManagementTab(self.headers, self.is_admin, self.is_manager)
        tab_title = "Mesai Talepleri (Tüm Ekip)" if self.is_manager and not self.is_admin else "🕒 Fazla Mesai Yönetimi"
        self.tabs.addTab(self.overtime_management_tab, tab_title)

        # Sadece Adminler bu tabları görür
        if self.is_admin:
            self.dashboard_tab = AdminDashboardTab(self.headers)
            self.tabs.insertTab(0, self.dashboard_tab, "📊 Dashboard") # Başa ekle
            
            self.menu_planning_tab = AdminMenuPlanningTab(self.headers)
            self.tabs.addTab(self.menu_planning_tab, "📅 Menü Planlama")
            
            self.reports_tab = AdminReportsTab(self.headers)
            self.tabs.addTab(self.reports_tab, "📋 Raporlar")

            self.user_management_tab = AdminUserManagementTab(self.headers)
            self.tabs.addTab(self.user_management_tab, "👥 Kullanıcı Yönetimi")
            
            self.tabs.setCurrentIndex(0) # Dashboard'u varsayılan yap

    def logout(self):
        """Çıkış sinyalini tetikler."""
        reply = QMessageBox.question(self, "Çıkış", "Çıkış yapmak istediğinizden emin misiniz?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.logout_requested.emit()

# --- KULLANICI PANELLERİ ---

class UserMenuTab(QWidget):
    """Kullanıcının yemek menüsünü gördüğü ve katılım bildirdiği tab."""
    def __init__(self, headers):
        super().__init__()
        self.headers = headers
        self.attendance_selections = {}
        self.active_view = 'weekly'
        self.current_date = QDate.currentDate()
        self.init_ui()
        self.load_menus()

    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Üst kontrol barı
        top_bar_layout = QHBoxLayout()
        
        # Görünüm butonları (Günlük, Haftalık, Aylık)
        view_buttons_layout = QHBoxLayout()
        self.daily_btn = QPushButton("Günlük")
        self.weekly_btn = QPushButton("Haftalık")
        self.monthly_btn = QPushButton("Aylık")
        self.daily_btn.clicked.connect(lambda: self.set_active_view('daily'))
        self.weekly_btn.clicked.connect(lambda: self.set_active_view('weekly'))
        self.monthly_btn.clicked.connect(lambda: self.set_active_view('monthly'))
        view_buttons_layout.addWidget(self.daily_btn)
        view_buttons_layout.addWidget(self.weekly_btn)
        view_buttons_layout.addWidget(self.monthly_btn)
        top_bar_layout.addLayout(view_buttons_layout)
        top_bar_layout.addStretch()

        # Navigasyon
        self.prev_btn = QPushButton("← Önceki")
        self.next_btn = QPushButton("Sonraki →")
        self.period_label = QLabel()
        self.period_label.setFont(QFont("Segoe UI", 14, QFont.Bold))
        self.prev_btn.clicked.connect(lambda: self.navigate(-1))
        self.next_btn.clicked.connect(lambda: self.navigate(1))
        top_bar_layout.addWidget(self.prev_btn)
        top_bar_layout.addWidget(self.period_label)
        top_bar_layout.addWidget(self.next_btn)
        top_bar_layout.addStretch()

        # Kaydet butonu
        self.save_btn = QPushButton("Seçimleri Kaydet")
        self.save_btn.clicked.connect(self.save_selections)
        top_bar_layout.addWidget(self.save_btn)
        
        layout.addLayout(top_bar_layout)

        # Menü kartlarının gösterileceği alan
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("background-color: transparent; border: none;")
        self.menu_container = QWidget()
        self.menu_layout = QHBoxLayout(self.menu_container) # Haftalık görünüm için
        self.scroll_area.setWidget(self.menu_container)
        layout.addWidget(self.scroll_area)
        
        self.update_view_buttons()

    def set_active_view(self, view):
        self.active_view = view
        self.update_view_buttons()
        self.load_menus()

    def update_view_buttons(self):
        self.daily_btn.setEnabled(self.active_view != 'daily')
        self.weekly_btn.setEnabled(self.active_view != 'weekly')
        self.monthly_btn.setEnabled(self.active_view != 'monthly')

    def navigate(self, direction):
        if self.active_view == 'daily':
            self.current_date = self.current_date.addDays(direction)
        elif self.active_view == 'weekly':
            self.current_date = self.current_date.addDays(7 * direction)
        elif self.active_view == 'monthly':
            self.current_date = self.current_date.addMonths(direction)
        self.load_menus()

    def load_menus(self):
        start_date, end_date = self.get_date_range()
        self.period_label.setText(self.get_period_text(start_date, end_date))
        
        try:
            params = {"start_date": start_date.toString("yyyy-MM-dd"), "end_date": end_date.toString("yyyy-MM-dd")}
            response = requests.get(f"{API_URL}/api/menus", headers=self.headers, params=params)
            response.raise_for_status()
            menus_data = response.json()
            self.display_menus(menus_data, start_date, end_date)
        except requests.exceptions.RequestException as e:
            QMessageBox.critical(self, "Hata", f"Menüler yüklenemedi: {e}")

    def display_menus(self, menus_data, start_date, end_date):
        # Eski widget'ları temizle
        while self.menu_layout.count():
            child = self.menu_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        menus_map = {item['date']: item for item in menus_data}
        
        current_date_iter = start_date
        while current_date_iter <= end_date:
            date_str = current_date_iter.toString("yyyy-MM-dd")
            menu = menus_map.get(date_str)
            
            card = self.create_menu_card(current_date_iter, menu)
            self.menu_layout.addWidget(card)
            
            current_date_iter = current_date_iter.addDays(1)
            
    def create_menu_card(self, q_date, menu_data):
        card = QFrame()
        card.setObjectName("Card")
        card_layout = QVBoxLayout(card)
        
        date_str = q_date.toString("dd MMMM yyyy, dddd")
        date_label = QLabel(date_str)
        date_label.setFont(QFont("Segoe UI", 12, QFont.Bold))
        card_layout.addWidget(date_label)

        if q_date == QDate.currentDate():
            date_label.setStyleSheet("color: #667eea;")

        if menu_data:
            items = menu_data.get('menu_items', {})
            card_layout.addWidget(QLabel(f"<b>Çorba:</b> {items.get('Corbasi', '-')}"))
            card_layout.addWidget(QLabel(f"<b>Ana Yemek:</b> {items.get('Ana_Yemek', '-')}"))
            card_layout.addWidget(QLabel(f"<b>Yan Yemek:</b> {items.get('Yan_Yemek', '-')}"))
            card_layout.addWidget(QLabel(f"<b>Tatlı:</b> {items.get('Tatli', '-')}"))
            
            card_layout.addStretch()

            # Katılım butonları (geçmiş günler için gösterme)
            if q_date >= QDate.currentDate():
                btn_layout = QHBoxLayout()
                yes_btn = QPushButton("Geleceğim")
                no_btn = QPushButton("Gelmeyeceğim")
                
                yes_btn.clicked.connect(lambda _, d=menu_data['date']: self.select_attendance(d, True, card))
                no_btn.clicked.connect(lambda _, d=menu_data['date']: self.select_attendance(d, False, card))
                
                btn_layout.addWidget(yes_btn)
                btn_layout.addWidget(no_btn)
                card_layout.addLayout(btn_layout)
        else:
            card_layout.addStretch()
            no_menu_label = QLabel("Bu gün için menü planlanmamış.")
            no_menu_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            card_layout.addWidget(no_menu_label)
            card_layout.addStretch()
            
        return card

    def select_attendance(self, date_str, will_attend, card):
        self.attendance_selections[date_str] = will_attend
        # Kartın stilini güncelle
        for w in card.parentWidget().findChildren(QFrame):
            w.setStyleSheet("#Card { background-color: white; border: 1px solid #e0e0e0; }") # Reset all
        
        style = "#Card { background-color: %s; border: 2px solid %s; }"
        if will_attend:
            card.setStyleSheet(style % ("#e8f5e9", "#4caf50")) # Yeşil
        else:
            card.setStyleSheet(style % ("#ffebee", "#f44336")) # Kırmızı
            
    def save_selections(self):
        if not self.attendance_selections:
            QMessageBox.information(self, "Bilgi", "Kaydedilecek bir seçim yapmadınız.")
            return
            
        payload = [{"date": k, "will_attend": v} for k, v in self.attendance_selections.items()]
        
        try:
            response = requests.post(f"{API_URL}/attendance/", headers=self.headers, json=payload)
            response.raise_for_status()
            QMessageBox.information(self, "Başarılı", f"{len(payload)} günlük katılım tercihiniz kaydedildi.")
            self.attendance_selections.clear()
            self.load_menus() # Kart stillerini sıfırlamak için yeniden yükle
        except requests.exceptions.RequestException as e:
            QMessageBox.critical(self, "Hata", f"Seçimler kaydedilemedi: {e}")

    def get_date_range(self):
        if self.active_view == 'daily':
            return self.current_date, self.current_date
        elif self.active_view == 'weekly':
            start_of_week = self.current_date.addDays(-(self.current_date.dayOfWeek() - 1))
            end_of_week = start_of_week.addDays(6)
            return start_of_week, end_of_week
        elif self.active_view == 'monthly':
            start_of_month = QDate(self.current_date.year(), self.current_date.month(), 1)
            end_of_month = QDate(self.current_date.year(), self.current_date.month(), self.current_date.daysInMonth())
            return start_of_month, end_of_month

    def get_period_text(self, start, end):
        if self.active_view == 'daily':
            return start.toString("dd MMMM yyyy")
        elif self.active_view == 'weekly':
            return f"{start.toString('dd MMM')} - {end.toString('dd MMM yyyy')}"
        elif self.active_view == 'monthly':
            return start.toString("MMMM yyyy")

class UserOvertimeTab(QWidget):
    """Kullanıcının fazla mesai talebi oluşturduğu ve geçmiş taleplerini gördüğü tab."""
    def __init__(self, headers, department):
        super().__init__()
        self.headers = headers
        self.department = department
        self.init_ui()
        self.load_my_requests()

    def init_ui(self):
        layout = QHBoxLayout(self)
        
        # Sol Taraf: Yeni Talep Formu
        form_card = QFrame()
        form_card.setObjectName("Card")
        form_layout = QVBoxLayout(form_card)
        
        form_layout.addWidget(QLabel("Yeni Fazla Mesai Talebi Oluştur", styleSheet="font-size: 16px; font-weight: bold;"))
        
        self.form = QFormLayout()
        self.date_edit = QDateEdit(QDate.currentDate())
        self.start_time_edit = QTimeEdit(QTime(18, 0))
        self.end_time_edit = QTimeEdit(QTime(20, 0))
        self.reason_edit = QTextEdit()
        self.reason_edit.setPlaceholderText("Yapılan işin detaylı açıklaması...")
        
        self.form.addRow("Tarih:", self.date_edit)
        self.form.addRow("Başlangıç Saati:", self.start_time_edit)
        self.form.addRow("Bitiş Saati:", self.end_time_edit)
        self.form.addRow("Açıklama:", self.reason_edit)
        
        self.submit_btn = QPushButton("Talep Gönder")
        self.submit_btn.clicked.connect(self.submit_request)
        
        form_layout.addLayout(self.form)
        form_layout.addWidget(self.submit_btn)
        form_layout.addStretch()
        
        layout.addWidget(form_card, 1) # 1/3 oran

        # Sağ Taraf: Geçmiş Talepler Tablosu
        table_card = QFrame()
        table_card.setObjectName("Card")
        table_layout = QVBoxLayout(table_card)
        table_layout.addWidget(QLabel("Geçmiş Taleplerim", styleSheet="font-size: 16px; font-weight: bold;"))
        
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Tarih", "Başlangıç", "Bitiş", "Açıklama", "Durum"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        table_layout.addWidget(self.table)
        layout.addWidget(table_card, 2) # 2/3 oran

    def load_my_requests(self):
        try:
            response = requests.get(f"{API_URL}/api/overtime/me", headers=self.headers)
            response.raise_for_status()
            requests_data = response.json()
            
            self.table.setRowCount(len(requests_data))
            for row, req in enumerate(requests_data):
                self.table.setItem(row, 0, QTableWidgetItem(req['date']))
                self.table.setItem(row, 1, QTableWidgetItem(req['start_time']))
                self.table.setItem(row, 2, QTableWidgetItem(req['end_time']))
                self.table.setItem(row, 3, QTableWidgetItem(req['reason']))
                status_item = QTableWidgetItem(req['status'])
                self.set_status_item_style(status_item, req['status'])
                self.table.setItem(row, 4, status_item)
                
        except requests.exceptions.RequestException as e:
            QMessageBox.critical(self, "Hata", f"Talepler yüklenemedi: {e}")

    def submit_request(self):
        payload = {
            "department": self.department or "Bilinmiyor",
            "date": self.date_edit.date().toString("yyyy-MM-dd"),
            "start_time": self.start_time_edit.time().toString("HH:mm"),
            "end_time": self.end_time_edit.time().toString("HH:mm"),
            "reason": self.reason_edit.toPlainText()
        }
        if not payload["reason"]:
            QMessageBox.warning(self, "Eksik Bilgi", "Açıklama alanı zorunludur.")
            return

        try:
            response = requests.post(f"{API_URL}/api/overtime", headers=self.headers, json=payload)
            if response.status_code == 400:
                 QMessageBox.warning(self, "Hata", response.json().get("detail"))
                 return
            response.raise_for_status()
            QMessageBox.information(self, "Başarılı", "Fazla mesai talebiniz yöneticinize iletildi.")
            self.reason_edit.clear()
            self.load_my_requests()
        except requests.exceptions.RequestException as e:
            QMessageBox.critical(self, "Hata", f"Talep gönderilemedi: {e}")

    def set_status_item_style(self, item, status):
        """Duruma göre hücre arka planını renklendirir."""
        colors = {
            "Onaylandı": "#d4edda",
            "Reddedildi": "#f8d7da",
            "Yönetici Tarafından Reddedildi": "#f8d7da",
            "İK Onayı Bekliyor": "#cce5ff",
            "Yönetici Onayı Bekliyor": "#fff3cd"
        }
        color = colors.get(status, "#ffffff")
        item.setBackground(eval(f"QColor('{color}')"))

# --- ADMIN / YÖNETİCİ PANELLERİ ---

class OvertimeManagementTab(QWidget):
    """Admin ve Yöneticilerin mesai taleplerini yönettiği tab."""
    def __init__(self, headers, is_admin, is_manager):
        super().__init__()
        self.headers = headers
        self.is_admin = is_admin
        self.is_manager = is_manager
        self.init_ui()
        self.load_requests()

    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Filtreleme alanı
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Durum:"))
        self.status_filter = QComboBox()
        self.status_filter.addItems(["Tüm Bekleyenler", "Yönetici Onayı Bekliyor", "İK Onayı Bekliyor", "Tümü", "Onaylandı", "Reddedilenler"])
        filter_layout.addWidget(self.status_filter)
        
        # Admin için ek filtreler
        if self.is_admin:
            filter_layout.addWidget(QLabel("Kullanıcı:"))
            self.user_filter = QComboBox()
            filter_layout.addWidget(self.user_filter)
            
            filter_layout.addWidget(QLabel("Departman:"))
            self.department_filter = QComboBox()
            filter_layout.addWidget(self.department_filter)
            self.populate_admin_filters()

        self.filter_btn = QPushButton("Filtrele")
        self.filter_btn.clicked.connect(self.load_requests)
        filter_layout.addWidget(self.filter_btn)
        filter_layout.addStretch()
        layout.addLayout(filter_layout)

        # Talepler tablosu
        self.table = QTableWidget(0, 8)
        self.table.setHorizontalHeaderLabels(["ID", "Personel", "Departman", "Tarih", "Saatler", "Açıklama", "Durum", "İşlemler"])
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setColumnHidden(0, True) # ID'yi gizle
        layout.addWidget(self.table)
        
    def populate_admin_filters(self):
        try:
            response = requests.get(f"{API_URL}/api/users", headers=self.headers)
            response.raise_for_status()
            users = response.json()
            
            self.user_filter.addItem("Tümü", userData=None)
            for user in users:
                self.user_filter.addItem(user['username'], userData=user['id'])
            
            departments = sorted(list(set(u['department'] for u in users if u['department'])))
            self.department_filter.addItem("Tümü", userData=None)
            for dep in departments:
                self.department_filter.addItem(dep, userData=dep)

        except requests.exceptions.RequestException as e:
            print(f"Filtreler yüklenemedi: {e}")

    def load_requests(self):
        # API endpoint'ini role göre belirle
        if self.is_admin:
            endpoint = "/api/overtime/all"
        elif self.is_manager:
            endpoint = "/api/overtime/manager/all"
        else:
            return

        # Filtre parametrelerini hazırla
        params = {}
        status_map = {
            "Tüm Bekleyenler": "Beklemede",
            "Yönetici Onayı Bekliyor": "Yönetici Onayı Bekliyor",
            "İK Onayı Bekliyor": "İK Onayı Bekliyor",
            "Onaylandı": "Onaylandı",
            "Reddedilenler": "Reddedildi",
        }
        status_text = self.status_filter.currentText()
        if status_text != "Tümü":
            params['status'] = status_map.get(status_text)

        if self.is_admin:
            if self.user_filter.currentIndex() > 0:
                params['user_id'] = self.user_filter.currentData()
            if self.department_filter.currentIndex() > 0:
                params['department'] = self.department_filter.currentData()

        try:
            response = requests.get(f"{API_URL}{endpoint}", headers=self.headers, params=params)
            response.raise_for_status()
            requests_data = response.json()
            self.display_requests(requests_data)
        except requests.exceptions.RequestException as e:
            QMessageBox.critical(self, "Hata", f"Talepler yüklenemedi: {e}")

    def display_requests(self, requests_data):
        self.table.setRowCount(len(requests_data))
        for row, req in enumerate(requests_data):
            self.table.setItem(row, 0, QTableWidgetItem(str(req['id'])))
            self.table.setItem(row, 1, QTableWidgetItem(req['user']['username']))
            self.table.setItem(row, 2, QTableWidgetItem(req['department']))
            self.table.setItem(row, 3, QTableWidgetItem(req['date']))
            self.table.setItem(row, 4, QTableWidgetItem(f"{req['start_time']} - {req['end_time']}"))
            self.table.setItem(row, 5, QTableWidgetItem(req['reason']))
            
            status_item = QTableWidgetItem(req['status'])
            UserOvertimeTab.set_status_item_style(self, status_item, req['status'])
            self.table.setItem(row, 6, status_item)

            # İşlem butonlarını ekle
            self.add_action_buttons(row, req)

    def add_action_buttons(self, row, request):
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        can_manager_act = self.is_manager and not self.is_admin and request['status'] == 'Yönetici Onayı Bekliyor'
        can_hr_act = self.is_admin and request['status'] == 'İK Onayı Bekliyor'

        if can_manager_act:
            approve_btn = QPushButton("Onayla")
            reject_btn = QPushButton("Reddet")
            approve_btn.clicked.connect(lambda _, r=request['id']: self.handle_manager_action(r, 'approve'))
            reject_btn.clicked.connect(lambda _, r=request['id']: self.handle_manager_action(r, 'reject'))
            layout.addWidget(approve_btn)
            layout.addWidget(reject_btn)
        elif can_hr_act:
            approve_btn = QPushButton("Onayla")
            reject_btn = QPushButton("Reddet")
            approve_btn.clicked.connect(lambda _, r=request['id']: self.handle_hr_action(r, 'Onaylandı'))
            reject_btn.clicked.connect(lambda _, r=request['id']: self.handle_hr_action(r, 'Reddedildi'))
            layout.addWidget(approve_btn)
            layout.addWidget(reject_btn)
        else:
            layout.addWidget(QLabel("-"))

        self.table.setCellWidget(row, 7, widget)

    def handle_manager_action(self, request_id, action):
        try:
            url = f"{API_URL}/api/overtime/{request_id}/manager_action?action={action}"
            response = requests.put(url, headers=self.headers)
            response.raise_for_status()
            QMessageBox.information(self, "Başarılı", "İşlem tamamlandı.")
            self.load_requests()
        except requests.exceptions.RequestException as e:
            QMessageBox.critical(self, "Hata", f"İşlem gerçekleştirilemedi: {e}")

    def handle_hr_action(self, request_id, status):
        try:
            url = f"{API_URL}/api/overtime/{request_id}/hr_action?status={status}"
            response = requests.put(url, headers=self.headers)
            response.raise_for_status()
            QMessageBox.information(self, "Başarılı", "İşlem tamamlandı.")
            self.load_requests()
        except requests.exceptions.RequestException as e:
            QMessageBox.critical(self, "Hata", f"İşlem gerçekleştirilemedi: {e}")

class AdminDashboardTab(QWidget):
    """Admin'in genel istatistikleri gördüğü dashboard."""
    def __init__(self, headers):
        super().__init__()
        self.headers = headers
        self.init_ui()
        self.load_stats()
        
    def init_ui(self):
        layout = QFormLayout(self)
        layout.setSpacing(20)
        font = QFont("Segoe UI", 18, QFont.Bold)
        
        self.today_selections_label = QLabel("Yükleniyor...")
        self.today_selections_label.setFont(font)
        self.active_users_label = QLabel("Yükleniyor...")
        self.active_users_label.setFont(font)
        
        layout.addRow("Bugünkü Yemek Katılımı:", self.today_selections_label)
        layout.addRow("Toplam Aktif Kullanıcı:", self.active_users_label)

    def load_stats(self):
        try:
            response = requests.get(f"{API_URL}/api/stats/dashboard", headers=self.headers)
            response.raise_for_status()
            stats = response.json()
            self.today_selections_label.setText(str(stats.get('today_selections', 'N/A')))
            self.active_users_label.setText(str(stats.get('active_users', 'N/A')))
        except requests.exceptions.RequestException as e:
            self.today_selections_label.setText("Hata")
            self.active_users_label.setText("Hata")
            print(f"Dashboard istatistikleri yüklenemedi: {e}")

class AdminMenuPlanningTab(QWidget):
    """Admin'in yeni menü oluşturduğu tab."""
    def __init__(self, headers):
        super().__init__()
        self.headers = headers
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        card = QFrame()
        card.setObjectName("Card")
        form_layout = QFormLayout(card)
        
        self.date_edit = QDateEdit(QDate.currentDate())
        self.soup_edit = QLineEdit()
        self.main_course_edit = QLineEdit()
        self.side_dish_edit = QLineEdit()
        self.dessert_edit = QLineEdit()
        
        form_layout.addRow("Tarih:", self.date_edit)
        form_layout.addRow("Çorba:", self.soup_edit)
        form_layout.addRow("Ana Yemek:", self.main_course_edit)
        form_layout.addRow("Yan Yemek:", self.side_dish_edit)
        form_layout.addRow("Tatlı / Meyve:", self.dessert_edit)
        
        self.submit_btn = QPushButton("Menüyü Kaydet")
        self.submit_btn.clicked.connect(self.submit_menu)
        form_layout.addRow(self.submit_btn)
        
        layout.addWidget(card)
        layout.addStretch()

    def submit_menu(self):
        payload = {
            "date": self.date_edit.date().toString("yyyy-MM-dd"),
            "meal_type": "Öğle Yemeği",
            "menu_items": {
                "Corbasi": self.soup_edit.text(),
                "Ana_Yemek": self.main_course_edit.text(),
                "Yan_Yemek": self.side_dish_edit.text(),
                "Tatli": self.dessert_edit.text()
            }
        }
        if not payload['menu_items']['Ana_Yemek']:
            QMessageBox.warning(self, "Eksik Bilgi", "Ana yemek alanı zorunludur.")
            return

        try:
            response = requests.post(f"{API_URL}/api/menu", headers=self.headers, json=payload)
            if response.status_code == 409:
                QMessageBox.warning(self, "Çakışma", response.json().get("detail"))
                return
            response.raise_for_status()
            QMessageBox.information(self, "Başarılı", "Menü başarıyla eklendi.")
            # Formu temizle
            self.soup_edit.clear()
            self.main_course_edit.clear()
            self.side_dish_edit.clear()
            self.dessert_edit.clear()
        except requests.exceptions.RequestException as e:
            QMessageBox.critical(self, "Hata", f"Menü eklenemedi: {e}")

class AdminReportsTab(QWidget):
    """Admin'in katılım raporlarını gördüğü tab."""
    def __init__(self, headers):
        super().__init__()
        self.headers = headers
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Tarih seçimi
        top_layout = QHBoxLayout()
        top_layout.addWidget(QLabel("Rapor Tarihi:"))
        self.date_edit = QDateEdit(QDate.currentDate())
        top_layout.addWidget(self.date_edit)
        self.show_report_btn = QPushButton("Raporu Göster")
        self.show_report_btn.clicked.connect(self.load_report)
        top_layout.addWidget(self.show_report_btn)
        top_layout.addStretch()
        layout.addLayout(top_layout)
        
        # Rapor tabloları
        report_layout = QHBoxLayout()
        
        # Gelecekler
        attending_card = QFrame()
        attending_card.setObjectName("Card")
        attending_layout = QVBoxLayout(attending_card)
        self.attending_label = QLabel("✔️ Gelecek Personeller (0)")
        self.attending_label.setStyleSheet("font-weight: bold; color: green;")
        self.attending_table = QTableWidget(0, 2)
        self.attending_table.setHorizontalHeaderLabels(["Personel", "Departman"])
        self.attending_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        attending_layout.addWidget(self.attending_label)
        attending_layout.addWidget(self.attending_table)
        
        # Gelmeyecekler
        not_attending_card = QFrame()
        not_attending_card.setObjectName("Card")
        not_attending_layout = QVBoxLayout(not_attending_card)
        self.not_attending_label = QLabel("❌ Gelmeyecek Personeller (0)")
        self.not_attending_label.setStyleSheet("font-weight: bold; color: red;")
        self.not_attending_table = QTableWidget(0, 2)
        self.not_attending_table.setHorizontalHeaderLabels(["Personel", "Departman"])
        self.not_attending_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        not_attending_layout.addWidget(self.not_attending_label)
        not_attending_layout.addWidget(self.not_attending_table)
        
        report_layout.addWidget(attending_card)
        report_layout.addWidget(not_attending_card)
        layout.addLayout(report_layout)

    def load_report(self):
        report_date = self.date_edit.date().toString("yyyy-MM-dd")
        try:
            response = requests.get(f"{API_URL}/api/attendance/{report_date}", headers=self.headers)
            response.raise_for_status()
            report_data = response.json()
            
            attending_list = [item for item in report_data if item['will_attend']]
            not_attending_list = [item for item in report_data if not item['will_attend']]

            self.attending_label.setText(f"✔️ Gelecek Personeller ({len(attending_list)})")
            self.populate_report_table(self.attending_table, attending_list)
            
            self.not_attending_label.setText(f"❌ Gelmeyecek Personeller ({len(not_attending_list)})")
            self.populate_report_table(self.not_attending_table, not_attending_list)

        except requests.exceptions.RequestException as e:
            QMessageBox.critical(self, "Hata", f"Rapor yüklenemedi: {e}")

    def populate_report_table(self, table, data):
        table.setRowCount(len(data))
        for row, item in enumerate(data):
            table.setItem(row, 0, QTableWidgetItem(item['user']['username']))
            table.setItem(row, 1, QTableWidgetItem(item['user']['department'] or 'N/A'))

class AdminUserManagementTab(QWidget):
    """Admin'in kullanıcıları yönettiği tab."""
    def __init__(self, headers):
        super().__init__()
        self.headers = headers
        self.init_ui()
        self.load_users()

    def init_ui(self):
        layout = QVBoxLayout(self)
        
        add_user_btn = QPushButton("+ Yeni Kullanıcı Ekle")
        add_user_btn.clicked.connect(self.open_user_dialog)
        layout.addWidget(add_user_btn, 0, Qt.AlignmentFlag.AlignLeft)
        
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Kullanıcı Adı", "Email", "Departman", "Yöneticisi", "İşlemler"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.table)
        
    def load_users(self):
        try:
            response = requests.get(f"{API_URL}/api/users", headers=self.headers)
            response.raise_for_status()
            users = response.json()
            self.table.setRowCount(len(users))
            for row, user in enumerate(users):
                self.table.setItem(row, 0, QTableWidgetItem(user['username']))
                self.table.setItem(row, 1, QTableWidgetItem(user['email']))
                self.table.setItem(row, 2, QTableWidgetItem(user['department'] or '-'))
                self.table.setItem(row, 3, QTableWidgetItem(user['manager']['username'] if user.get('manager') else 'Yok'))
                self.add_user_action_buttons(row, user)
        except requests.exceptions.RequestException as e:
            QMessageBox.critical(self, "Hata", f"Kullanıcılar yüklenemedi: {e}")
            
    def add_user_action_buttons(self, row, user):
        widget = QWidget()
        layout = QHBoxLayout(widget)
        
        edit_btn = QPushButton("Düzenle")
        delete_btn = QPushButton("Sil")
        delete_btn.setStyleSheet("background-color: #ef4444;")
        
        edit_btn.clicked.connect(lambda _, u=user: self.open_user_dialog(u))
        delete_btn.clicked.connect(lambda _, u_id=user['id'], u_name=user['username']: self.delete_user(u_id, u_name))
        
        layout.addWidget(edit_btn)
        layout.addWidget(delete_btn)
        self.table.setCellWidget(row, 4, widget)

    def open_user_dialog(self, user=None):
        dialog = UserFormDialog(self.headers, user, self)
        dialog.user_saved.connect(self.load_users)
        dialog.exec()
        
    def delete_user(self, user_id, username):
        reply = QMessageBox.question(self, "Kullanıcı Sil", f"'{username}' adlı kullanıcıyı silmek istediğinize emin misiniz?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                response = requests.delete(f"{API_URL}/api/users/{user_id}", headers=self.headers)
                response.raise_for_status()
                QMessageBox.information(self, "Başarılı", f"'{username}' silindi.")
                self.load_users()
            except requests.exceptions.RequestException as e:
                QMessageBox.critical(self, "Hata", f"Kullanıcı silinemedi: {e}")

class UserFormDialog(QDialog):
    """Yeni kullanıcı ekleme ve düzenleme için diyalog penceresi."""
    from PySide6.QtCore import Signal
    user_saved = Signal()

    def __init__(self, headers, user=None, parent=None):
        super().__init__(parent)
        self.headers = headers
        self.user = user
        self.is_edit_mode = user is not None
        
        self.setWindowTitle("Kullanıcı Düzenle" if self.is_edit_mode else "Yeni Kullanıcı Ekle")
        self.setMinimumWidth(400)
        self.setStyleSheet(STYLE)
        
        self.init_ui()
        self.populate_form()
        self.load_managers()

    def init_ui(self):
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        
        self.username_edit = QLineEdit()
        self.email_edit = QLineEdit()
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.department_edit = QLineEdit()
        self.manager_combo = QComboBox()

        form_layout.addRow("Kullanıcı Adı:", self.username_edit)
        form_layout.addRow("E-posta:", self.email_edit)
        if not self.is_edit_mode:
            form_layout.addRow("Şifre:", self.password_edit)
        form_layout.addRow("Departman:", self.department_edit)
        form_layout.addRow("Yöneticisi:", self.manager_combo)
        
        self.save_btn = QPushButton("Kaydet")
        self.save_btn.clicked.connect(self.save_user)
        
        layout.addLayout(form_layout)
        layout.addWidget(self.save_btn)

    def populate_form(self):
        if self.is_edit_mode:
            self.username_edit.setText(self.user['username'])
            self.username_edit.setReadOnly(True)
            self.email_edit.setText(self.user['email'])
            self.department_edit.setText(self.user['department'] or "")
        else:
            self.password_edit.setPlaceholderText("Yeni kullanıcı için zorunlu")

    def load_managers(self):
        try:
            response = requests.get(f"{API_URL}/api/users", headers=self.headers)
            response.raise_for_status()
            users = response.json()
            
            self.manager_combo.addItem("Yönetici Yok", userData=None)
            for u in users:
                # Kendisini yöneticisi olarak atamasını engelle
                if self.is_edit_mode and u['id'] == self.user['id']:
                    continue
                self.manager_combo.addItem(u['username'], userData=u['id'])

            if self.is_edit_mode and self.user.get('manager_id'):
                index = self.manager_combo.findData(self.user['manager_id'])
                if index != -1:
                    self.manager_combo.setCurrentIndex(index)
        except requests.exceptions.RequestException as e:
            QMessageBox.warning(self, "Hata", f"Yönetici listesi yüklenemedi: {e}")

    def save_user(self):
        payload = {
            "email": self.email_edit.text(),
            "department": self.department_edit.text(),
            "manager_id": self.manager_combo.currentData()
        }
        
        if self.is_edit_mode:
            url = f"{API_URL}/api/users/{self.user['id']}"
            method = 'PUT'
        else:
            payload['username'] = self.username_edit.text()
            payload['password'] = self.password_edit.text()
            if not payload['username'] or not payload['password']:
                QMessageBox.warning(self, "Eksik Bilgi", "Yeni kullanıcı için kullanıcı adı ve şifre zorunludur.")
                return
            url = f"{API_URL}/api/users/"
            method = 'POST'
            
        try:
            response = requests.request(method, url, headers=self.headers, json=payload)
            if response.status_code == 400:
                QMessageBox.warning(self, "Hata", response.json().get("detail"))
                return
            response.raise_for_status()
            QMessageBox.information(self, "Başarılı", "Kullanıcı bilgileri kaydedildi.")
            self.user_saved.emit()
            self.accept()
        except requests.exceptions.RequestException as e:
            QMessageBox.critical(self, "Hata", f"Kullanıcı kaydedilemedi: {e}")

# --- Uygulamayı Başlatma ---
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
