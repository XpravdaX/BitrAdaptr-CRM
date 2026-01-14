"""
Модуль управления клиентами
"""
import customtkinter as ctk
from tkinter import messagebox
from typing import Dict, Any, List, Tuple
from datetime import datetime
import re

from core.database import db_manager
from core.models import BaseModel, CustomField
from modules.base_module import BaseModule
from ui.styles import Styles
from utils.validators import Validators


class Client(BaseModel):
    """Модель клиента"""

    TABLE_NAME = "clients"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = kwargs.get('name', '')
        self.email = kwargs.get('email', '')
        self.phone = kwargs.get('phone', '')
        self.company = kwargs.get('company', '')
        self.status = kwargs.get('status', 'активный')  # active, inactive, lead
        self.notes = kwargs.get('notes', '')

        # Динамические пользовательские поля
        for key, value in kwargs.items():
            if key not in ['id', 'name', 'email', 'phone', 'company',
                           'status', 'notes', 'created_at', 'updated_at']:
                setattr(self, key, value)

    def to_dict(self) -> Dict[str, Any]:
        data = {
            'name': self.name,
            'email': self.email,
            'phone': Validators.format_phone(self.phone) if self.phone else '',
            'company': self.company,
            'status': self.status,
            'notes': self.notes,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
        if self.id:
            data['id'] = self.id
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Client':
        return cls(**data)


class ClientsModule(BaseModule):
    """Модуль для работы с клиентами"""

    MODULE_NAME = "Клиенты"
    MODULE_VERSION = "1.0"

    def __init__(self):
        super().__init__()
        self.model_class = Client
        self.initialize_database()
        self._setup_default_fields()
        self.selected_client_id = None  # ID выбранного клиента для удаления/редактирования
        self.field_dependencies = {}  # Зависимости между полями

    def _setup_default_fields(self):
        """Настраивает поля по умолчанию"""
        self.custom_fields = [
            CustomField("name", "text", "Имя", required=True),
            CustomField("email", "email", "Email", required=False),
            CustomField("phone", "phone", "Телефон", required=True),
            CustomField("company", "text", "Компания", required=False),
            CustomField("status", "select", "Статус", required=True,
                        options=['активный', 'неактивный', 'потенциальный']),
            CustomField("notes", "textarea", "Заметки", required=False)
        ]

        # Настраиваем зависимости между полями
        self._setup_field_dependencies()

    def _setup_field_dependencies(self):
        """Настраивает зависимости между полями"""
        self.field_dependencies = {
            'status': {
                'trigger_value': 'потенциальный',
                'dependent_field': 'company',
                'action': 'make_required',
                'message': 'Для потенциальных клиентов обязательно указание компании'
            }
        }

    def initialize_database(self):
        """Создает таблицу клиентов"""
        schema = self.get_fields_schema()
        schema.update({
            'name': 'TEXT NOT NULL',
            'email': 'TEXT',
            'phone': 'TEXT',
            'company': 'TEXT',
            'status': 'TEXT DEFAULT "активный"',
            'notes': 'TEXT'
        })

        db_manager.create_table(Client.TABLE_NAME, schema)

    def get_fields_schema(self) -> Dict[str, str]:
        schema = super().get_fields_schema()
        # Можно динамически добавлять пользовательские поля
        for field in self.custom_fields:
            if field.name not in schema:
                # Определяем тип поля для SQLite
                sql_type = self._get_sql_type(field.type)
                schema[field.name] = sql_type
        return schema

    def _get_sql_type(self, field_type: str) -> str:
        """Преобразует тип поля в SQL тип"""
        type_mapping = {
            'text': 'TEXT',
            'email': 'TEXT',
            'phone': 'TEXT',
            'number': 'REAL',
            'date': 'TEXT',
            'select': 'TEXT',
            'textarea': 'TEXT',
            'boolean': 'INTEGER'
        }
        return type_mapping.get(field_type, 'TEXT')

    def get_ui_component(self, parent) -> ctk.CTkFrame:
        """Создает интерфейс для модуля клиентов"""
        self.main_frame = ctk.CTkFrame(parent)

        # Создаем вкладки
        self.tabview = ctk.CTkTabview(self.main_frame)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)

        # Вкладка списка клиентов
        self.list_tab = self.tabview.add("Список клиентов")
        self._create_list_view(self.list_tab)

        # Вкладка добавления клиента
        self.add_tab = self.tabview.add("Добавить клиента")
        self._create_add_form(self.add_tab)

        # Вкладка удаления/редактирования
        self.edit_tab = self.tabview.add("Управление клиентом")
        self._create_edit_form(self.edit_tab)

        return self.main_frame

    def _create_list_view(self, parent):
        """Создает вид списка клиентов"""
        # Панель поиска
        search_frame = ctk.CTkFrame(parent)
        search_frame.pack(fill="x", padx=10, pady=(10, 5))

        ctk.CTkLabel(search_frame, text="Поиск:").pack(side="left", padx=5)
        self.search_entry = ctk.CTkEntry(search_frame, width=300)
        self.search_entry.pack(side="left", padx=5, pady=5)

        search_btn = ctk.CTkButton(search_frame, text="Найти", width=100, command=self._search_clients)
        search_btn.pack(side="left", padx=5)

        refresh_btn = ctk.CTkButton(search_frame, text="Обновить", width=100,
                                     command=self._refresh_clients_list)
        refresh_btn.pack(side="left", padx=5)

        # Таблица клиентов
        columns = ["ID", "Имя", "Email", "Телефон", "Компания", "Статус", "Действия"]
        self.tree_frame = ctk.CTkScrollableFrame(parent)
        self.tree_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # Заголовки
        for i, col in enumerate(columns):
            header = ctk.CTkLabel(self.tree_frame, text=col, font=("Arial", 12, "bold"))
            header.grid(row=0, column=i, padx=5, pady=5, sticky="ew")
            self.tree_frame.grid_columnconfigure(i, weight=1)

        # Загрузка данных
        self._load_clients_to_grid()

    def _load_clients_to_grid(self, search_term: str = None):
        """Загружает клиентов в таблицу"""
        # Очищаем старые данные (кроме заголовков)
        for widget in self.tree_frame.winfo_children():
            if widget.grid_info()["row"] > 0:
                widget.destroy()

        # Получаем клиентов
        if search_term:
            clients = Client.get_all(where="name LIKE ? OR email LIKE ? OR phone LIKE ?",
                                    params=(f"%{search_term}%", f"%{search_term}%", f"%{search_term}%"))
        else:
            clients = Client.get_all()

        for i, client in enumerate(clients, start=1):
            data = [client.id, client.name, client.email,
                    Validators.format_phone(client.phone) if client.phone else "",
                    client.company, client.status]

            # Данные клиента
            for j, value in enumerate(data):
                cell = ctk.CTkLabel(self.tree_frame, text=str(value), anchor="w")
                cell.grid(row=i, column=j, padx=5, pady=2, sticky="ew")

            # Кнопка выбора для редактирования/удаления
            select_btn = ctk.CTkButton(
                self.tree_frame,
                text="Выбрать",
                width=80,
                height=25,
                command=lambda cid=client.id: self._select_client(cid)
            )
            select_btn.grid(row=i, column=6, padx=5, pady=2)

    def _search_clients(self):
        """Поиск клиентов"""
        search_term = self.search_entry.get().strip()
        self._load_clients_to_grid(search_term)

    def _refresh_clients_list(self):
        """Обновляет список клиентов"""
        self.search_entry.delete(0, "end")
        self._load_clients_to_grid()

    def _select_client(self, client_id: int):
        """Выбирает клиента для редактирования/удаления"""
        self.selected_client_id = client_id
        client = Client.get(client_id)

        if client:
            # Переключаемся на вкладку управления
            self.tabview.set("Управление клиентом")

            # Заполняем поля формы
            self._fill_edit_form(client)
            messagebox.showinfo("Выбран клиент", f"Выбран клиент: {client.name} (ID: {client.id})")

    def _create_add_form(self, parent):
        """Создает форму добавления клиента"""
        form_frame = ctk.CTkScrollableFrame(parent)
        form_frame.pack(fill="both", expand=True, padx=20, pady=20)

        self.form_fields = {}
        self.form_widgets = {}  # Для хранения виджетов полей
        current_row = 0

        # Создаем поля формы из custom_fields
        for field in self.custom_fields:
            if field.type in ['name', 'email', 'phone', 'company']:
                # Создаем контейнер для поля
                field_container = ctk.CTkFrame(form_frame)
                field_container.grid(row=current_row, column=0, columnspan=2, sticky="ew", padx=5, pady=10)
                field_container.grid_columnconfigure(1, weight=1)

                # Метка поля
                field_label = ctk.CTkLabel(
                    field_container,
                    text=field.label + (" *" if field.required else ""),
                    font=("Arial", 12)
                )
                field_label.grid(row=0, column=0, sticky="w", padx=(0, 10), pady=(0, 5))

                # Поле ввода
                entry = ctk.CTkEntry(field_container, width=400)
                entry.grid(row=0, column=1, sticky="ew", padx=(0, 0), pady=(0, 5))

                # Метка с примером
                example = Validators.MASKS.get(field.type, {}).get('example', '')
                example_label = ctk.CTkLabel(
                    field_container,
                    text=f"Пример: {example}",
                    font=("Arial", 10),
                    text_color="gray"
                )
                example_label.grid(row=1, column=0, columnspan=2, sticky="w", padx=(0, 0), pady=(2, 0))

                # Настраиваем маску ввода
                if field.type == 'phone':
                    entry.bind('<KeyRelease>', lambda e, f=field.type: self._apply_phone_mask(e, f))
                elif field.type == 'name':
                    entry.bind('<KeyRelease>', lambda e, f=field.type: self._validate_name_input(e, f))

                self.form_fields[field.name] = (entry, field)
                self.form_widgets[field.name] = {
                    'entry': entry,
                    'example': example_label,
                    'container': field_container,
                    'label': field_label
                }

            elif field.type == "select":
                # Контейнер для выпадающего списка
                field_container = ctk.CTkFrame(form_frame)
                field_container.grid(row=current_row, column=0, columnspan=2, sticky="ew", padx=5, pady=10)
                field_container.grid_columnconfigure(1, weight=1)

                label = ctk.CTkLabel(
                    field_container,
                    text=field.label + (" *" if field.required else ""),
                    font=("Arial", 12)
                )
                label.grid(row=0, column=0, sticky="w", padx=(0, 10), pady=5)

                entry = ctk.CTkComboBox(field_container, values=field.options, width=400)
                entry.grid(row=0, column=1, sticky="ew", padx=(0, 0), pady=5)
                entry.configure(command=lambda v, f=field.name: self._handle_dependency(f, v))

                # Пример для выпадающего списка
                example_label = ctk.CTkLabel(
                    field_container,
                    text=f"Пример: выберите один из вариантов",
                    font=("Arial", 10),
                    text_color="gray"
                )
                example_label.grid(row=1, column=0, columnspan=2, sticky="w", padx=(0, 0), pady=(2, 0))

                self.form_fields[field.name] = (entry, field)
                self.form_widgets[field.name] = {
                    'combo': entry,
                    'label': label,
                    'example': example_label,
                    'container': field_container
                }

            elif field.type == "textarea":
                # Контейнер для текстового поля
                field_container = ctk.CTkFrame(form_frame)
                field_container.grid(row=current_row, column=0, columnspan=2, sticky="ew", padx=5, pady=10)
                field_container.grid_columnconfigure(1, weight=1)

                label = ctk.CTkLabel(
                    field_container,
                    text=field.label + (" *" if field.required else ""),
                    font=("Arial", 12)
                )
                label.grid(row=0, column=0, sticky="w", padx=(0, 10), pady=(0, 5))

                entry = ctk.CTkTextbox(field_container, height=100)
                entry.grid(row=0, column=1, sticky="ew", padx=(0, 0), pady=(0, 5))

                # Пример для текстового поля
                example_label = ctk.CTkLabel(
                    field_container,
                    text=f"Пример: дополнительная информация о клиенте",
                    font=("Arial", 10),
                    text_color="gray"
                )
                example_label.grid(row=1, column=0, columnspan=2, sticky="w", padx=(0, 0), pady=(2, 0))

                self.form_fields[field.name] = (entry, field)
                self.form_widgets[field.name] = {
                    'textbox': entry,
                    'label': label,
                    'example': example_label,
                    'container': field_container
                }
            else:
                # Контейнер для обычного поля
                field_container = ctk.CTkFrame(form_frame)
                field_container.grid(row=current_row, column=0, columnspan=2, sticky="ew", padx=5, pady=10)
                field_container.grid_columnconfigure(1, weight=1)

                label = ctk.CTkLabel(
                    field_container,
                    text=field.label + (" *" if field.required else ""),
                    font=("Arial", 12)
                )
                label.grid(row=0, column=0, sticky="w", padx=(0, 10), pady=5)

                entry = ctk.CTkEntry(field_container, width=400)
                entry.grid(row=0, column=1, sticky="ew", padx=(0, 0), pady=5)

                # Пример для обычного поля
                example_label = ctk.CTkLabel(
                    field_container,
                    text=f"Пример: введите {field.label.lower()}",
                    font=("Arial", 10),
                    text_color="gray"
                )
                example_label.grid(row=1, column=0, columnspan=2, sticky="w", padx=(0, 0), pady=(2, 0))

                self.form_fields[field.name] = (entry, field)
                self.form_widgets[field.name] = {
                    'entry': entry,
                    'label': label,
                    'example': example_label,
                    'container': field_container
                }

            current_row += 1

        # Кнопки
        button_frame = ctk.CTkFrame(form_frame)
        button_frame.grid(row=current_row, column=0, columnspan=2, pady=20)

        save_btn = ctk.CTkButton(
            button_frame,
            text="Сохранить клиента",
            command=self._save_client,
            width=150,
            height=40,
            fg_color=Styles.PRIMARY_COLOR,
            hover_color=Styles.HOVER_COLOR
        )
        save_btn.pack(side="left", padx=10)

        clear_btn = ctk.CTkButton(
            button_frame,
            text="Очистить форму",
            command=self._clear_form,
            width=150,
            height=40
        )
        clear_btn.pack(side="left", padx=10)

        form_frame.grid_columnconfigure(1, weight=1)

    def _apply_phone_mask(self, event, field_type):
        """Применяет маску для телефона"""
        widget = event.widget
        value = widget.get()

        if not value:
            return

        # Удаляем все нецифровые символы
        digits = re.sub(r'\D', '', value)

        if len(digits) <= 1:
            formatted = digits
        elif len(digits) <= 4:
            formatted = f"+7 ({digits[1:4]}"
        elif len(digits) <= 7:
            formatted = f"+7 ({digits[1:4]}) {digits[4:7]}"
        elif len(digits) <= 9:
            formatted = f"+7 ({digits[1:4]}) {digits[4:7]}-{digits[7:9]}"
        else:
            formatted = f"+7 ({digits[1:4]}) {digits[4:7]}-{digits[7:9]}-{digits[9:11]}"

        # Обновляем значение, если оно изменилось
        if formatted != value:
            widget.delete(0, "end")
            widget.insert(0, formatted)

            # Перемещаем курсор в конец
            widget.icursor(len(formatted))

    def _validate_name_input(self, event, field_type):
        """Валидирует ввод имени"""
        widget = event.widget
        value = widget.get()

        # Разрешаем только буквы, пробелы и дефисы
        cleaned = re.sub(r'[^А-Яа-яA-Za-z\s\-]', '', value)

        if cleaned != value:
            widget.delete(0, "end")
            widget.insert(0, cleaned)
            widget.icursor(len(cleaned))

    def _handle_dependency(self, field_name, value):
        """Обрабатывает зависимости между полями"""
        if field_name in self.field_dependencies:
            dependency = self.field_dependencies[field_name]

            if dependency.get('trigger_value') == value:
                dependent_field = dependency['dependent_field']
                action = dependency['action']

                if dependent_field in self.form_widgets:
                    if action == 'make_required':
                        # Обновляем метку поля
                        if 'label' in self.form_widgets[dependent_field]:
                            label = self.form_widgets[dependent_field]['label']
                            current_text = label.cget('text')
                            if ' *' not in current_text:
                                label.configure(text=current_text + ' *')

                        # Показываем сообщение
                        messagebox.showinfo("Зависимость полей", dependency['message'])

    def _save_client(self):
        """Сохраняет клиента из формы"""
        data = {}
        validation_errors = []

        for field_name, (widget, field) in self.form_fields.items():
            if isinstance(widget, ctk.CTkTextbox):
                value = widget.get("1.0", "end-1c")
            elif isinstance(widget, ctk.CTkComboBox):
                value = widget.get()
            else:
                value = widget.get()

            # Валидация в зависимости от типа поля
            if field.type in ['name', 'email', 'phone', 'company']:
                is_valid, error_msg = Validators.validate_field(field.type, value, field.label)
                if not is_valid and (field.required or value):
                    validation_errors.append(error_msg)
                    # Подсвечиваем поле с ошибкой
                    if isinstance(widget, ctk.CTkEntry):
                        widget.configure(border_color=Styles.ERROR_COLOR)
                else:
                    if isinstance(widget, ctk.CTkEntry):
                        widget.configure(border_color="#4A5568")
            else:
                # Стандартная валидация для других типов полей
                if field.required and not value:
                    validation_errors.append(f"Поле '{field.label}' обязательно для заполнения!")
                    if isinstance(widget, ctk.CTkEntry):
                        widget.configure(border_color=Styles.ERROR_COLOR)
                else:
                    if isinstance(widget, ctk.CTkEntry):
                        widget.configure(border_color="#4A5568")

            # Форматирование телефона
            if field.type == 'phone' and value:
                value = Validators.format_phone(value)

            data[field_name] = value

        # Проверяем зависимости
        status = data.get('status')
        company = data.get('company')

        if status == 'потенциальный' and not company:
            validation_errors.append("Для потенциальных клиентов обязательно указание компании!")

        if validation_errors:
            messagebox.showerror("Ошибки валидации", "\n".join(validation_errors))
            return

        # Создаем и сохраняем клиента
        client = Client(**data)
        client_id = client.save()

        messagebox.showinfo("Успех", f"Клиент сохранен! ID: {client_id}")

        # Обновляем список клиентов
        self._refresh_clients_list()

        # Очищаем форму
        self._clear_form()

        # Переключаемся на вкладку списка
        self.tabview.set("Список клиентов")

    def _clear_form(self):
        """Очищает форму"""
        for widget, field in self.form_fields.values():
            if isinstance(widget, ctk.CTkTextbox):
                widget.delete("1.0", "end")
            elif isinstance(widget, ctk.CTkComboBox):
                widget.set("")
            else:
                widget.delete(0, "end")
                widget.configure(border_color="#4A5568")

    def _create_edit_form(self, parent):
        """Создает форму управления клиентом"""
        form_frame = ctk.CTkScrollableFrame(parent)
        form_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Информация о выбранном клиенте
        self.selected_client_info = ctk.CTkLabel(
            form_frame,
            text="Выберите клиента из списка",
            font=("Arial", 16, "bold"),
            text_color=Styles.PRIMARY_COLOR
        )
        self.selected_client_info.grid(row=0, column=0, columnspan=2, pady=10)

        # Форма редактирования
        self.edit_form_fields = {}
        self.edit_form_widgets = {}
        current_row = 1

        for field in self.custom_fields:
            if field.type in ['name', 'email', 'phone', 'company']:
                # Создаем контейнер для поля
                field_container = ctk.CTkFrame(form_frame)
                field_container.grid(row=current_row, column=0, columnspan=2, sticky="ew", padx=5, pady=10)
                field_container.grid_columnconfigure(1, weight=1)

                # Метка поля
                field_label = ctk.CTkLabel(
                    field_container,
                    text=field.label + (" *" if field.required else ""),
                    font=("Arial", 12)
                )
                field_label.grid(row=0, column=0, sticky="w", padx=(0, 10), pady=(0, 5))

                # Поле ввода
                entry = ctk.CTkEntry(field_container, width=400)
                entry.grid(row=0, column=1, sticky="ew", padx=(0, 0), pady=(0, 5))

                # Метка с примером
                example = Validators.MASKS.get(field.type, {}).get('example', '')
                example_label = ctk.CTkLabel(
                    field_container,
                    text=f"Пример: {example}",
                    font=("Arial", 10),
                    text_color="gray"
                )
                example_label.grid(row=1, column=0, columnspan=2, sticky="w", padx=(0, 0), pady=(2, 0))

                # Настраиваем маску ввода
                if field.type == 'phone':
                    entry.bind('<KeyRelease>', lambda e, f=field.type: self._apply_phone_mask(e, f))
                elif field.type == 'name':
                    entry.bind('<KeyRelease>', lambda e, f=field.type: self._validate_name_input(e, f))

                self.edit_form_fields[field.name] = (entry, field)
                self.edit_form_widgets[field.name] = {
                    'entry': entry,
                    'example': example_label,
                    'container': field_container,
                    'label': field_label
                }

            elif field.type == "select":
                # Контейнер для выпадающего списка
                field_container = ctk.CTkFrame(form_frame)
                field_container.grid(row=current_row, column=0, columnspan=2, sticky="ew", padx=5, pady=10)
                field_container.grid_columnconfigure(1, weight=1)

                label = ctk.CTkLabel(
                    field_container,
                    text=field.label + (" *" if field.required else ""),
                    font=("Arial", 12)
                )
                label.grid(row=0, column=0, sticky="w", padx=(0, 10), pady=5)

                entry = ctk.CTkComboBox(field_container, values=field.options, width=400)
                entry.grid(row=0, column=1, sticky="ew", padx=(0, 0), pady=5)
                entry.configure(command=lambda v, f=field.name: self._handle_edit_dependency(f, v))

                # Пример для выпадающего списка
                example_label = ctk.CTkLabel(
                    field_container,
                    text=f"Пример: выберите один из вариантов",
                    font=("Arial", 10),
                    text_color="gray"
                )
                example_label.grid(row=1, column=0, columnspan=2, sticky="w", padx=(0, 0), pady=(2, 0))

                self.edit_form_fields[field.name] = (entry, field)
                self.edit_form_widgets[field.name] = {
                    'combo': entry,
                    'label': label,
                    'example': example_label,
                    'container': field_container
                }

            elif field.type == "textarea":
                # Контейнер для текстового поля
                field_container = ctk.CTkFrame(form_frame)
                field_container.grid(row=current_row, column=0, columnspan=2, sticky="ew", padx=5, pady=10)
                field_container.grid_columnconfigure(1, weight=1)

                label = ctk.CTkLabel(
                    field_container,
                    text=field.label + (" *" if field.required else ""),
                    font=("Arial", 12)
                )
                label.grid(row=0, column=0, sticky="w", padx=(0, 10), pady=(0, 5))

                entry = ctk.CTkTextbox(field_container, height=100)
                entry.grid(row=0, column=1, sticky="ew", padx=(0, 0), pady=(0, 5))

                # Пример для текстового поля
                example_label = ctk.CTkLabel(
                    field_container,
                    text=f"Пример: дополнительная информация о клиенте",
                    font=("Arial", 10),
                    text_color="gray"
                )
                example_label.grid(row=1, column=0, columnspan=2, sticky="w", padx=(0, 0), pady=(2, 0))

                self.edit_form_fields[field.name] = (entry, field)
                self.edit_form_widgets[field.name] = {
                    'textbox': entry,
                    'label': label,
                    'example': example_label,
                    'container': field_container
                }
            else:
                # Контейнер для обычного поля
                field_container = ctk.CTkFrame(form_frame)
                field_container.grid(row=current_row, column=0, columnspan=2, sticky="ew", padx=5, pady=10)
                field_container.grid_columnconfigure(1, weight=1)

                label = ctk.CTkLabel(
                    field_container,
                    text=field.label + (" *" if field.required else ""),
                    font=("Arial", 12)
                )
                label.grid(row=0, column=0, sticky="w", padx=(0, 10), pady=5)

                entry = ctk.CTkEntry(field_container, width=400)
                entry.grid(row=0, column=1, sticky="ew", padx=(0, 0), pady=5)

                # Пример для обычного поля
                example_label = ctk.CTkLabel(
                    field_container,
                    text=f"Пример: введите {field.label.lower()}",
                    font=("Arial", 10),
                    text_color="gray"
                )
                example_label.grid(row=1, column=0, columnspan=2, sticky="w", padx=(0, 0), pady=(2, 0))

                self.edit_form_fields[field.name] = (entry, field)
                self.edit_form_widgets[field.name] = {
                    'entry': entry,
                    'label': label,
                    'example': example_label,
                    'container': field_container
                }

            current_row += 1

        # Кнопки управления
        button_frame = ctk.CTkFrame(form_frame)
        button_frame.grid(row=current_row, column=0, columnspan=2, pady=30)

        # Кнопка обновить
        update_btn = ctk.CTkButton(
            button_frame,
            text="Обновить данные",
            command=self._update_client,
            width=150,
            height=40,
            fg_color=Styles.PRIMARY_COLOR,
            hover_color=Styles.HOVER_COLOR
        )
        update_btn.pack(side="left", padx=10)

        # Кнопка удалить
        delete_btn = ctk.CTkButton(
            button_frame,
            text="Удалить клиента",
            command=self._delete_client,
            width=150,
            height=40,
            fg_color=Styles.ERROR_COLOR,
            hover_color="#B71C1C"
        )
        delete_btn.pack(side="left", padx=10)

        # Кнопка очистить
        clear_edit_btn = ctk.CTkButton(
            button_frame,
            text="Очистить форму",
            command=self._clear_edit_form,
            width=150,
            height=40
        )
        clear_edit_btn.pack(side="left", padx=10)

        form_frame.grid_columnconfigure(1, weight=1)

    def _handle_edit_dependency(self, field_name, value):
        """Обрабатывает зависимости между полями в форме редактирования"""
        if field_name in self.field_dependencies:
            dependency = self.field_dependencies[field_name]

            if dependency.get('trigger_value') == value:
                dependent_field = dependency['dependent_field']
                action = dependency['action']

                if dependent_field in self.edit_form_widgets:
                    if action == 'make_required':
                        # Обновляем метку поля
                        if 'label' in self.edit_form_widgets[dependent_field]:
                            label = self.edit_form_widgets[dependent_field]['label']
                            current_text = label.cget('text')
                            if ' *' not in current_text:
                                label.configure(text=current_text + ' *')

                        # Показываем сообщение
                        messagebox.showinfo("Зависимость полей", dependency['message'])

    def _fill_edit_form(self, client: Client):
        """Заполняет форму редактирования данными клиента"""
        self.selected_client_info.configure(
            text=f"Редактирование: {client.name} (ID: {client.id})"
        )

        for field_name, (widget, field) in self.edit_form_fields.items():
            value = getattr(client, field_name, "")

            if isinstance(widget, ctk.CTkTextbox):
                widget.delete("1.0", "end")
                widget.insert("1.0", value if value else "")
            elif isinstance(widget, ctk.CTkComboBox):
                widget.set(value if value else "")
            else:
                widget.delete(0, "end")
                widget.insert(0, value if value else "")

    def _update_client(self):
        """Обновляет данные клиента"""
        if not self.selected_client_id:
            messagebox.showwarning("Предупреждение", "Сначала выберите клиента!")
            return

        client = Client.get(self.selected_client_id)
        if not client:
            messagebox.showerror("Ошибка", "Клиент не найден!")
            return

        data = {}
        validation_errors = []

        for field_name, (widget, field) in self.edit_form_fields.items():
            if isinstance(widget, ctk.CTkTextbox):
                value = widget.get("1.0", "end-1c")
            elif isinstance(widget, ctk.CTkComboBox):
                value = widget.get()
            else:
                value = widget.get()

            # Валидация в зависимости от типа поля
            if field.type in ['name', 'email', 'phone', 'company']:
                is_valid, error_msg = Validators.validate_field(field.type, value, field.label)
                if not is_valid and (field.required or value):
                    validation_errors.append(error_msg)
                    # Подсвечиваем поле с ошибкой
                    if isinstance(widget, ctk.CTkEntry):
                        widget.configure(border_color=Styles.ERROR_COLOR)
                else:
                    if isinstance(widget, ctk.CTkEntry):
                        widget.configure(border_color="#4A5568")
            else:
                # Стандартная валидация для других типов полей
                if field.required and not value:
                    validation_errors.append(f"Поле '{field.label}' обязательно для заполнения!")
                    if isinstance(widget, ctk.CTkEntry):
                        widget.configure(border_color=Styles.ERROR_COLOR)
                else:
                    if isinstance(widget, ctk.CTkEntry):
                        widget.configure(border_color="#4A5568")

            # Форматирование телефона
            if field.type == 'phone' and value:
                value = Validators.format_phone(value)

            data[field_name] = value

        # Проверяем зависимости
        status = data.get('status')
        company = data.get('company')

        if status == 'потенциальный' and not company:
            validation_errors.append("Для потенциальных клиентов обязательно указание компании!")

        if validation_errors:
            messagebox.showerror("Ошибки валидации", "\n".join(validation_errors))
            return

        # Обновляем клиента
        for key, value in data.items():
            setattr(client, key, value)

        client.save()
        messagebox.showinfo("Успех", f"Данные клиента {client.name} обновлены!")

        # Обновляем список клиентов
        self._refresh_clients_list()

    def _delete_client(self):
        """Удаляет выбранного клиента"""
        if not self.selected_client_id:
            messagebox.showwarning("Предупреждение", "Сначала выберите клиента!")
            return

        client = Client.get(self.selected_client_id)
        if not client:
            messagebox.showerror("Ошибка", "Клиент не найден!")
            return

        # Подтверждение удаления
        confirm = messagebox.askyesno(
            "Подтверждение удаления",
            f"Вы уверены, что хотите удалить клиента '{client.name}' (ID: {client.id})?"
        )

        if confirm:
            if client.delete():
                messagebox.showinfo("Успех", f"Клиент '{client.name}' удален!")
                self.selected_client_id = None
                self._clear_edit_form()
                self.selected_client_info.configure(text="Выберите клиента из списка")

                # Обновляем список клиентов
                self._refresh_clients_list()
            else:
                messagebox.showerror("Ошибка", "Не удалось удалить клиента!")

    def _clear_edit_form(self):
        """Очищает форму редактирования"""
        for widget, field in self.edit_form_fields.values():
            if isinstance(widget, ctk.CTkTextbox):
                widget.delete("1.0", "end")
            elif isinstance(widget, ctk.CTkComboBox):
                widget.set("")
            else:
                widget.delete(0, "end")
                widget.configure(border_color="#4A5568")

        self.selected_client_id = None
        self.selected_client_info.configure(text="Выберите клиента из списка")