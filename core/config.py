"""
Конфигурация системы
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DB_DIR = BASE_DIR / "db"
DB_DIR.mkdir(exist_ok=True)  # Создаем папку, если её нет
DB_PATH = DB_DIR / "crm.db"


class Config:
    """Настройки приложения"""
    APP_NAME = "БитрАдапт"
    VERSION = "1.0.0"
    DB_PATH = str(DB_PATH)
    ENABLE_LOGGING = True

    # Настройки UI
    UI_THEME = "dark-blue"
    UI_SCALING = 1.0
    UI_FONT = ("Arial", 12)