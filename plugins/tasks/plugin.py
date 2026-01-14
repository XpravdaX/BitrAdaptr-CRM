"""
Плагин менеджера задач
"""
import customtkinter as ctk
from tkinter import messagebox
from typing import Dict, Any
from datetime import datetime

from plugins.base_plugin import BasePlugin
from core.database import db_manager
from ui.styles import Styles


class TaskModel:
    """Модель задачи"""
    
    TABLE_NAME = "tasks"
    
    def __init__(self, **kwargs):
        self.id = kwargs.get('id')
        self.title = kwargs.get('title', '')
        self.description = kwargs.get('description', '')
        self.priority = kwargs.get('priority', 'medium')
        self.status = kwargs.get('status', 'pending')
        self.created_at = kwargs.get('created_at', datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        data = {
            'title': self.title,
            'description': self.description,
            'priority': self.priority,
            'status': self.status,
            'created_at': self.created_at
        }
        if self.id:
            data['id'] = self.id
        return data
    
    def save(self) -> int:
        """Сохраняет задачу в БД"""
        data = self.to_dict()
        
        if self.id:
            # Обновление
            db_manager.update(self.TABLE_NAME, data, "id = ?", (self.id,))
            return self.id
        else:
            # Создание
            self.id = db_manager.insert(self.TABLE_NAME, data)
            return self.id
    
    @classmethod
    def get_all(cls):
        """Получает все задачи"""
        results = db_manager.select(cls.TABLE_NAME)
        return [cls(**dict(row)) for row in results]
    
    @classmethod
    def get(cls, task_id: int):
        """Получает задачу по ID"""
        result = db_manager.select(cls.TABLE_NAME, where="id = ?", params=(task_id,))
        if result:
            return cls(**dict(result[0]))
        return None
    
    def delete(self) -> bool:
        """Удаляет задачу"""
        if self.id:
            return db_manager.delete(self.TABLE_NAME, "id = ?", (self.id,))
        return False


class Plugin(BasePlugin):
    """Плагин менеджера задач"""
    
    def __init__(self):
        super().__init__()
        self.plugin_info = {
            'name': 'Задачи',
            'icon': '✅'
        }
    
    def get_ui_component(self, parent) -> ctk.CTkFrame:
        """Создает интерфейс для управления задачами"""
        main_frame = ctk.CTkFrame(parent)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Заголовок
        title = ctk.CTkLabel(
            main_frame,
            text="Управление задачами",
            font=("Arial", 20, "bold"),
            text_color=Styles.PRIMARY_COLOR
        )
        title.pack(pady=10)
        
        # Простой интерфейс
        self._create_simple_interface(main_frame)
        
        return main_frame
    
    def _create_simple_interface(self, parent):
        """Создает простой интерфейс для задач"""
        # Форма добавления
        form_frame = ctk.CTkFrame(parent)
        form_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(form_frame, text="Новая задача:").pack(anchor="w")
        
        self.task_entry = ctk.CTkEntry(form_frame, placeholder_text="Введите задачу...")
        self.task_entry.pack(fill="x", pady=5)
        
        add_btn = ctk.CTkButton(
            form_frame,
            text="Добавить задачу",
            command=self._add_task,
            fg_color=Styles.SUCCESS_COLOR
        )
        add_btn.pack(pady=5)
        
        # Список задач
        list_frame = ctk.CTkFrame(parent)
        list_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        ctk.CTkLabel(list_frame, text="Список задач:").pack(anchor="w")
        
        self.tasks_listbox = ctk.CTkScrollableFrame(list_frame, height=200)
        self.tasks_listbox.pack(fill="both", expand=True, pady=5)
        
        refresh_btn = ctk.CTkButton(
            list_frame,
            text="Обновить список",
            command=self._refresh_tasks
        )
        refresh_btn.pack(pady=5)
        
        # Загружаем задачи
        self._refresh_tasks()
    
    def _add_task(self):
        """Добавляет новую задачу"""
        title = self.task_entry.get().strip()
        
        if not title:
            messagebox.showwarning("Ошибка", "Введите текст задачи!")
            return
        
        task = TaskModel(
            title=title,
            description="",
            priority="medium",
            status="pending"
        )
        
        task.save()
        
        self.task_entry.delete(0, "end")
        self._refresh_tasks()
        messagebox.showinfo("Успех", "Задача добавлена!")
    
    def _refresh_tasks(self):
        """Обновляет список задач"""
        # Очищаем список
        for widget in self.tasks_listbox.winfo_children():
            widget.destroy()
        
        tasks = TaskModel.get_all()
        
        if not tasks:
            label = ctk.CTkLabel(
                self.tasks_listbox,
                text="Задач нет",
                text_color="gray"
            )
            label.pack(pady=10)
            return
        
        for task in tasks:
            task_frame = ctk.CTkFrame(self.tasks_listbox)
            task_frame.pack(fill="x", pady=2)
            
            # Текст задачи
            task_text = f"{task.id}. {task.title}"
            if task.status == 'completed':
                task_text = f"✅ {task_text}"
            elif task.status == 'in_progress':
                task_text = f"⚡ {task_text}"
            else:
                task_text = f"⏳ {task_text}"
            
            label = ctk.CTkLabel(
                task_frame,
                text=task_text,
                anchor="w"
            )
            label.pack(side="left", fill="x", expand=True, padx=5)
            
            # Кнопка удаления
            delete_btn = ctk.CTkButton(
                task_frame,
                text="🗑️",
                width=30,
                height=30,
                command=lambda t_id=task.id: self._delete_task(t_id),
                fg_color=Styles.ERROR_COLOR
            )
            delete_btn.pack(side="right", padx=5)
            
            # Кнопка завершения
            if task.status != 'completed':
                complete_btn = ctk.CTkButton(
                    task_frame,
                    text="✓",
                    width=30,
                    height=30,
                    command=lambda t_id=task.id: self._complete_task(t_id),
                    fg_color=Styles.SUCCESS_COLOR
                )
                complete_btn.pack(side="right", padx=2)
    
    def _delete_task(self, task_id):
        """Удаляет задачу"""
        task = TaskModel.get(task_id)
        if task and task.delete():
            self._refresh_tasks()
    
    def _complete_task(self, task_id):
        """Отмечает задачу как выполненную"""
        task = TaskModel.get(task_id)
        if task:
            task.status = 'completed'
            task.save()
            self._refresh_tasks()
    
    def initialize_database(self):
        """Инициализирует таблицу задач"""
        schema = {
            'id': 'INTEGER PRIMARY KEY AUTOINCREMENT',
            'title': 'TEXT NOT NULL',
            'description': 'TEXT',
            'priority': 'TEXT',
            'status': 'TEXT',
            'created_at': 'TEXT'
        }
        db_manager.create_table(TaskModel.TABLE_NAME, schema)
    
    def get_module_name(self) -> str:
        return "Задачи"
    
    def get_sidebar_icon(self) -> str:
        return "✅"