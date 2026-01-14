"""
Модуль управления плагинами
"""
import customtkinter as ctk
from tkinter import messagebox
from typing import Dict, Any, List
from pathlib import Path
import os

from modules.base_module import BaseModule
from ui.styles import Styles
from core.config import Config
from plugins import plugin_manager


class PluginsModule(BaseModule):
    """Модуль управления плагинами"""

    MODULE_NAME = "Плагины"
    MODULE_VERSION = "1.0"

    def __init__(self):
        super().__init__()
        plugin_manager.discover_plugins()

    def get_ui_component(self, parent) -> ctk.CTkFrame:
        """Создает интерфейс для управления плагинами"""
        frame = ctk.CTkFrame(parent)
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Заголовок
        title = ctk.CTkLabel(
            frame,
            text="Управление плагинами",
            font=("Arial", 24, "bold"),
            text_color=Styles.PRIMARY_COLOR
        )
        title.pack(pady=(0, 20))

        # Scrollable area
        scrollable_frame = ctk.CTkScrollableFrame(frame)
        scrollable_frame.pack(fill="both", expand=True)

        # Обновить список плагинов
        refresh_btn = ctk.CTkButton(
            scrollable_frame,
            text="🔄 Обновить список плагинов",
            command=self._refresh_plugins,
            width=250,
            height=40,
            fg_color=Styles.SECONDARY_COLOR,
            hover_color="#8A2C5C"
        )
        refresh_btn.pack(pady=(0, 20))

        # Список плагинов
        ctk.CTkLabel(scrollable_frame, text="Доступные плагины:", 
                     font=("Arial", 16, "bold")).pack(anchor="w", pady=(10, 5))
        
        self.plugins_container = ctk.CTkFrame(scrollable_frame)
        self.plugins_container.pack(fill="x", pady=10)

        self._load_plugins_list()

        # Информация
        info_frame = ctk.CTkFrame(scrollable_frame)
        info_frame.pack(fill="x", pady=20)
        
        info_text = """
        📌 Информация о плагинах:
        
        • Плагины добавляют новые возможности в CRM
        • Для активации плагина нажмите "Включить"
        • После включения плагин появится в боковой панели
        • Для деактивации нажмите "Выключить"
        • Перезапустите приложение для полного применения изменений
        """
        
        info_label = ctk.CTkLabel(
            info_frame,
            text=info_text,
            justify="left",
            font=("Arial", 11)
        )
        info_label.pack(padx=10, pady=10)

        return frame

    def _load_plugins_list(self):
        """Загружает список плагинов"""
        # Очищаем контейнер
        for widget in self.plugins_container.winfo_children():
            widget.destroy()

        if not plugin_manager.plugins:
            no_plugins_label = ctk.CTkLabel(
                self.plugins_container,
                text="📭 Плагины не найдены\nСоздайте папку в директории plugins/",
                font=("Arial", 14),
                text_color="gray"
            )
            no_plugins_label.pack(pady=20)
            return

        for i, (plugin_id, plugin_info) in enumerate(plugin_manager.plugins.items()):
            self._create_plugin_card(plugin_id, plugin_info, i)

    def _create_plugin_card(self, plugin_id: str, plugin_info: Dict[str, Any], index: int):
        """Создает карточку плагина"""
        card = ctk.CTkFrame(self.plugins_container)
        card.pack(fill="x", pady=5, padx=5)
        
        # Верхняя часть карточки
        top_frame = ctk.CTkFrame(card)
        top_frame.pack(fill="x", padx=10, pady=10)
        
        # Иконка и название
        icon_label = ctk.CTkLabel(
            top_frame,
            text=plugin_info.get('icon', '🔌'),
            font=("Arial", 20)
        )
        icon_label.pack(side="left", padx=(0, 10))
        
        name_frame = ctk.CTkFrame(top_frame)
        name_frame.pack(side="left", fill="x", expand=True)
        
        name_label = ctk.CTkLabel(
            name_frame,
            text=plugin_info.get('name', plugin_id),
            font=("Arial", 16, "bold")
        )
        name_label.pack(anchor="w")
        
        version_label = ctk.CTkLabel(
            name_frame,
            text=f"Версия: {plugin_info.get('version', '1.0')}",
            font=("Arial", 11),
            text_color="gray"
        )
        version_label.pack(anchor="w")
        
        # Статус плагина
        status_frame = ctk.CTkFrame(top_frame)
        status_frame.pack(side="right")
        
        is_enabled = plugin_manager.is_plugin_enabled(plugin_id)
        status_text = "✅ Включен" if is_enabled else "❌ Выключен"
        status_color = Styles.SUCCESS_COLOR if is_enabled else Styles.ERROR_COLOR
        
        status_label = ctk.CTkLabel(
            status_frame,
            text=status_text,
            font=("Arial", 12, "bold"),
            text_color=status_color
        )
        status_label.pack(pady=5)
        
        # Кнопки управления
        button_frame = ctk.CTkFrame(card)
        button_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        if is_enabled:
            disable_btn = ctk.CTkButton(
                button_frame,
                text="Выключить",
                command=lambda pid=plugin_id: self._disable_plugin(pid),
                width=100,
                height=35,
                fg_color=Styles.ERROR_COLOR,
                hover_color="#B71C1C"
            )
            disable_btn.pack(side="right", padx=5)
        else:
            enable_btn = ctk.CTkButton(
                button_frame,
                text="Включить",
                command=lambda pid=plugin_id: self._enable_plugin(pid),
                width=100,
                height=35,
                fg_color=Styles.SUCCESS_COLOR,
                hover_color="#388E3C"
            )
            enable_btn.pack(side="right", padx=5)
        
        # Описание
        if plugin_info.get('description'):
            desc_label = ctk.CTkLabel(
                card,
                text=plugin_info['description'],
                justify="left",
                wraplength=800,
                font=("Arial", 12)
            )
            desc_label.pack(anchor="w", padx=10, pady=(0, 10))
        
        # Автор
        if plugin_info.get('author'):
            author_label = ctk.CTkLabel(
                card,
                text=f"Автор: {plugin_info['author']}",
                justify="left",
                font=("Arial", 10),
                text_color="gray"
            )
            author_label.pack(anchor="w", padx=10, pady=(0, 10))
        
        # Разделитель
        if index < len(plugin_manager.plugins) - 1:
            separator = ctk.CTkFrame(card, height=1, fg_color="#555555")
            separator.pack(fill="x", padx=10, pady=(0, 5))

    def _refresh_plugins(self):
        """Обновляет список плагинов"""
        plugin_manager.discover_plugins()
        self._load_plugins_list()
        messagebox.showinfo("Обновлено", "Список плагинов обновлен!")

    def _enable_plugin(self, plugin_id: str):
        """Включает плагин"""
        if plugin_manager.enable_plugin(plugin_id):
            self._load_plugins_list()
            messagebox.showinfo("Успех", 
                f"Плагин '{plugin_manager.get_plugin_info(plugin_id)['name']}' включен!\n"
                f"Перезапустите приложение для отображения в боковой панели.")
        else:
            messagebox.showerror("Ошибка", "Не удалось включить плагин")

    def _disable_plugin(self, plugin_id: str):
        """Выключает плагин"""
        plugin_info = plugin_manager.get_plugin_info(plugin_id)
        confirm = messagebox.askyesno(
            "Выключение плагина",
            f"Вы уверены, что хотите выключить плагин '{plugin_info['name']}'?"
        )
        
        if confirm:
            if plugin_manager.disable_plugin(plugin_id):
                self._load_plugins_list()
                messagebox.showinfo("Успех", 
                    f"Плагин '{plugin_info['name']}' выключен!\n"
                    f"Перезапустите приложение для полного отключения.")
            else:
                messagebox.showerror("Ошибка", "Не удалось выключить плагин")

    def initialize_database(self):
        """Инициализирует таблицы БД для модуля"""
        pass