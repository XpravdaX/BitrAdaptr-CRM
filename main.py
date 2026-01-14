"""
Главный файл приложения CRM
"""
import sys
import os
import logging
from tkinter import messagebox
from pathlib import Path

# Добавляем корневую директорию в путь
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import customtkinter as ctk
from PIL import Image

from core.config import Config
from core.database import db_manager
from ui.styles import Styles
from modules.clients import ClientsModule
from modules.reports import ReportsModule
from modules.settings import SettingsModule
from modules.plugins import PluginsModule
from utils.dependencies import setup_client_dependencies  # Импортируем зависимости


class PluginModuleWrapper:
    """Обертка для плагинов, чтобы они работали как модули"""

    def __init__(self, plugin):
        self.plugin = plugin
        self.MODULE_NAME = plugin.get_module_name()
        # Назначаем пустую функцию для совместимости
        self.initialize_database = lambda: None

    def get_ui_component(self, parent):
        """Возвращает UI компонент плагина"""
        return self.plugin.get_ui_component(parent)


class FlexCRMApp:
    """Главное приложение CRM"""

    def __init__(self):
        self.root = ctk.CTk()
        self.setup_window()
        self.setup_logging()
        self.setup_database()

        # Настраиваем зависимости перед инициализацией модулей
        self.setup_dependencies()

        self.modules = []
        self.plugin_modules = []
        self.current_module = None

        # Загружаем плагины
        self.load_plugins()

        # Инициализация модулей
        self.init_modules()

    def setup_window(self):
        """Настраивает главное окно"""
        self.root.title(f"{Config.APP_NAME} v{Config.VERSION}")
        self.root.geometry("1200x700")
        self.root.minsize(800, 600)

        # Устанавливаем тему
        Styles.setup_theme()

    def setup_logging(self):
        """Настраивает логирование"""
        logging.basicConfig(
            level=logging.INFO if Config.ENABLE_LOGGING else logging.WARNING,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def setup_database(self):
        """Настраивает базу данных"""
        try:
            db_manager.connect()
            self.logger.info("Database initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize database: {e}")
            messagebox.showerror("Ошибка", f"Ошибка инициализации БД: {e}")

    def setup_dependencies(self):
        """Настраивает зависимости между полями"""
        try:
            setup_client_dependencies()
            self.logger.info("Field dependencies initialized")
        except Exception as e:
            self.logger.warning(f"Failed to setup dependencies: {e}")

    def load_plugins(self):
        """Загружает включенные плагины"""
        try:
            from plugins import plugin_manager

            plugin_manager.discover_plugins()
            self.logger.info(f"Найдено плагинов: {len(plugin_manager.plugins)}")

            for plugin_id, plugin_info in plugin_manager.plugins.items():
                if plugin_manager.is_plugin_enabled(plugin_id):
                    # Пытаемся загрузить плагин, если еще не загружен
                    if plugin_id not in plugin_manager.loaded_plugins:
                        if not plugin_manager.enable_plugin(plugin_id):
                            self.logger.warning(f"Не удалось загрузить плагин: {plugin_id}")
                            continue

                    plugin_instance = plugin_manager.get_plugin_module(plugin_id)
                    if plugin_instance:
                        self.plugin_modules.append(plugin_instance)
                        self.logger.info(f"Загружен плагин: {plugin_id}")
        except Exception as e:
            self.logger.error(f"Ошибка загрузки плагинов: {e}")
            # Не показываем ошибку пользователю, если плагины не загрузились

    def init_modules(self):
        """Инициализирует все модули"""
        # Регистрируем стандартные модули
        self.modules.append(ClientsModule())
        self.modules.append(ReportsModule())

        # Добавляем плагины как модули
        for plugin in self.plugin_modules:
            plugin_wrapper = PluginModuleWrapper(plugin)
            self.modules.append(plugin_wrapper)

        # Модуль управления плагинами и настройки
        self.modules.append(PluginsModule())
        self.modules.append(SettingsModule())

        self.logger.info(f"Загружено {len(self.modules)} модулей")

    def create_sidebar(self):
        """Создает боковую панель"""
        sidebar = ctk.CTkFrame(self.root, width=200, corner_radius=0)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        # Заголовок
        header = Styles.create_header_label(sidebar, Config.APP_NAME)
        header.pack(pady=20)

        # Кнопки основных модулей (кроме настроек и плагинов)
        for i, module in enumerate(self.modules):
            # Пропускаем специальные модули в основном списке
            if module.MODULE_NAME in ["Настройки", "Плагины"]:
                continue

            # Проверяем, является ли это плагином
            is_plugin = hasattr(module, 'plugin')

            # Определяем иконку и цвет
            if module.MODULE_NAME == "Клиенты":
                icon = "👥"
                bg_color = "#2D3748"
                hover_color = "#4A5568"
            elif module.MODULE_NAME == "Отчеты":
                icon = "📊"
                bg_color = "#2D3748"
                hover_color = "#4A5568"
            elif is_plugin:
                # Для плагинов используем иконку из плагина
                icon = module.plugin.get_sidebar_icon()
                bg_color = "#2A4D69"  # Синий для плагинов
                hover_color = "#3B6C8C"
            else:
                icon = "📦"
                bg_color = "#2D3748"
                hover_color = "#4A5568"

            btn = ctk.CTkButton(
                sidebar,
                text=f"{icon} {module.MODULE_NAME}",
                command=lambda m=module: self.switch_module(m),
                height=45,
                font=("Arial", 14),
                fg_color=bg_color,
                hover_color=hover_color,
                border_width=1,
                border_color="#4A5568",
                corner_radius=8,
                anchor="w"
            )
            btn.pack(fill="x", padx=10, pady=5)

        # Разделитель перед системными модулями
        separator = ctk.CTkFrame(sidebar, height=2, fg_color="#555555")
        separator.pack(fill="x", padx=20, pady=20)

        # Добавляем модуль "Плагины"
        plugins_module = next((m for m in self.modules if m.MODULE_NAME == "Плагины"), None)
        if plugins_module:
            plugins_btn = ctk.CTkButton(
                sidebar,
                text="🔌 Плагины",
                command=lambda m=plugins_module: self.switch_module(m),
                height=45,
                font=("Arial", 14),
                fg_color="#333333",
                hover_color="#444444",
                border_width=1,
                border_color="#555555",
                corner_radius=8,
                anchor="w"
            )
            plugins_btn.pack(fill="x", padx=10, pady=5)

        # Добавляем кнопку "Настройки"
        settings_module = next((m for m in self.modules if m.MODULE_NAME == "Настройки"), None)
        if settings_module:
            settings_btn = ctk.CTkButton(
                sidebar,
                text="⚙️ Настройки",
                command=lambda m=settings_module: self.switch_module(m),
                height=45,
                font=("Arial", 14),
                fg_color="#333333",
                hover_color="#444444",
                border_width=1,
                border_color="#555555",
                corner_radius=8,
                anchor="w"
            )
            settings_btn.pack(fill="x", padx=10, pady=5)

        # Разделитель
        separator = ctk.CTkFrame(sidebar, height=2, fg_color="#555555")
        separator.pack(fill="x", padx=20, pady=20)

        # Кнопка выхода
        exit_btn = ctk.CTkButton(
            sidebar,
            text="🚪 Выход",
            command=self.on_closing,
            height=45,
            font=("Arial", 14),
            fg_color=Styles.ERROR_COLOR,
            hover_color="#B71C1C",
            border_width=1,
            border_color="#D32F2F",
            corner_radius=8
        )
        exit_btn.pack(side="bottom", fill="x", padx=10, pady=10)

        return sidebar

    def create_main_area(self):
        """Создает основную область"""
        main_area = ctk.CTkFrame(self.root)
        main_area.pack(side="right", fill="both", expand=True)

        # Заголовок модуля
        self.module_title = ctk.CTkLabel(
            main_area,
            text="Добро пожаловать в БитрАдапт",
            font=("Arial", 20, "bold"),
            text_color=Styles.PRIMARY_COLOR
        )
        self.module_title.pack(pady=20)

        # Контейнер для модуля
        self.module_container = ctk.CTkFrame(main_area)
        self.module_container.pack(fill="both", expand=True, padx=20, pady=10)

        return main_area

    def switch_module(self, module):
        """Переключает активный модуль"""
        self.current_module = module

        # Обновляем заголовок
        self.module_title.configure(text=module.MODULE_NAME)

        # Очищаем контейнер
        for widget in self.module_container.winfo_children():
            widget.destroy()

        # Добавляем UI модуля
        module_ui = module.get_ui_component(self.module_container)
        module_ui.pack(fill="both", expand=True)

        self.logger.info(f"Switched to module: {module.MODULE_NAME}")

    def create_welcome_screen(self):
        """Создает экран приветствия"""
        welcome_frame = ctk.CTkFrame(self.module_container)
        welcome_frame.pack(fill="both", expand=True)

        # Текст приветствия с описанием новых функций
        welcome_text = """
        Добро пожаловать в БитрАдапт!

        Гибкая CRM система для управления вашим бизнесом.

        Новые возможности:
        • Управление клиентами с масками ввода
        • Зависимости между полями
        • Автоматическое форматирование телефонов
        • Примеры ввода для каждого поля
        • Генерация отчетов
        • Гибкая настройка полей
        • Модульная архитектура
        • Красивый интерфейс
        • Система плагинов

        Выберите модуль в боковой панели для начала работы.
        """

        text_label = ctk.CTkLabel(
            welcome_frame,
            text=welcome_text,
            font=("Arial", 16),
            justify="left"
        )
        text_label.pack(pady=50, padx=50)

    def on_closing(self):
        """Обрабатывает закрытие приложения"""
        try:
            db_manager.close()
            self.logger.info("Application closed")
        except:
            pass
        finally:
            self.root.quit()
            self.root.destroy()

    def run(self):
        """Запускает приложение"""
        try:
            # Создаем интерфейс
            self.create_sidebar()
            main_area = self.create_main_area()

            # Показываем экран приветствия
            self.create_welcome_screen()

            # Обработка закрытия окна
            self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

            # Запуск главного цикла
            self.root.mainloop()

        except Exception as e:
            self.logger.error(f"Application error: {e}")
            messagebox.showerror("Критическая ошибка", f"Произошла ошибка: {str(e)}")
            sys.exit(1)


def main():
    """Точка входа в приложение"""
    app = FlexCRMApp()
    app.run()


if __name__ == "__main__":
    main()