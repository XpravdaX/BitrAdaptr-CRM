"""
Базовый класс для модулей
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any
import customtkinter as ctk
from core.database import db_manager
from core.models import BaseModel


class BaseModule(ABC):
    """Абстрактный базовый класс для всех модулей"""

    MODULE_NAME = "Базовый модуль"
    MODULE_VERSION = "1.0"

    def __init__(self):
        self.model_class = None
        self.custom_fields = []

    @abstractmethod
    def get_ui_component(self, parent) -> ctk.CTkFrame:
        """Возвращает UI компонент модуля"""
        pass

    @abstractmethod
    def initialize_database(self):
        """Инициализирует таблицы БД для модуля"""
        pass

    def add_custom_field(self, field):
        """Добавляет пользовательское поле"""
        self.custom_fields.append(field)

    def get_fields_schema(self) -> Dict[str, str]:
        """Возвращает схему полей для таблицы БД"""
        base_schema = {
            'id': 'INTEGER PRIMARY KEY AUTOINCREMENT',
            'created_at': 'TEXT',
            'updated_at': 'TEXT'
        }
        return base_schema