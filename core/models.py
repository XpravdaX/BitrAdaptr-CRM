"""
Базовые модели данных
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime
from .database import db_manager


class BaseModel(ABC):
    """Абстрактная базовая модель"""

    TABLE_NAME = ""

    def __init__(self, **kwargs):
        self.id = kwargs.get('id')
        self.created_at = kwargs.get('created_at', datetime.now().isoformat())
        self.updated_at = kwargs.get('updated_at', datetime.now().isoformat())

    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """Преобразует объект в словарь"""
        pass

    @classmethod
    @abstractmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BaseModel':
        """Создает объект из словаря"""
        pass

    def save(self) -> int:
        """Сохраняет объект в БД"""
        data = self.to_dict()
        data['updated_at'] = datetime.now().isoformat()

        if self.id:
            # Обновление существующей записи
            db_manager.update(self.TABLE_NAME, data, "id = ?", (self.id,))
            return self.id
        else:
            # Вставка новой записи
            data['created_at'] = datetime.now().isoformat()
            self.id = db_manager.insert(self.TABLE_NAME, data)
            return self.id

    @classmethod
    def get(cls, obj_id: int) -> Optional['BaseModel']:
        """Получает объект по ID"""
        result = db_manager.select(cls.TABLE_NAME, where="id = ?", params=(obj_id,))
        if result:
            return cls.from_dict(result[0])
        return None

    @classmethod
    def get_all(cls, where: str = None, params: tuple = None) -> List['BaseModel']:
        """Получает все объекты"""
        results = db_manager.select(cls.TABLE_NAME, where=where, params=params)
        return [cls.from_dict(row) for row in results]

    def delete(self) -> bool:
        """Удаляет объект из БД"""
        if self.id:
            return db_manager.delete(self.TABLE_NAME, "id = ?", (self.id,))
        return False


class CustomField:
    """Класс для пользовательских полей"""

    def __init__(self, name: str, field_type: str, label: str,
                 required: bool = False, options: List[str] = None):
        self.name = name
        self.type = field_type  # text, number, date, select, email, phone
        self.label = label
        self.required = required
        self.options = options or []

    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'type': self.type,
            'label': self.label,
            'required': self.required,
            'options': self.options
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CustomField':
        return cls(
            name=data['name'],
            field_type=data['type'],
            label=data['label'],
            required=data.get('required', False),
            options=data.get('options', [])
        )