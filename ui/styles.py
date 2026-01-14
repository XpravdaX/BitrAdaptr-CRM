"""
Стили и темы приложения
"""
import customtkinter as ctk


class Styles:
    """Класс для управления стилями"""

    # Цветовая палитра
    PRIMARY_COLOR = "#2E86AB"
    SECONDARY_COLOR = "#A23B72"
    SUCCESS_COLOR = "#4CAF50"
    WARNING_COLOR = "#FF9800"
    ERROR_COLOR = "#F44336"
    HOVER_COLOR = "#1B5E7F"

    # Фоновые цвета
    BG_LIGHT = "#F5F5F5"
    BG_DARK = "#2B2B2B"

    @classmethod
    def setup_theme(cls):
        """Настраивает тему приложения"""
        ctk.set_appearance_mode("dark")  # dark, light, system
        ctk.set_default_color_theme("dark-blue")  # blue, green, dark-blue

    @classmethod
    def create_header_label(cls, parent, text: str):
        """Создает заголовок"""
        return ctk.CTkLabel(
            parent,
            text=text,
            font=("Arial", 24, "bold"),
            text_color=cls.PRIMARY_COLOR
        )

    @classmethod
    def create_card(cls, parent):
        """Создает карточку с тенью"""
        frame = ctk.CTkFrame(
            parent,
            corner_radius=10,
            border_width=1,
            border_color="#555555"
        )
        return frame

    @classmethod
    def create_primary_button(cls, parent, text: str, command=None):
        """Создает основную кнопку"""
        return ctk.CTkButton(
            parent,
            text=text,
            command=command,
            fg_color=cls.PRIMARY_COLOR,
            hover_color=cls.HOVER_COLOR,
            font=("Arial", 14, "bold"),
            height=40,
            corner_radius=8
        )