"""
Базовый класс для плагинов
"""
from abc import ABC, abstractmethod
import customtkinter as ctk


class BasePlugin(ABC):
    """Абстрактный базовый класс для плагинов"""
    
    def __init__(self):
        self.plugin_info = {}
    
    @abstractmethod
    def get_ui_component(self, parent) -> ctk.CTkFrame:
        """Возвращает UI компонент плагина"""
        pass
    
    @abstractmethod
    def initialize_database(self):
        """Инициализирует таблицы БД для плагина"""
        pass
    
    def get_module_name(self) -> str:
        """Возвращает имя модуля для отображения в сайдбаре"""
        return self.plugin_info.get('name', 'Плагин')
    
    def get_sidebar_icon(self) -> str:
        """Возвращает иконку для сайдбара"""
        return self.plugin_info.get('icon', '🔌')