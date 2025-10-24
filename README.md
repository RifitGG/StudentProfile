# Student Dashboard System

**Система управления учебной деятельностью студентов** — комплексное решение для автоматизации процессов учёта расписания, домашних заданий и оценок в образовательных учреждениях.
Авторы: Зайцев Ярослав, Иванов Егор, Петренко Кирилл

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![Flask](https://img.shields.io/badge/flask-3.0+-green.svg)
![PySide6](https://img.shields.io/badge/PySide6-6.0+-orange.svg)
![MySQL](https://img.shields.io/badge/mysql-8.0+-blue.svg)

---

## Содержание

- [Обзор](#обзор)
- [Возможности](#возможности)
- [Архитектура](#архитектура)
- [Требования](#требования)
- [Установка](#установка)
- [Конфигурация](#конфигурация)
- [Использование](#использование)
- [API Endpoints](#api-endpoints)

---

## Обзор

Student Dashboard System представляет собой трёхкомпонентное приложение:

1. **REST API сервер** (Flask) — централизованный бэкенд для управления данными
2. **Десктопный клиент** (PySide6/Qt6) — современный графический интерфейс с системой уведомлений
3. **Консольный менеджер** — CLI-инструмент для администрирования и экспорта данных

Система предназначена для студентов, преподавателей и администраторов образовательных учреждений, обеспечивая централизованный доступ к информации об учебном процессе.

---

## Возможности

### Десктопный клиент

- **Аутентификация и регистрация** — защищённый вход с хешированием паролей (Werkzeug)
- **Интерактивный календарь** — визуализация дедлайнов и расписания с цветовым кодированием
- **Управление домашними заданиями**:
  - Просмотр активных и завершённых заданий
  - Загрузка и скачивание прикреплённых файлов
  - Фильтрация по заголовку и описанию
  - Индикация просроченных заданий
- **Расписание занятий** — просмотр пар по дням недели с информацией об аудиториях и преподавателях
- **Журнал оценок** — отслеживание академических показателей
- **Система уведомлений**:
  - Push-уведомления о новых заданиях, изменениях в расписании и оценках
  - Автоматический опрос сервера с настраиваемым интервалом
  - Звуковые оповещения
- **Персонализация**:
  - Загрузка пользовательских аватаров
  - Настройка параметров уведомлений
  - Интеграция с системным треем

### REST API сервер

- **RESTful архитектура** — стандартизированные HTTP-методы и JSON-формат
- **Endpoint'ы для**:
  - Регистрации и авторизации пользователей
  - CRUD операций над расписанием, домашними заданиями и оценками
  - Загрузки и скачивания файлов
- **Защита данных** — хеширование паролей с использованием `werkzeug.security`
- **CORS-ready** — готовность к работе с фронтенд-приложениями

### Консольный менеджер

- **Интерактивная CLI** — REPL-интерфейс для администрирования
- **Управление данными**:
  - Добавление студентов, заданий, расписания и оценок
  - Просмотр записей с форматированным выводом
- **Экспорт данных** — выгрузка в CSV и JSON форматы для анализа и интеграции

---

## Архитектура

```
┌─────────────────────────────────────────────────────────┐
│                   Desktop Client (PySide6)              │
│  ┌──────────┐  ┌──────────┐  ┌───────────┐            │
│  │  Login   │  │ Calendar │  │ Homework  │            │
│  │ Widget   │  │  Widget  │  │  Manager  │            │
│  └──────────┘  └──────────┘  └───────────┘            │
│         │              │              │                 │
│         └──────────────┴──────────────┘                │
│                        │                                │
│                   HTTP/JSON                             │
│                        │                                │
└────────────────────────┼────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│              REST API Server (Flask)                    │
│  ┌─────────────────────────────────────────────┐       │
│  │  Routes: /register, /login, /students/*     │       │
│  │         /homework/*, /admin/*                │       │
│  └─────────────────────────────────────────────┘       │
│                        │                                │
│                   SQLAlchemy ORM                        │
│                        │                                │
└────────────────────────┼────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│                  MySQL Database                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐             │
│  │ students │  │ schedule │  │ homeworks│             │
│  └──────────┘  └──────────┘  └──────────┘             │
│  ┌──────────┐                                          │
│  │  grades  │                                          │
│  └──────────┘                                          │
└─────────────────────────────────────────────────────────┘
```

**Технологический стек:**

- **Backend**: Python 3.8+, Flask 3.0+, SQLAlchemy 2.0+
- **Frontend**: PySide6 (Qt6), QtWidgets, QtGui
- **Database**: MySQL 8.0+ (или MariaDB 10.5+)
- **ORM**: SQLAlchemy с драйвером PyMySQL
- **Security**: Werkzeug password hashing (PBKDF2 SHA-256)

---

## Требования

### Системные требования

- **ОС**: Windows 10/11, Linux (Ubuntu 20.04+), macOS 10.15+
- **Python**: 3.8 или выше
- **MySQL**: 8.0 или выше (либо MariaDB 10.5+)
- **RAM**: минимум 2 ГБ
- **Дисковое пространство**: 500 МБ

### Python-зависимости

```txt
Flask>=3.0.0
SQLAlchemy>=2.0.0
PyMySQL>=1.1.0
requests>=2.31.0
PySide6>=6.6.0
Werkzeug>=3.0.0
```

---

## Установка

### 1. Клонирование репозитория

```bash
git clone https://github.com/yourusername/student-dashboard.git
cd student-dashboard
```

### 2. Создание виртуального окружения

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/macOS
python3 -m venv venv
source venv/bin/activate
```

### 3. Установка зависимостей

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Настройка базы данных

#### Создание БД в MySQL

```sql
CREATE DATABASE student_dashboard CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'student_user'@'localhost' IDENTIFIED BY 'secure_password';
GRANT ALL PRIVILEGES ON student_dashboard.* TO 'student_user'@'localhost';
FLUSH PRIVILEGES;
```

#### Инициализация таблиц и тестовых данных

```bash
python db_init.py
```

Скрипт создаст:
- Таблицы: `students`, `schedule`, `homeworks`, `grades`
- Тестовые данные (2 студента, расписание, задания, оценки)

**Тестовые учётные данные:**
- Иванов Иван Иванович / `password1`
- Петрова Мария Сергеевна / `password2`

---

## Конфигурация

### Файл `config.py`

```python
# Настройки подключения к MySQL
MYSQL_USER = "student_user"
MYSQL_PASSWORD = "secure_password"
MYSQL_HOST = "127.0.0.1"
MYSQL_PORT = 3306
MYSQL_DB = "student_dashboard"

# Альтернативно: использовать DATABASE_URL
DATABASE_URL = ""  # Например: "mysql+pymysql://user:pass@host/db"

# URL API-сервера для клиента
API_URL = "http://127.0.0.1:5000"

# Директория для загруженных файлов
UPLOAD_DIR = "uploads"

# Директория для аватаров (клиент)
AVATAR_DIR = "avatars"
```

### Переменные окружения (опционально)

```bash
export MYSQL_USER="student_user"
export MYSQL_PASSWORD="secure_password"
export MYSQL_HOST="127.0.0.1"
export MYSQL_DB="student_dashboard"
```

---

## Использование

### Запуск API-сервера

```bash
python server_api.py
```

Сервер запустится на `http://127.0.0.1:5000`

**Параметры запуска:**
- `debug=True` — режим отладки с hot-reload
- `host='0.0.0.0'` — доступ из сети (по умолчанию только localhost)
- `port=5000` — порт сервера

### Запуск десктопного клиента

```bash
python client.py
```

**Основные функции:**
1. Войдите с тестовыми учётными данными или зарегистрируйте нового студента
2. Навигация по разделам: Обзор, Календарь, Расписание, Домашние задания, Оценки
3. Настройте интервал опроса и уведомления в разделе «Настройки»
4. Загрузите аватар через кнопку «Загрузить аватар»

### Запуск консольного менеджера

```bash
python server_console.py
```

**Доступные команды:**

```
help                    — показать список команд
list_students           — список всех студентов
list_homeworks          — список домашних заданий
list_schedule           — расписание
add_student             — добавить студента (интерактивно)
add_homework            — добавить задание
add_schedule            — добавить пару в расписание
add_grade               — поставить оценку
export <table> <file>   — экспорт таблицы (students|homeworks|grades|schedule) в CSV/JSON
exit                    — выход
```

**Примеры экспорта:**

```bash
> export students students.csv
> export homeworks homeworks.json
> export grades grades_2024.csv
```

---

## API Endpoints

### Аутентификация

| Метод | Endpoint | Описание | Тело запроса |
|-------|----------|----------|--------------|
| POST | `/register` | Регистрация нового студента | `{full_name, program, year, password}` |
| POST | `/login` | Авторизация | `{full_name, password}` |

**Пример регистрации:**

```bash
curl -X POST http://localhost:5000/register \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "Сидоров Петр Александрович",
    "program": "ИСиП",
    "year": 1,
    "password": "mypassword"
  }'
```

**Ответ:**

```json
{
  "id": 3,
  "full_name": "Сидоров Петр Александрович"
}
```

### Расписание

| Метод | Endpoint | Описание | Параметры |
|-------|----------|----------|-----------|
| GET | `/students/<id>/schedule` | Получить расписание студента | `?day=Monday` (опционально) |

**Пример:**

```bash
curl http://localhost:5000/students/1/schedule?day=Monday
```

**Ответ:**

```json
[
  {
    "week_day": "Monday",
    "time": "09:00-10:30",
    "subject": "Программирование",
    "classroom": "A101",
    "teacher": "И. Сидоров"
  }
]
```

### Домашние задания

| Метод | Endpoint | Описание | Тело/Параметры |
|-------|----------|----------|----------------|
| GET | `/students/<id>/homework` | Получить все задания студента | — |
| POST | `/students/<id>/homework` | Создать задание | JSON: `{title, description, due_date}` или Multipart с файлом |
| GET | `/homework/<id>/download` | Скачать прикреплённый файл | — |

**Пример создания задания с файлом (Multipart):**

```bash
curl -X POST http://localhost:5000/students/1/homework \
  -F "title=Лабораторная 2" \
  -F "description=Реализовать сортировку" \
  -F "due_date=2025-11-01" \
  -F "file=@lab2.pdf"
```

**Ответ:**

```json
{
  "id": 5,
  "title": "Лабораторная 2",
  "attachment": "20251024143022_lab2.pdf"
}
```

### Оценки

| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | `/students/<id>/grades` | Получить оценки студента |

**Пример:**

```bash
curl http://localhost:5000/students/1/grades
```

**Ответ:**

```json
[
  {
    "id": 1,
    "subject": "Программирование",
    "grade": "A",
    "comment": "Отлично"
  }
]
```

### Административные функции

| Метод | Endpoint | Описание | Тело запроса |
|-------|----------|----------|--------------|
| POST | `/admin/push_homework` | Создать задание для всего направления | `{program, title, description, due_date}` |

**Пример:**

```bash
curl -X POST http://localhost:5000/admin/push_homework \
  -H "Content-Type: application/json" \
  -d '{
    "program": "ИСиП",
    "title": "Курсовая работа",
    "description": "Разработка веб-приложения",
    "due_date": "2025-12-20"
  }'
```


### Модели SQLAlchemy

#### Student

```python
class Student(Base):
    __tablename__ = 'students'
    id = Column(Integer, primary_key=True)
    full_name = Column(String(255), nullable=False)
    program = Column(String(128), nullable=False)  # Направление обучения
    year = Column(Integer, nullable=False)         # Курс
    password_hash = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
```

#### ScheduleItem

```python
class ScheduleItem(Base):
    __tablename__ = 'schedule'
    id = Column(Integer, primary_key=True)
    program = Column(String(128), nullable=False)
    week_day = Column(String(32), nullable=False)  # Monday, Tuesday, ...
    time = Column(String(64), nullable=False)      # HH:MM-HH:MM
    subject = Column(String(255), nullable=False)
    classroom = Column(String(64), nullable=True)
    teacher = Column(String(128), nullable=True)
```

#### Homework

```python
class Homework(Base):
    __tablename__ = 'homeworks'
    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey('students.id'), nullable=True)
    program = Column(String(128), nullable=True)  # Для групповых заданий
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    due_date = Column(String(64), nullable=True)  # ISO format or custom
    created_at = Column(DateTime, default=datetime.utcnow)
    pushed = Column(Integer, default=0)           # Флаг отправленного задания
    attachment = Column(String(512), nullable=True)  # Имя файла
```

#### Grade

```python
class Grade(Base):
    __tablename__ = 'grades'
    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey('students.id'), nullable=False)
    subject = Column(String(255), nullable=False)
    grade = Column(String(32), nullable=False)     # A, B+, 5, и т.д.
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
```

---

## 🛠️ Разработка

### Структура проекта

```
student-dashboard/
├── server_api.py          # Flask REST API сервер
├── server_console.py      # CLI менеджер (REPL)
├── client.py              # PySide6 десктопный клиент
├── db_models.py           # SQLAlchemy модели
├── db_init.py             # Скрипт инициализации БД
├── config.py              # Конфигурация приложения
├── requirements.txt       # Python-зависимости
├── README.md              # Документация
├── uploads/               # Загруженные файлы (создаётся автоматически)
├── avatars/               # Аватары пользователей (создаётся автоматически)
└── .venv/                 # Виртуальное окружение (не коммитится)
```

### Добавление новых endpoint'ов

**Пример в `server_api.py`:**

```python
@app.route('/students/<int:student_id>/profile', methods=['GET'])
def get_profile(student_id):
    sess = get_session(engine)
    student = sess.get(Student, student_id)
    if not student:
        return jsonify({'error': 'Student not found'}), 404
    return jsonify({
        'id': student.id,
        'full_name': student.full_name,
        'program': student.program,
        'year': student.year
    })
```

### Логирование

**Включение подробных логов SQLAlchemy:**

```python
# В db_models.py
engine = create_engine(db_url, echo=True)  # echo=True для SQL-логов
```

**Настройка логирования Flask:**

```python
# В server_api.py
import logging
logging.basicConfig(level=logging.DEBUG)
app.logger.setLevel(logging.DEBUG)
```

---

##  Безопасность

### Реализованные меры защиты

1. **Хеширование паролей**:
   - Используется `werkzeug.security.generate_password_hash()` (PBKDF2 SHA-256)
   - Пароли не хранятся в открытом виде

2. **SQL Injection Protection**:
   - SQLAlchemy ORM использует параметризованные запросы
   - Все пользовательские данные фильтруются

3. **Безопасная загрузка файлов**:
   - `werkzeug.utils.secure_filename()` для санитизации имён файлов
   - Таймстамп-префикс для предотвращения коллизий

4. **HTTPS-ready**:
   - Для продакшена рекомендуется использовать Nginx/Apache с SSL/TLS

### Рекомендации для продакшена

```bash
# Используйте WSGI-сервер (например, Gunicorn)
gunicorn -w 4 -b 0.0.0.0:5000 server_api:app

# Настройте файрвол
sudo ufw allow 5000/tcp

# Регулярное резервное копирование БД
mysqldump -u student_user -p student_dashboard > backup_$(date +%Y%m%d).sql
```

### Переменные окружения для продакшена

```bash
# .env файл (не коммитится)
MYSQL_PASSWORD=strong_random_password_here
SECRET_KEY=your_secret_key_for_sessions
FLASK_ENV=production
```

---

##  Устранение неполадок

### Проблема: "Access denied for user"

**Решение:**

```sql
-- Проверьте права пользователя
SHOW GRANTS FOR 'student_user'@'localhost';

-- Пересоздайте пользователя
DROP USER 'student_user'@'localhost';
CREATE USER 'student_user'@'localhost' IDENTIFIED BY 'new_password';
GRANT ALL PRIVILEGES ON student_dashboard.* TO 'student_user'@'localhost';
```

### Проблема: "Connection refused" на клиенте

**Решение:**

1. Убедитесь, что API-сервер запущен: `curl http://127.0.0.1:5000`
2. Проверьте `API_URL` в `config.py`
3. Проверьте файрвол: `sudo ufw status`

### Проблема: "Module not found"

**Решение:**

```bash
# Переустановите зависимости
pip install --upgrade --force-reinstall -r requirements.txt

# Или установите конкретный модуль
pip install PySide6
```

---

### Оптимизация

```python
# Использование connection pooling
engine = create_engine(
    db_url,
    pool_size=20,           # Размер пула соединений
    max_overflow=40,        # Дополнительные соединения
    pool_pre_ping=True      # Проверка соединений перед использованием
)
```





