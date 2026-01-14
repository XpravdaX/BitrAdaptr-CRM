"""
Модуль настроек системы
"""
import customtkinter as ctk
from tkinter import messagebox
from typing import Dict, Any
import json
from pathlib import Path

from modules.base_module import BaseModule
from ui.styles import Styles
from core.config import Config


class SettingsModule(BaseModule):
    """Модуль настроек системы"""

    MODULE_NAME = "Настройки"
    MODULE_VERSION = "1.0"

    def __init__(self):
        super().__init__()
        self.settings_file = Path(__file__).parent.parent / "settings.json"
        self.settings = self.load_settings()

    def load_settings(self) -> Dict[str, Any]:
        """Загружает настройки из файла"""
        default_settings = {
            "appearance_mode": "dark",  # dark, light, system
            "ui_scaling": 1.0,
            "enable_notifications": True,
            "auto_save": True,
            "backup_interval": 24,  # часов
            "max_rows_per_page": 50,
            "default_status": "активный"  # Изменено на русский
        }

        if self.settings_file.exists():
            try:
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    loaded_settings = json.load(f)
                    default_settings.update(loaded_settings)
            except Exception as e:
                print(f"Ошибка загрузки настроек: {e}")

        return default_settings

    def save_settings(self):
        """Сохраняет настройки в файл"""
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить настройки: {e}")
            return False

    def get_ui_component(self, parent) -> ctk.CTkFrame:
        """Создает интерфейс для модуля настроек"""
        frame = ctk.CTkFrame(parent)
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Заголовок
        title = ctk.CTkLabel(
            frame,
            text="Настройки системы",
            font=("Arial", 24, "bold"),
            text_color=Styles.PRIMARY_COLOR
        )
        title.pack(pady=(0, 20))

        # Scrollable area
        scrollable_frame = ctk.CTkScrollableFrame(frame)
        scrollable_frame.pack(fill="both", expand=True)

        # Вкладки настроек
        tabview = ctk.CTkTabview(scrollable_frame)
        tabview.pack(fill="both", expand=True, padx=10, pady=10)

        # Вкладка: Внешний вид
        appearance_tab = tabview.add("Внешний вид")
        self._create_appearance_tab(appearance_tab)

        # Вкладка: Система
        system_tab = tabview.add("Система")
        self._create_system_tab(system_tab)

        # Вкладка: База данных
        database_tab = tabview.add("База данных")
        self._create_database_tab(database_tab)

        # Кнопки сохранения
        button_frame = ctk.CTkFrame(frame)
        button_frame.pack(fill="x", pady=20)

        save_btn = ctk.CTkButton(
            button_frame,
            text="Сохранить настройки",
            command=self._save_all_settings,
            width=200,
            height=45,
            fg_color=Styles.PRIMARY_COLOR,
            hover_color=Styles.HOVER_COLOR,
            font=("Arial", 14, "bold")
        )
        save_btn.pack(side="left", padx=10)

        reset_btn = ctk.CTkButton(
            button_frame,
            text="Сбросить настройки",
            command=self._reset_settings,
            width=200,
            height=45,
            fg_color=Styles.WARNING_COLOR,
            hover_color="#E68900",
            font=("Arial", 14)
        )
        reset_btn.pack(side="left", padx=10)

        return frame

    def _create_appearance_tab(self, parent):
        """Создает вкладку настроек внешнего вида"""
        # Тема оформления
        ctk.CTkLabel(parent, text="Тема оформления:", font=("Arial", 14, "bold")).pack(anchor="w", pady=(10, 5))

        self.appearance_var = ctk.StringVar(value=self.settings["appearance_mode"])
        appearance_frame = ctk.CTkFrame(parent)
        appearance_frame.pack(fill="x", pady=5)

        # Используем русские названия тем
        themes = {
            "dark": "Тёмная",
            "light": "Светлая",
            "system": "Системная"
        }

        for mode, label in themes.items():
            radio = ctk.CTkRadioButton(
                appearance_frame,
                text=label,
                variable=self.appearance_var,
                value=mode,
                font=("Arial", 12)
            )
            radio.pack(side="left", padx=10, pady=5)

        # Масштаб интерфейса
        ctk.CTkLabel(parent, text="Масштаб интерфейса:", font=("Arial", 14, "bold")).pack(anchor="w", pady=(20, 5))

        self.scaling_var = ctk.DoubleVar(value=self.settings["ui_scaling"])
        scaling_slider = ctk.CTkSlider(
            parent,
            from_=0.5,
            to=2.0,
            number_of_steps=15,
            variable=self.scaling_var,
            command=self._on_scaling_change
        )
        scaling_slider.pack(fill="x", pady=5)

        scaling_value = ctk.CTkLabel(parent, text=f"{self.scaling_var.get():.1f}x")
        scaling_value.pack(pady=5)
        self.scaling_label = scaling_value

    def _on_scaling_change(self, value):
        """Обработчик изменения масштаба"""
        self.scaling_label.configure(text=f"{float(value):.1f}x")

    def _create_system_tab(self, parent):
        """Создает вкладку системных настроек"""
        # Уведомления
        self.notifications_var = ctk.BooleanVar(value=self.settings["enable_notifications"])
        notifications_check = ctk.CTkCheckBox(
            parent,
            text="Включить уведомления",
            variable=self.notifications_var,
            font=("Arial", 12)
        )
        notifications_check.pack(anchor="w", pady=20)

        # Автосохранение
        self.autosave_var = ctk.BooleanVar(value=self.settings["auto_save"])
        autosave_check = ctk.CTkCheckBox(
            parent,
            text="Автосохранение форм",
            variable=self.autosave_var,
            font=("Arial", 12)
        )
        autosave_check.pack(anchor="w", pady=5)

        # Интервал резервного копирования
        ctk.CTkLabel(parent, text="Интервал резервного копирования (часы):",
                     font=("Arial", 14, "bold")).pack(anchor="w", pady=(20, 5))

        self.backup_var = ctk.IntVar(value=self.settings["backup_interval"])
        backup_slider = ctk.CTkSlider(
            parent,
            from_=1,
            to=168,  # неделя
            number_of_steps=167,
            variable=self.backup_var
        )
        backup_slider.pack(fill="x", pady=5)

        backup_value = ctk.CTkLabel(parent, text=f"{self.backup_var.get()} часов")
        backup_value.pack(pady=5)
        self.backup_label = backup_value

        backup_slider.configure(command=lambda v: self.backup_label.configure(text=f"{int(float(v))} часов"))

    def _create_database_tab(self, parent):
        """Создает вкладку настроек базы данных"""
        # Максимальное количество записей на странице
        ctk.CTkLabel(parent, text="Записей на странице:", font=("Arial", 14, "bold")).pack(anchor="w", pady=(10, 5))

        self.rows_var = ctk.IntVar(value=self.settings["max_rows_per_page"])
        rows_combo = ctk.CTkComboBox(
            parent,
            values=["10", "25", "50", "100", "Все"],
            variable=self.rows_var,
            width=200
        )
        rows_combo.pack(anchor="w", pady=5)

        # Статус по умолчанию для новых клиентов
        ctk.CTkLabel(parent, text="Статус по умолчанию для новых клиентов:",
                     font=("Arial", 14, "bold")).pack(anchor="w", pady=(20, 5))

        self.status_var = ctk.StringVar(value=self.settings["default_status"])
        status_combo = ctk.CTkComboBox(
            parent,
            values=["активный", "неактивный", "потенциальный"],  # На русском
            variable=self.status_var,
            width=200
        )
        status_combo.pack(anchor="w", pady=5)

        # Информация о базе данных
        ctk.CTkLabel(parent, text="Информация о БД:", font=("Arial", 14, "bold")).pack(anchor="w", pady=(20, 5))

        db_info_frame = ctk.CTkFrame(parent)
        db_info_frame.pack(fill="x", pady=5)

        db_path = Config.DB_PATH
        db_size = "Не доступно"

        try:
            import os
            if os.path.exists(db_path):
                db_size = f"{os.path.getsize(db_path) / 1024 / 1024:.2f} MB"
        except:
            pass

        info_text = f"Путь: {db_path}\nРазмер: {db_size}"
        db_info = ctk.CTkLabel(db_info_frame, text=info_text, justify="left")
        db_info.pack(padx=10, pady=10)

        # Кнопка резервного копирования БД
        backup_btn = ctk.CTkButton(
            parent,
            text="Создать резервную копию БД",
            command=self._create_backup,
            width=250,
            height=40,
            fg_color=Styles.SECONDARY_COLOR,
            hover_color="#8A2C5C"
        )
        backup_btn.pack(pady=20)

    def _create_backup(self):
        """Создает резервную копию базы данных"""
        try:
            from pathlib import Path
            import shutil
            import datetime

            db_path = Path(Config.DB_PATH)
            if not db_path.exists():
                messagebox.showerror("Ошибка", "Файл базы данных не найден!")
                return

            # Создаем папку для бэкапов если её нет
            backup_dir = Path(__file__).parent.parent / "backups"
            backup_dir.mkdir(exist_ok=True)

            # Генерируем имя файла с датой
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = backup_dir / f"crm_backup_{timestamp}.db"

            # Копируем файл
            shutil.copy2(db_path, backup_path)

            messagebox.showinfo("Успех", f"Резервная копия создана:\n{backup_path}")

        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось создать резервную копию: {e}")

    def _save_all_settings(self):
        """Сохраняет все настройки"""
        self.settings.update({
            "appearance_mode": self.appearance_var.get(),
            "ui_scaling": self.scaling_var.get(),
            "enable_notifications": self.notifications_var.get(),
            "auto_save": self.autosave_var.get(),
            "backup_interval": self.backup_var.get(),
            "max_rows_per_page": self.rows_var.get(),
            "default_status": self.status_var.get()
        })

        if self.save_settings():
            # Применяем настройки оформления - теперь только тему, без цветовой схемы
            ctk.set_appearance_mode(self.settings["appearance_mode"])

            messagebox.showinfo("Успех", "Настройки сохранены!\nПерезапустите приложение для полного применения изменений.")
        else:
            messagebox.showerror("Ошибка", "Не удалось сохранить настройки!")

    def _reset_settings(self):
        """Сбрасывает настройки к значениям по умолчанию"""
        confirm = messagebox.askyesno(
            "Сброс настроек",
            "Вы уверены, что хотите сбросить все настройки к значениям по умолчанию?"
        )

        if confirm:
            self.settings = {
                "appearance_mode": "dark",
                "ui_scaling": 1.0,
                "enable_notifications": True,
                "auto_save": True,
                "backup_interval": 24,
                "max_rows_per_page": 50,
                "default_status": "активный"  # На русском
            }

            # Обновляем UI
            self.appearance_var.set(self.settings["appearance_mode"])
            self.scaling_var.set(self.settings["ui_scaling"])
            self.notifications_var.set(self.settings["enable_notifications"])
            self.autosave_var.set(self.settings["auto_save"])
            self.backup_var.set(self.settings["backup_interval"])
            self.rows_var.set(self.settings["max_rows_per_page"])
            self.status_var.set(self.settings["default_status"])

            messagebox.showinfo("Сброс", "Настройки сброшены к значениям по умолчанию!")

    def initialize_database(self):
        """Инициализирует таблицы БД для модуля"""
        pass