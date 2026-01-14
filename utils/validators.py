"""
Валидаторы данных
"""
import re
from datetime import datetime
from typing import Optional, Tuple, Dict
from tkinter import messagebox
import customtkinter as ctk


class Validators:
    """Класс для валидации данных"""

    # Шаблоны масок
    MASKS = {
        'name': {
            'pattern': r'^[А-Яа-яA-Za-z\s\-]{2,50}$',
            'example': 'Иван Иванов',
            'error': 'Имя должно содержать только буквы, пробелы и дефисы (2-50 символов)'
        },
        'email': {
            'pattern': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
            'example': 'example@domain.com',
            'error': 'Неверный формат email'
        },
        'phone': {
            'pattern': r'^(\+7|8)?[\s\-]?\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}$',
            'example': '+7 (999) 123-45-67 или 89991234567',
            'error': 'Неверный формат телефона. Пример: +7 (999) 123-45-67'
        },
        'company': {
            'pattern': r'^[А-Яа-яA-Za-z0-9\s\-\.,\(\)]{2,100}$',
            'example': 'ООО "Ромашка"',
            'error': 'Название компании должно быть 2-100 символов'
        }
    }

    @staticmethod
    def is_valid_email(email: str) -> bool:
        """Проверяет валидность email"""
        return bool(re.match(Validators.MASKS['email']['pattern'], email))

    @staticmethod
    def is_valid_phone(phone: str) -> bool:
        """Проверяет валидность телефона"""
        # Удаляем все пробелы, скобки и дефисы
        cleaned = re.sub(r'[\s\-\(\)]', '', phone)
        # Проверяем длину и содержание
        return bool(re.match(Validators.MASKS['phone']['pattern'], phone))

    @staticmethod
    def is_valid_name(name: str) -> bool:
        """Проверяет валидность имени"""
        return bool(re.match(Validators.MASKS['name']['pattern'], name))

    @staticmethod
    def is_valid_company(company: str) -> bool:
        """Проверяет валидность названия компании"""
        return bool(re.match(Validators.MASKS['company']['pattern'], company))

    @staticmethod
    def is_valid_date(date_str: str, fmt: str = "%Y-%m-%d") -> bool:
        """Проверяет валидность даты"""
        try:
            datetime.strptime(date_str, fmt)
            return True
        except ValueError:
            return False

    @staticmethod
    def is_valid_number(value: str, min_val: float = None,
                        max_val: float = None) -> bool:
        """Проверяет валидность числа"""
        try:
            num = float(value)
            if min_val is not None and num < min_val:
                return False
            if max_val is not None and num > max_val:
                return False
            return True
        except ValueError:
            return False

    @staticmethod
    def required(value: str) -> bool:
        """Проверяет, что поле не пустое"""
        return bool(str(value).strip())

    @staticmethod
    def format_phone(phone: str) -> str:
        """Форматирует телефон в единый формат"""
        # Удаляем все нецифровые символы
        digits = re.sub(r'\D', '', phone)

        if digits.startswith('8') and len(digits) == 11:
            digits = '7' + digits[1:]
        elif digits.startswith('7') and len(digits) == 11:
            pass
        elif len(digits) == 10:
            digits = '7' + digits

        if len(digits) == 11 and digits.startswith('7'):
            return f"+7 ({digits[1:4]}) {digits[4:7]}-{digits[7:9]}-{digits[9:]}"
        return phone

    @staticmethod
    def create_field_with_example(parent, field_type: str, label: str,
                                 required: bool = False, width: int = 300) -> Tuple[ctk.CTkEntry, ctk.CTkLabel]:
        """Создает поле ввода с примером"""
        frame = ctk.CTkFrame(parent)

        # Метка поля
        field_label = ctk.CTkLabel(
            frame,
            text=label + (" *" if required else ""),
            font=("Arial", 12)
        )
        field_label.grid(row=0, column=0, sticky="w", padx=5, pady=(5, 0))

        # Поле ввода
        entry = ctk.CTkEntry(frame, width=width)
        entry.grid(row=1, column=0, sticky="ew", padx=5, pady=(0, 2))

        # Метка с примером
        example = Validators.MASKS.get(field_type, {}).get('example', '')
        example_label = ctk.CTkLabel(
            frame,
            text=f"Пример: {example}",
            font=("Arial", 10),
            text_color="gray"
        )
        example_label.grid(row=2, column=0, sticky="w", padx=5, pady=(0, 5))

        frame.grid_columnconfigure(0, weight=1)

        return entry, example_label, frame

    @staticmethod
    def validate_field(field_type: str, value: str, field_name: str = None) -> Tuple[bool, str]:
        """Валидирует поле и возвращает сообщение об ошибке"""
        if not value:
            return (False, f"Поле '{field_name}' обязательно для заполнения") if field_name else (False, "Поле обязательно для заполнения")

        validators = {
            'name': Validators.is_valid_name,
            'email': Validators.is_valid_email,
            'phone': Validators.is_valid_phone,
            'company': Validators.is_valid_company
        }

        if field_type in validators:
            if not validators[field_type](value):
                return False, Validators.MASKS.get(field_type, {}).get('error', 'Неверный формат')

        return True, ""