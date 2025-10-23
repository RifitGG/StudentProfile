# client.py

import sys
import os
import json
import shutil
import requests
from datetime import datetime, timedelta, date


from PySide6.QtWidgets import (
    QApplication, QWidget, QHBoxLayout, QVBoxLayout, QLabel, QLineEdit, QPushButton,
    QMessageBox, QTableWidget, QTableWidgetItem, QComboBox, QFileDialog, QSplitter,
    QListWidget, QListWidgetItem, QTextEdit, QStackedWidget, QFormLayout, QSizePolicy,
    QCalendarWidget, QCheckBox, QSpinBox, QGroupBox, QGridLayout,
    QSystemTrayIcon, QMenu
)
try:
    from PySide6.QtWidgets import QAction
except Exception:
    from PySide6.QtGui import QAction

from PySide6.QtGui import QPixmap, QTextCharFormat, QBrush, QColor, QIcon
from PySide6.QtCore import Qt, QTimer, QDate, QPropertyAnimation, QRect

import config

API = getattr(config, "API_URL", "http://127.0.0.1:5000")
AVATAR_DIR = getattr(config, "AVATAR_DIR", "avatars")
SETTINGS_FILE = "settings.json"

DEFAULT_SETTINGS = {
    "poll_interval_sec": 60,
    "notify_homework": True,
    "notify_schedule": True,
    "notify_grades": True,
    "notify_sound": True,
    "enable_tray": True,
    "auto_poll_after_login": True,
    "notification_duration_sec": 6
}


def ensure_avatar_dir():
    p = os.path.join(os.getcwd(), AVATAR_DIR)
    os.makedirs(p, exist_ok=True)
    return p

def save_avatar(student_id: int, src_path: str) -> str:
    folder = ensure_avatar_dir()
    dest = os.path.join(folder, f"{student_id}.png")
    try:
        pix = QPixmap(src_path)
        pix = pix.scaled(512, 512, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        pix.save(dest, "PNG")
    except Exception:
        shutil.copyfile(src_path, dest)
    return dest

def avatar_path(student_id: int):
    p = os.path.join(ensure_avatar_dir(), f"{student_id}.png")
    return p if os.path.exists(p) else None

def parse_date_safe(s):
    if not s:
        return None
    try:
        return datetime.fromisoformat(s)
    except Exception:
        for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M", "%d.%m.%Y"):
            try:
                return datetime.strptime(s, fmt)
            except Exception:
                continue
    return None

def qdate_from_dt(dt: datetime):
    return QDate(dt.year, dt.month, dt.day)

def set_format_for_date(calendar: QCalendarWidget, qdate: QDate, color_hex: str):
    fmt = QTextCharFormat()
    fmt.setBackground(QBrush(QColor(color_hex)))
    calendar.setDateTextFormat(qdate, fmt)

def clear_all_formats(calendar: QCalendarWidget):
    today = date.today()
    for d in range(-365, 366):
        dt = today + timedelta(days=d)
        calendar.setDateTextFormat(QDate(dt.year, dt.month, dt.day), QTextCharFormat())

def api_get(path, params=None, timeout=10):
    return requests.get(API + path, params=params, timeout=timeout)

def api_post_json(path, data, timeout=10):
    return requests.post(API + path, json=data, timeout=timeout)


def load_settings():
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                s = json.load(f)
            for k, v in DEFAULT_SETTINGS.items():
                if k not in s:
                    s[k] = v
            return s
        except Exception:
            return DEFAULT_SETTINGS.copy()
    return DEFAULT_SETTINGS.copy()

def save_settings(settings):
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print("Failed to save settings:", e)


class NotificationPopup(QWidget):
    PADDING = 12
    WIDTH = 360
    HEIGHT = 90

    _active = []

    def __init__(self, title: str, message: str, duration: int = 6, parent=None):
        super().__init__(parent, Qt.Window | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.duration = duration
        self.title = title
        self.message = message
        self._build_ui()
        self._position()
        NotificationPopup._active.append(self)
        self.show()
        self._animate_in()
        QTimer.singleShot(self.duration * 1000, self.close_popup)

    def _build_ui(self):
        self.resize(self.WIDTH, self.HEIGHT)
        self.main = QVBoxLayout(self)
        self.main.setContentsMargins(8, 8, 8, 8)
        container = QWidget(self)
        container.setStyleSheet("""
            background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 #ffffff, stop:1 #fff0f6);
            border: 1px solid #ffd6ea;
            border-radius: 10px;
        """)
        c_layout = QVBoxLayout(container)
        t = QLabel(self.title)
        t.setStyleSheet("font-weight:700; color:#ff2e6e;")
        m = QLabel(self.message)
        m.setWordWrap(True)
        m.setStyleSheet("color:#40192a;")
        c_layout.addWidget(t)
        c_layout.addWidget(m)
        self.main.addWidget(container)

    def _position(self):
        screen = QApplication.primaryScreen()
        geo = screen.availableGeometry()
        margin = 16
        x = geo.x() + geo.width() - self.WIDTH - margin
        y = geo.y() + geo.height() - self.HEIGHT - margin
        for p in NotificationPopup._active:
            if p is self:
                continue
            y -= (self.HEIGHT + 10)
        self.move(x, y)

    def _animate_in(self):
        screen = QApplication.primaryScreen()
        geo = screen.availableGeometry()
        start_x = geo.x() + geo.width() + 10
        end_x = self.x()
        y = self.y()
        self.setGeometry(start_x, y, self.WIDTH, self.HEIGHT)
        anim = QPropertyAnimation(self, b"geometry")
        anim.setDuration(260)
        anim.setStartValue(QRect(start_x, y, self.WIDTH, self.HEIGHT))
        anim.setEndValue(QRect(end_x, y, self.WIDTH, self.HEIGHT))
        anim.start()
        self._anim = anim

    def close_popup(self):
        try:
            if self in NotificationPopup._active:
                NotificationPopup._active.remove(self)
        except Exception:
            pass
        self.close()
        for p in NotificationPopup._active:
            p._reposition_after_close()

    def _reposition_after_close(self):
        screen = QApplication.primaryScreen()
        geo = screen.availableGeometry()
        margin = 16
        target_x = geo.x() + geo.width() - self.WIDTH - margin
        idx = NotificationPopup._active.index(self)
        target_y = geo.y() + geo.height() - self.HEIGHT - margin - idx * (self.HEIGHT + 10)
        anim = QPropertyAnimation(self, b"geometry")
        anim.setDuration(240)
        anim.setStartValue(self.geometry())
        anim.setEndValue(QRect(target_x, target_y, self.WIDTH, self.HEIGHT))
        anim.start()
        self._anim = anim


class LoginRegisterWidget(QWidget):
    def __init__(self, on_success):
        super().__init__()
        self.on_success = on_success
        self._build_ui()

    def _build_ui(self):
        self.setStyleSheet("""
            QLabel#title { font-size:18px; font-weight:700; color:#ff3d7a; }
            QLineEdit { background:#fff6fb; border:1px solid #ffd6ea; padding:6px; border-radius:6px; }
            QPushButton { background:#ff8fb6; color:white; padding:8px; border-radius:8px; }
        """)
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        title = QLabel("Личный кабинет студента")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        form = QFormLayout()
        self.input_name = QLineEdit(); self.input_name.setPlaceholderText("Иванов Иван Иванович")
        self.input_pass = QLineEdit(); self.input_pass.setEchoMode(QLineEdit.Password); self.input_pass.setPlaceholderText("Пароль")
        form.addRow("ФИО:", self.input_name); form.addRow("Пароль:", self.input_pass)
        layout.addLayout(form)

        btn_login = QPushButton("Войти"); btn_login.clicked.connect(self.on_login)
        btn_reg = QPushButton("Зарегистрироваться"); btn_reg.clicked.connect(self.on_register)

        reg_opts = QHBoxLayout()
        self.combo_program = QComboBox(); self.combo_program.addItems(["ИСиП", "Банковское дело", "Юриспруденция"])
        self.combo_year = QComboBox(); self.combo_year.addItems(["1","2","3","4"])
        reg_opts.addWidget(self.combo_program); reg_opts.addWidget(self.combo_year)

        layout.addWidget(btn_login); layout.addLayout(reg_opts); layout.addWidget(btn_reg)
        layout.addStretch(1)

    def on_login(self):
        name = self.input_name.text().strip(); pwd = self.input_pass.text().strip()
        if not name or not pwd:
            QMessageBox.warning(self, "Ошибка", "Введите ФИО и пароль"); return
        try:
            resp = api_post_json("/login", {"full_name": name, "password": pwd})
        except Exception as e:
            QMessageBox.critical(self, "Ошибка сети", str(e)); return
        if resp.status_code == 200:
            data = resp.json(); self.on_success(data.get("id"), data.get("full_name"))
        else:
            try: err = resp.json().get("error", resp.text)
            except Exception: err = resp.text
            QMessageBox.warning(self, "Ошибка", err)

    def on_register(self):
        name = self.input_name.text().strip(); pwd = self.input_pass.text().strip()
        program = self.combo_program.currentText(); year = int(self.combo_year.currentText())
        if not name or not pwd:
            QMessageBox.warning(self, "Ошибка", "Введите ФИО и пароль для регистрации"); return
        try:
            resp = api_post_json("/register", {"full_name": name, "program": program, "year": year, "password": pwd})
        except Exception as e:
            QMessageBox.critical(self, "Ошибка сети", str(e)); return
        if resp.status_code == 200:
            data = resp.json(); QMessageBox.information(self, "Успех", f"Зарегистрировано id={data.get('id')}")
        else:
            try: err = resp.json().get("error", resp.text)
            except Exception: err = resp.text
            QMessageBox.warning(self, "Ошибка", err)


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.student_id = None
        self.full_name = None
        self.program = None
        self.year = None

        self.homework_list = []
        self.schedule_list = []
        self.grades_list = []

        self.attachment_to_send = None

        self.settings = load_settings()

        self.poll_timer = QTimer(self)
        self.poll_timer.timeout.connect(self.poll_updates)

        self._snapshot = {"homework": "", "schedule": "", "grades": ""}
        self._prev_snapshot = {"homework": "", "schedule": "", "grades": ""}

        self._first_seed_done = False

        self.tray = None

        self._build_ui()
        self.login_widget = LoginRegisterWidget(self.on_logged_in)
        self.show_login_dialog()

        if self.settings.get("enable_tray", True):
            self._init_tray()

    def _build_ui(self):
        self.setWindowTitle("ЛК Студента")
        self.resize(1200, 760)
        self.setStyleSheet("""
            QWidget { background: #fff0f6; color: #40192a; font-family: Arial, Helvetica, sans-serif; }
            QListWidget { background: #fff6fb; border: 1px solid #ffd6ea; border-radius: 8px; padding:6px; }
            QListWidget::item:selected { background: #ff8fb6; color: white; border-radius:6px; }
            QLabel#title { font-size:18px; font-weight:700; color:#ff3d7a; }
            QPushButton { background: #ff8fb6; color: white; border-radius:8px; padding:8px; }
            QLineEdit { background: #fff6fb; border:1px solid #ffd6ea; padding:6px; border-radius:6px; }
            QTableWidget { background: white; border-radius:8px; }
            QHeaderView::section { background: #ffd6ea; padding:6px; border: none; }
        """)

        main_layout = QHBoxLayout(self)
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)

        left = QWidget(); left_layout = QVBoxLayout(left); left_layout.setContentsMargins(10,10,10,10)
        self.avatar_label = QLabel(); self.avatar_label.setFixedSize(100,100); self.avatar_label.setStyleSheet("background:white; border-radius:8px;"); self.avatar_label.setAlignment(Qt.AlignCenter)
        self.name_label = QLabel("Не авторизован"); self.name_label.setObjectName("title")
        self.small_label = QLabel("")
        self.btn_upload_avatar = QPushButton("Загрузить аватар"); self.btn_upload_avatar.clicked.connect(self.upload_avatar); self.btn_upload_avatar.setVisible(False)
        self.btn_logout = QPushButton("Выйти"); self.btn_logout.clicked.connect(self.logout); self.btn_logout.setVisible(False)
        left_layout.addWidget(self.avatar_label, alignment=Qt.AlignHCenter); left_layout.addWidget(self.name_label, alignment=Qt.AlignHCenter); left_layout.addWidget(self.small_label, alignment=Qt.AlignHCenter)
        left_layout.addWidget(self.btn_upload_avatar); left_layout.addWidget(self.btn_logout); left_layout.addSpacing(12)

        self.nav = QListWidget()
        for name in ["Обзор", "Календарь", "Расписание", "Домашние задания", "Оценки", "Настройки"]:
            self.nav.addItem(QListWidgetItem(name))
        self.nav.currentRowChanged.connect(self.on_nav_changed)
        left_layout.addWidget(self.nav)
        left_layout.addStretch(1)

        splitter.addWidget(left)
        splitter.setCollapsible(0, False)

        self.stack = QStackedWidget(); splitter.addWidget(self.stack); splitter.setStretchFactor(1,1)

        page_overview = QWidget(); ov_layout = QVBoxLayout(page_overview)
        lbl = QLabel("Обзор"); lbl.setObjectName("title")
        status_h = QHBoxLayout(); self.lbl_api_status = QLabel("API: —"); self.lbl_last_update = QLabel("Последнее обновление: —"); status_h.addWidget(self.lbl_api_status); status_h.addStretch(1); status_h.addWidget(self.lbl_last_update)
        self.overview_text = QLabel("Пожалуйста, войдите в систему."); self.overview_text.setWordWrap(True)
        self.overview_details = QTextEdit(); self.overview_details.setReadOnly(True)
        ov_layout.addWidget(lbl); ov_layout.addLayout(status_h); ov_layout.addWidget(self.overview_text); ov_layout.addWidget(self.overview_details); ov_layout.addStretch(1)
        self.stack.addWidget(page_overview)

        page_calendar = QWidget(); cal_layout = QHBoxLayout(page_calendar)
        left_cal = QVBoxLayout(); self.calendar = QCalendarWidget(); self.calendar.setGridVisible(True); self.calendar.selectionChanged.connect(self.on_calendar_selected); left_cal.addWidget(self.calendar); cal_layout.addLayout(left_cal,1)
        right_cal = QVBoxLayout(); lbl_day = QLabel("События на выбранную дату:"); self.list_day = QListWidget(); right_cal.addWidget(lbl_day); right_cal.addWidget(self.list_day); cal_layout.addLayout(right_cal,1); self.stack.addWidget(page_calendar)

        page_schedule = QWidget(); sch_layout = QVBoxLayout(page_schedule)
        top_controls = QHBoxLayout(); top_controls.addWidget(QLabel("Показать день:"))
        self.combo_day = QComboBox(); self.combo_day.addItems(["Все", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])
        top_controls.addWidget(self.combo_day); btn_filter = QPushButton("Загрузить"); btn_filter.clicked.connect(self.load_schedule); top_controls.addWidget(btn_filter); top_controls.addStretch()
        sch_layout.addLayout(top_controls)
        self.tbl_schedule = QTableWidget(0,4); self.tbl_schedule.setHorizontalHeaderLabels(["День","Время","Предмет","Аудитория/Преподаватель"]); sch_layout.addWidget(self.tbl_schedule); self.stack.addWidget(page_schedule)

        page_hw = QWidget(); hw_layout = QVBoxLayout(page_hw)
        hw_top = QHBoxLayout(); self.hw_search = QLineEdit(); self.hw_search.setPlaceholderText("Поиск по заголовку или описанию..."); self.hw_search.textChanged.connect(self.filter_homework_local)
        hw_top.addWidget(self.hw_search); btn_refresh_hw = QPushButton("Обновить"); btn_refresh_hw.clicked.connect(self.load_homework); hw_top.addWidget(btn_refresh_hw); hw_layout.addLayout(hw_top)
        self.tbl_hw = QTableWidget(0,5); self.tbl_hw.setHorizontalHeaderLabels(["ID","Заголовок","Описание","Срок","Файл"]); hw_layout.addWidget(self.tbl_hw)
        push_box = QHBoxLayout(); self.input_hw_title = QLineEdit(); self.input_hw_title.setPlaceholderText("Заголовок")
        self.input_hw_desc = QLineEdit(); self.input_hw_desc.setPlaceholderText("Описание")
        self.input_hw_due = QLineEdit(); self.input_hw_due.setPlaceholderText("Срок YYYY-MM-DD")
        self.lbl_attach = QLineEdit(); self.lbl_attach.setReadOnly(True)
        btn_attach = QPushButton("Прикрепить файл"); btn_attach.clicked.connect(self.attach_file)
        btn_send = QPushButton("Отправить ДЗ"); btn_send.clicked.connect(self.push_homework)
        push_box.addWidget(self.input_hw_title); push_box.addWidget(self.input_hw_desc); push_box.addWidget(self.input_hw_due)
        push_box.addWidget(self.lbl_attach); push_box.addWidget(btn_attach); push_box.addWidget(btn_send)
        hw_layout.addLayout(push_box); self.stack.addWidget(page_hw)

        page_gr = QWidget(); gr_layout = QVBoxLayout(page_gr)
        self.tbl_gr = QTableWidget(0,3); self.tbl_gr.setHorizontalHeaderLabels(["Предмет","Оценка","Комментарий"]); gr_layout.addWidget(self.tbl_gr)
        btn_refresh_gr = QPushButton("Обновить оценки"); btn_refresh_gr.clicked.connect(self.load_grades); gr_layout.addWidget(btn_refresh_gr); self.stack.addWidget(page_gr)

        page_set = QWidget(); set_layout = QVBoxLayout(page_set)
        set_layout.addWidget(QLabel("Настройки приложения"))
        grp = QGroupBox("Опрос сервера и уведомления"); g_l = QGridLayout()
        g_l.addWidget(QLabel("Интервал опроса (сек):"), 0, 0)
        self.spin_interval = QSpinBox(); self.spin_interval.setRange(5, 3600); self.spin_interval.setValue(self.settings.get("poll_interval_sec", DEFAULT_SETTINGS["poll_interval_sec"]))
        g_l.addWidget(self.spin_interval, 0, 1)
        self.chk_notify_hw = QCheckBox("Уведомления о новых/изменённых ДЗ"); self.chk_notify_hw.setChecked(self.settings.get("notify_homework", True))
        self.chk_notify_sched = QCheckBox("Уведомления об изменениях в расписании"); self.chk_notify_sched.setChecked(self.settings.get("notify_schedule", True))
        self.chk_notify_gr = QCheckBox("Уведомления об изменениях оценок"); self.chk_notify_gr.setChecked(self.settings.get("notify_grades", True))
        self.chk_notify_sound = QCheckBox("Звуковой сигнал при уведомлении"); self.chk_notify_sound.setChecked(self.settings.get("notify_sound", True))
        self.chk_enable_tray = QCheckBox("Включить трей"); self.chk_enable_tray.setChecked(self.settings.get("enable_tray", True))
        g_l.addWidget(self.chk_notify_hw, 1, 0, 1, 2)
        g_l.addWidget(self.chk_notify_sched, 2, 0, 1, 2)
        g_l.addWidget(self.chk_notify_gr, 3, 0, 1, 2)
        g_l.addWidget(self.chk_notify_sound, 4, 0, 1, 2)
        g_l.addWidget(self.chk_enable_tray, 5, 0, 1, 2)
        grp.setLayout(g_l); set_layout.addWidget(grp)
        btn_row = QHBoxLayout()
        btn_save_set = QPushButton("Сохранить настройки"); btn_save_set.clicked.connect(self.save_settings_from_ui)
        btn_reset_set = QPushButton("Восстановить по умолчанию"); btn_reset_set.clicked.connect(self.reset_settings)
        btn_row.addWidget(btn_save_set); btn_row.addWidget(btn_reset_set); btn_row.addStretch()
        set_layout.addLayout(btn_row); set_layout.addStretch(1)
        self.stack.addWidget(page_set)

        self.nav.setCurrentRow(0); self.stack.setCurrentIndex(0)


    def _init_tray(self):
        if not QSystemTrayIcon.isSystemTrayAvailable():
            print("System tray is not available on this system.")
            return
        default_icon = QIcon()
        if os.path.exists("app_icon.png"):
            default_icon = QIcon("app_icon.png")
        else:
            pm = QPixmap(64,64); pm.fill(QColor("#ff8fb6")); default_icon = QIcon(pm)
        self.tray = QSystemTrayIcon(self)
        self.tray.setIcon(default_icon)
        menu = QMenu()
        act_show = QAction("Показать окно"); act_show.triggered.connect(self.show_normal)
        act_hide = QAction("Скрыть окно"); act_hide.triggered.connect(self.hide)
        act_check = QAction("Проверить обновления"); act_check.triggered.connect(self.poll_updates)
        act_exit = QAction("Выход"); act_exit.triggered.connect(self._on_exit)
        menu.addAction(act_show); menu.addAction(act_hide); menu.addAction(act_check); menu.addSeparator(); menu.addAction(act_exit)
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self._on_tray_activated)
        self.tray.show()

    def _on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.Trigger:
            if self.isVisible():
                self.hide()
            else:
                self.show_normal()

    def show_normal(self):
        self.show(); self.raise_(); self.activateWindow()

    def _on_exit(self):
        QApplication.quit()


    def show_login_dialog(self):
        dlg = QWidget(); dlg.setWindowTitle("Вход / Регистрация"); dlg.setWindowModality(Qt.ApplicationModal)
        layout = QVBoxLayout(dlg); layout.addWidget(self.login_widget); dlg.setFixedSize(480, 340)
        dlg.move(self.geometry().center() - dlg.rect().center()); dlg.show(); self._login_dialog = dlg

    def on_logged_in(self, student_id, full_name):
        self.student_id = student_id; self.full_name = full_name
        self.name_label.setText(full_name); self.small_label.setText("Студент")
        self.btn_logout.setVisible(True); self.btn_upload_avatar.setVisible(True)
        try:
            if hasattr(self, "_login_dialog") and self._login_dialog:
                self._login_dialog.close()
        except Exception:
            pass
        # initial load
        self.load_homework(); self.load_schedule(); self.load_grades(); self.update_profile(); self.highlight_calendar_dates(); self.update_overview()
        self._snapshot["homework"] = json.dumps(self.homework_list, sort_keys=True, ensure_ascii=False)
        self._snapshot["schedule"] = json.dumps(self.schedule_list, sort_keys=True, ensure_ascii=False)
        self._snapshot["grades"] = json.dumps(self.grades_list, sort_keys=True, ensure_ascii=False)
        self._first_seed_done = True
        if self.settings.get("auto_poll_after_login", True):
            self.start_polling()
        if self.settings.get("enable_tray", True) and not self.tray:
            self._init_tray()

    def logout(self):
        self.stop_polling()
        self.student_id = None; self.full_name = None; self.program = None; self.year = None
        self.homework_list = []; self.schedule_list = []; self.grades_list = []
        self.avatar_label.clear(); self.name_label.setText("Не авторизован"); self.small_label.setText("")
        self.btn_logout.setVisible(False); self.btn_upload_avatar.setVisible(False)
        QMessageBox.information(self, "Выход", "Вы вышли из аккаунта.")
        self.show_login_dialog()


    def on_nav_changed(self, idx):
        self.stack.setCurrentIndex(idx)
        page = self.nav.currentItem().text()
        if page == "Календарь": self.on_calendar_selected()
        elif page == "Расписание": self.load_schedule()
        elif page == "Домашние задания": self.load_homework()
        elif page == "Оценки": self.load_grades()
        elif page == "Обзор": self.update_overview()


    def update_profile(self):
        if not self.student_id: return
        try:
            r = api_get(f"/students/{self.student_id}/homework")
            if r.status_code == 200:
                arr = r.json()
                for h in arr:
                    prog = h.get("program")
                    if prog:
                        self.program = prog; break
            if not self.program:
                r2 = api_get(f"/students/{self.student_id}/schedule")
                if r2.status_code == 200:
                    arr2 = r2.json()
                    if arr2:
                        self.program = arr2[0].get("subject", "")
        except Exception:
            pass
        info = []
        if self.program: info.append(f"Направление: {self.program}")
        if self.year: info.append(f"Курс: {self.year}")
        self.small_label.setText(" • ".join(info))
        av = avatar_path(self.student_id)
        if av:
            pix = QPixmap(av).scaled(100,100, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.avatar_label.setPixmap(pix)

    def upload_avatar(self):
        if not self.student_id:
            QMessageBox.warning(self, "Ошибка", "Сначала войдите в систему"); return
        path, _ = QFileDialog.getOpenFileName(self, "Выберите изображение для аватара", filter="Images (*.png *.jpg *.jpeg)")
        if not path: return
        dest = save_avatar(self.student_id, path)
        pix = QPixmap(dest).scaled(100,100, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.avatar_label.setPixmap(pix)
        QMessageBox.information(self, "Успех", f"Аватар сохранён локально: {dest}")


    def load_schedule(self):
        if not self.student_id:
            QMessageBox.warning(self, "Ошибка", "Нужно войти."); return
        day = self.combo_day.currentText(); params = None if day == "Все" else {"day": day}
        try:
            r = api_get(f"/students/{self.student_id}/schedule", params=params)
            if r.status_code != 200:
                QMessageBox.warning(self, "Ошибка", r.text); return
            data = r.json(); self.schedule_list = data
            self.tbl_schedule.setRowCount(0)
            for it in data:
                row = self.tbl_schedule.rowCount(); self.tbl_schedule.insertRow(row)
                self.tbl_schedule.setItem(row, 0, QTableWidgetItem(it.get("week_day",""))); self.tbl_schedule.setItem(row, 1, QTableWidgetItem(it.get("time","")))
                self.tbl_schedule.setItem(row, 2, QTableWidgetItem(it.get("subject",""))); self.tbl_schedule.setItem(row, 3, QTableWidgetItem((it.get("classroom","") or "") + " / " + (it.get("teacher","") or "")))
            self._snapshot["schedule"] = json.dumps(self.schedule_list, sort_keys=True, ensure_ascii=False)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))


    def load_homework(self):
        if not self.student_id: return
        try:
            r = api_get(f"/students/{self.student_id}/homework")
            if r.status_code != 200: return
            data = r.json(); self.homework_list = data; self.populate_homework_table(data); self.highlight_calendar_dates()
            self._snapshot["homework"] = json.dumps(self.homework_list, sort_keys=True, ensure_ascii=False)
        except Exception as e:
            print("load_homework error:", e)

    def populate_homework_table(self, data):
        self.tbl_hw.setRowCount(0)
        query = self.hw_search.text().lower().strip() if hasattr(self, "hw_search") else ""
        now = datetime.now()
        for h in data:
            title = (h.get("title") or ""); desc = (h.get("description") or "")
            if query and (query not in title.lower() and query not in desc.lower()): continue
            row = self.tbl_hw.rowCount(); self.tbl_hw.insertRow(row)
            self.tbl_hw.setItem(row, 0, QTableWidgetItem(str(h.get("id",""))))
            self.tbl_hw.setItem(row, 1, QTableWidgetItem(title)); self.tbl_hw.setItem(row, 2, QTableWidgetItem(desc))
            due_dt = parse_date_safe(h.get("due_date")); due_text = due_dt.strftime("%Y-%m-%d %H:%M") if due_dt else (h.get("due_date") or "")
            self.tbl_hw.setItem(row, 3, QTableWidgetItem(due_text))
            att = h.get("attachment") or ""
            if att:
                btn = QPushButton("Скачать"); hid = h.get("id"); btn.clicked.connect(lambda _, hid=hid: self.download_attachment(hid)); self.tbl_hw.setCellWidget(row, 4, btn)
            else:
                self.tbl_hw.setItem(row, 4, QTableWidgetItem(""))

            if due_dt:
                if due_dt < now: color = "#ffd6da"
                elif due_dt <= now + timedelta(hours=24): color = "#fff0d6"
                else: color = "#ecffd9"
                for col in range(5):
                    item = self.tbl_hw.item(row, col)
                    if item: item.setBackground(QBrush(QColor(color)))
                    else:
                        w = self.tbl_hw.cellWidget(row, col)
                        if w: w.setStyleSheet(f"background:{color}; border-radius:6px;")
        self.tbl_hw.resizeColumnsToContents()

    def filter_homework_local(self):
        if hasattr(self, "homework_list"):
            self.populate_homework_table(self.homework_list)

    def attach_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Прикрепить файл")
        if path:
            self.lbl_attach.setText(path); self.attachment_to_send = path

    def push_homework(self):
        if not self.student_id:
            QMessageBox.warning(self, "Ошибка", "Нужно войти."); return
        title = self.input_hw_title.text().strip(); desc = self.input_hw_desc.text().strip(); due = self.input_hw_due.text().strip()
        if not title:
            QMessageBox.warning(self, "Ошибка", "Введите заголовок"); return
        try:
            if hasattr(self, "attachment_to_send") and self.attachment_to_send and os.path.exists(self.attachment_to_send):
                with open(self.attachment_to_send, "rb") as f:
                    files = {"file": f}; data = {"title": title, "description": desc, "due_date": due}
                    r = requests.post(f"{API}/students/{self.student_id}/homework", data=data, files=files, timeout=30)
            else:
                r = requests.post(f"{API}/students/{self.student_id}/homework", json={"title": title, "description": desc, "due_date": due}, timeout=20)
            if r.status_code == 200:
                QMessageBox.information(self, "Успех", "Задание отправлено"); self.input_hw_title.clear(); self.input_hw_desc.clear(); self.input_hw_due.clear(); self.lbl_attach.clear(); self.attachment_to_send = None
                self.load_homework(); self.update_overview()
            else:
                try: err = r.json().get("error", r.text)
                except Exception: err = r.text
                QMessageBox.warning(self, "Ошибка", err)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка сети", str(e))

    def download_attachment(self, hw_id):
        try:
            r = requests.get(f"{API}/homework/{hw_id}/download", stream=True, timeout=30)
            if r.status_code == 200:
                cd = r.headers.get("Content-Disposition", ""); fname = None
                if "filename=" in cd: fname = cd.split("filename=")[-1].strip('"; ')
                if not fname: fname = f"attachment_{hw_id}"
                save = QFileDialog.getSaveFileName(self, "Сохранить файл", fname)[0]
                if save:
                    with open(save, "wb") as f:
                        for chunk in r.iter_content(8192): f.write(chunk)
                    QMessageBox.information(self, "Успех", "Файл сохранён")
            else:
                try: err = r.json().get("error", r.text)
                except Exception: err = r.text
                QMessageBox.warning(self, "Ошибка", err)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка сети", str(e))


    def load_grades(self):
        if not self.student_id:
            QMessageBox.warning(self, "Ошибка", "Нужно войти."); return
        try:
            r = api_get(f"/students/{self.student_id}/grades")
            if r.status_code != 200:
                QMessageBox.warning(self, "Ошибка", "Не удалось загрузить оценки"); return
            data = r.json(); self.grades_list = data
            self.tbl_gr.setRowCount(0)
            for g in data:
                row = self.tbl_gr.rowCount(); self.tbl_gr.insertRow(row)
                self.tbl_gr.setItem(row, 0, QTableWidgetItem(g.get("subject",""))); self.tbl_gr.setItem(row, 1, QTableWidgetItem(g.get("grade",""))); self.tbl_gr.setItem(row, 2, QTableWidgetItem(g.get("comment","")))
            self._snapshot["grades"] = json.dumps(self.grades_list, sort_keys=True, ensure_ascii=False)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка сети", str(e))


    def highlight_calendar_dates(self):
        clear_all_formats(self.calendar)
        now = datetime.now()
        for h in getattr(self, "homework_list", []):
            due = parse_date_safe(h.get("due_date"))
            if not due: continue
            qd = qdate_from_dt(due)
            if due < now: color = "#ffd6da"
            elif due <= now + timedelta(hours=24): color = "#fff0d6"
            else: color = "#ecffd9"
            set_format_for_date(self.calendar, qd, color)

    def on_calendar_selected(self):
        if not self.student_id: return
        sel = self.calendar.selectedDate(); pydate = date(sel.year(), sel.month(), sel.day()); weekday_name = pydate.strftime("%A")
        self.list_day.clear()
        try:
            if hasattr(self, "schedule_list") and self.schedule_list:
                items = [it for it in self.schedule_list if it.get("week_day") == weekday_name]
            else:
                r = api_get(f"/students/{self.student_id}/schedule", params={"day": weekday_name}); items = r.json() if r.status_code == 200 else []
            if items:
                self.list_day.addItem("— Пары —")
                for it in items:
                    t = it.get("time",""); subj = it.get("subject",""); cls = it.get("classroom",""); teacher = it.get("teacher","")
                    self.list_day.addItem(f"{t} — {subj} ({cls}) — {teacher}")
            else:
                self.list_day.addItem("Пар нет на этот день (по расписанию).")
        except Exception as e:
            self.list_day.addItem("Ошибка загрузки расписания: " + str(e))
        try:
            hlist = []
            for h in getattr(self, "homework_list", []):
                due = parse_date_safe(h.get("due_date"))
                if due and due.date() == pydate: hlist.append(h)
            if hlist:
                self.list_day.addItem("— Домашние задания —")
                for h in hlist:
                    title = h.get("title",""); due = parse_date_safe(h.get("due_date")); due_txt = due.strftime("%Y-%m-%d %H:%M") if due else (h.get("due_date") or "")
                    self.list_day.addItem(f"{title} (срок: {due_txt})")
        except Exception as e:
            self.list_day.addItem("Ошибка загрузки ДЗ: " + str(e))


    def start_polling(self):
        interval = max(5, int(self.settings.get("poll_interval_sec", DEFAULT_SETTINGS["poll_interval_sec"])))
        self.poll_timer.start(interval * 1000)
        self._prev_snapshot["homework"] = self._snapshot.get("homework", "")
        self._prev_snapshot["schedule"] = self._snapshot.get("schedule", "")
        self._prev_snapshot["grades"] = self._snapshot.get("grades", "")
        self.poll_updates()

    def stop_polling(self):
        if self.poll_timer.isActive():
            self.poll_timer.stop()

    def _play_sound(self):
        if self.settings.get("notify_sound", True):
            try:
                QApplication.beep()
            except Exception:
                pass

    def poll_updates(self):
        if not self.student_id:
            return
        try:
            r_hw = api_get(f"/students/{self.student_id}/homework")
            r_s = api_get(f"/students/{self.student_id}/schedule")
            r_g = api_get(f"/students/{self.student_id}/grades")
            hw, s, g = None, None, None
            if r_hw.status_code == 200: hw = r_hw.json()
            if r_s.status_code == 200: s = r_s.json()
            if r_g.status_code == 200: g = r_g.json()
            hw_json = json.dumps(hw, sort_keys=True, ensure_ascii=False) if hw is not None else ""
            s_json = json.dumps(s, sort_keys=True, ensure_ascii=False) if s is not None else ""
            g_json = json.dumps(g, sort_keys=True, ensure_ascii=False) if g is not None else ""
            if not self._first_seed_done:
                self._snapshot["homework"] = hw_json; self._snapshot["schedule"] = s_json; self._snapshot["grades"] = g_json
                self._first_seed_done = True
                self.lbl_api_status.setText("API: Доступно")
                self.lbl_last_update.setText(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                return
            if hw_json and hw_json != self._snapshot.get("homework", ""):
                prev_hw = json.loads(self._snapshot.get("homework", "[]")) if self._snapshot.get("homework", "") else []
                now_hw = hw or []
                self._prev_snapshot["homework"] = self._snapshot.get("homework", "")
                self._snapshot["homework"] = hw_json
                self.homework_list = now_hw
                self.populate_homework_table(now_hw)
                self.highlight_calendar_dates()
                prev_map = {str(h.get("id")): h for h in prev_hw}
                now_map = {str(h.get("id")): h for h in now_hw}
                added = [now_map[k] for k in now_map.keys() - prev_map.keys()]
                removed = [prev_map[k] for k in prev_map.keys() - now_map.keys()]
                changed = []
                for k in (set(prev_map.keys()) & set(now_map.keys())):
                    if json.dumps(prev_map[k], sort_keys=True, ensure_ascii=False) != json.dumps(now_map[k], sort_keys=True, ensure_ascii=False):
                        changed.append(now_map[k])
                if self.settings.get("notify_homework", True):
                    for a in added:
                        title = "Новое ДЗ"
                        body = f"{a.get('title','(без названия)')}\nСрок: {a.get('due_date','—')}"
                        NotificationPopup(title, body, duration=self.settings.get("notification_duration_sec", 6))
                    for c in changed:
                        title = "Обновлено ДЗ"
                        body = f"{c.get('title','(без названия)')}\nСрок: {c.get('due_date','—')}"
                        NotificationPopup(title, body, duration=self.settings.get("notification_duration_sec", 6))
                    if removed:
                        NotificationPopup("Удалено ДЗ", f"Удалено {len(removed)} заданий", duration=self.settings.get("notification_duration_sec", 6))
                    if (added or changed or removed):
                        self._play_sound()
            if s_json and s_json != self._snapshot.get("schedule", ""):
                prev_s = json.loads(self._snapshot.get("schedule", "[]")) if self._snapshot.get("schedule", "") else []
                now_s = s or []
                self._prev_snapshot["schedule"] = self._snapshot.get("schedule", "")
                self._snapshot["schedule"] = s_json
                self.schedule_list = now_s
                if self.nav.currentItem() and self.nav.currentItem().text() == "Расписание":
                    self.load_schedule()
                if self.settings.get("notify_schedule", True):
                    prev_map = {str(x.get("id")): x for x in prev_s}
                    now_map = {str(x.get("id")): x for x in now_s}
                    added = [now_map[k] for k in now_map.keys() - prev_map.keys()]
                    removed = [prev_map[k] for k in prev_map.keys() - now_map.keys()]
                    for a in added:
                        NotificationPopup("Новая пара", f"{a.get('subject','')} — {a.get('time','')}\n{a.get('week_day','')}", duration=self.settings.get("notification_duration_sec", 6))
                    if removed:
                        NotificationPopup("Пары удалены", f"Удалено {len(removed)} пар.", duration=self.settings.get("notification_duration_sec", 6))
                    if (added or removed):
                        self._play_sound()

            if g_json and g_json != self._snapshot.get("grades", ""):
                prev_g = json.loads(self._snapshot.get("grades", "[]")) if self._snapshot.get("grades", "") else []
                now_g = g or []
                self._prev_snapshot["grades"] = self._snapshot.get("grades", "")
                self._snapshot["grades"] = g_json
                self.grades_list = now_g
                if self.nav.currentItem() and self.nav.currentItem().text() == "Оценки":
                    self.load_grades()
                if self.settings.get("notify_grades", True):
                    prev_map = {str(x.get("id")): x for x in prev_g}
                    now_map = {str(x.get("id")): x for x in now_g}
                    added = [now_map[k] for k in now_map.keys() - prev_map.keys()]
                    changed = []
                    for k in (set(prev_map.keys()) & set(now_map.keys())):
                        if json.dumps(prev_map[k], sort_keys=True, ensure_ascii=False) != json.dumps(now_map[k], sort_keys=True, ensure_ascii=False):
                            changed.append(now_map[k])
                    for a in added:
                        NotificationPopup("Новая оценка", f"{a.get('subject','')} — {a.get('grade','')}", duration=self.settings.get("notification_duration_sec", 6))
                    for c in changed:
                        NotificationPopup("Обновлена оценка", f"{c.get('subject','')} — {c.get('grade','')}", duration=self.settings.get("notification_duration_sec", 6))
                    if (added or changed):
                        self._play_sound()
            self.update_overview()
            self.lbl_last_update.setText(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            self.lbl_api_status.setText("API: Доступно")
        except Exception as e:
            self.lbl_api_status.setText("API: Недоступно")
            print("Polling error:", e)


    def check_reminders(self):
        if not getattr(self, "homework_list", None): return
        now = datetime.now(); window = now + timedelta(hours=24)
        for h in self.homework_list:
            due = parse_date_safe(h.get("due_date"))
            if not due: continue
            if now <= due <= window:
                NotificationPopup("Напоминание: ДЗ скоро", f"{h.get('title','(без названия)')}\nСрок: {due.strftime('%Y-%m-%d %H:%M')}", duration=self.settings.get("notification_duration_sec", 6))
                self._play_sound()


    def count_homework_states(self):
        now = datetime.now(); overdue = 0; due_24 = 0; future = 0; soonest = None; soonest_hw = None
        for h in getattr(self, "homework_list", []):
            due = parse_date_safe(h.get("due_date"))
            if not due:
                future += 1; continue
            if due < now: overdue += 1
            elif due <= now + timedelta(hours=24): due_24 += 1
            else: future += 1
            if due and (soonest is None or due < soonest) and due >= now:
                soonest = due; soonest_hw = h
        return {'total': len(getattr(self, "homework_list", [])), 'overdue': overdue, 'due_24': due_24, 'future': future, 'next': soonest_hw, 'next_dt': soonest}

    def count_weekly_classes(self):
        today = date.today(); count = 0
        for d in range(7):
            dt = today + timedelta(days=d); wd = dt.strftime('%A')
            for it in getattr(self, 'schedule_list', []):
                if it.get('week_day') == wd: count += 1
        return count

    def recent_grades(self, n=3):
        try:
            r = api_get(f"/students/{self.student_id}/grades")
            if r.status_code != 200: return []
            arr = r.json()
            try:
                arr_sorted = sorted(arr, key=lambda x: x.get('created_at',''), reverse=True)
            except Exception:
                arr_sorted = arr
            return arr_sorted[:n]
        except Exception:
            return []

    def update_overview(self):
        if not self.student_id:
            self.overview_text.setText("Пожалуйста, войдите в систему."); self.overview_details.setPlainText(""); self.lbl_api_status.setText("API: —"); return
        try:
            r = api_get(f"/students/{self.student_id}/schedule", timeout=5); api_ok = (r.status_code == 200)
        except Exception:
            api_ok = False
        hw_stats = self.count_homework_states(); classes_week = self.count_weekly_classes(); recent = self.recent_grades(3); avatar = avatar_path(self.student_id) or "(нет)"
        overview_html = f"Привет, <b>{self.full_name}</b>!<br/>API: <b>{'Доступно' if api_ok else 'Недоступно'}</b><br/>ID: <b>{self.student_id}</b><br/>Направление: <b>{self.program or '—'}</b> | Курс: <b>{self.year or '—'}</b>"
        self.overview_text.setText(overview_html)
        details = []; details.append(f"Всего ДЗ: {hw_stats['total']} (Просрочено: {hw_stats['overdue']}, До 24ч: {hw_stats['due_24']}, Позже: {hw_stats['future']})")
        if hw_stats['next']:
            ndt = hw_stats['next_dt'].strftime('%Y-%m-%d %H:%M') if hw_stats['next_dt'] else hw_stats['next'].get('due_date','')
            details.append(f"Ближайшее ДЗ: {hw_stats['next'].get('title','(без названия)')} — {ndt}")
        details.append(f"Пар в ближайшие 7 дней (по расписанию): {classes_week}")
        if recent:
            details.append("Последние оценки:")
            for g in recent: details.append(f"  {g.get('subject','')} — {g.get('grade','')} ({g.get('comment','')})")
        details.append(f"Аватар: {avatar}"); details.append(f"API URL: {API}")
        self.overview_details.setPlainText("\n".join(details))


    def save_settings_from_ui(self):
        self.settings["poll_interval_sec"] = int(self.spin_interval.value())
        self.settings["notify_homework"] = bool(self.chk_notify_hw.isChecked())
        self.settings["notify_schedule"] = bool(self.chk_notify_sched.isChecked())
        self.settings["notify_grades"] = bool(self.chk_notify_gr.isChecked())
        self.settings["notify_sound"] = bool(self.chk_notify_sound.isChecked())
        self.settings["enable_tray"] = bool(self.chk_enable_tray.isChecked())
        save_settings(self.settings)
        QMessageBox.information(self, "Настройки", "Настройки сохранены.")
        if self.poll_timer.isActive():
            self.stop_polling(); self.start_polling()
        if self.settings.get("enable_tray", True) and not self.tray:
            self._init_tray()
        elif not self.settings.get("enable_tray", True) and self.tray:
            try:
                self.tray.hide(); self.tray.deleteLater(); self.tray = None
            except Exception:
                pass

    def reset_settings(self):
        self.settings = DEFAULT_SETTINGS.copy()
        self.spin_interval.setValue(self.settings["poll_interval_sec"])
        self.chk_notify_hw.setChecked(self.settings["notify_homework"])
        self.chk_notify_sched.setChecked(self.settings["notify_schedule"])
        self.chk_notify_gr.setChecked(self.settings["notify_grades"])
        self.chk_notify_sound.setChecked(self.settings["notify_sound"])
        self.chk_enable_tray.setChecked(self.settings["enable_tray"])
        save_settings(self.settings)
        QMessageBox.information(self, "Настройки", "Настройки восстановлены по умолчанию.")
        if self.poll_timer.isActive():
            self.stop_polling(); self.start_polling()


def main():
    app = QApplication(sys.argv)
    if os.path.exists("app_icon.png"):
        app.setWindowIcon(QIcon("app_icon.png"))
    w = MainWindow(); w.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
