"""
Управление зависимостями между полями
"""
from typing import Dict, Any, List, Callable
import customtkinter as ctk
from tkinter import messagebox


class FieldDependencyManager:
    """Менеджер зависимостей между полями"""
    
    def __init__(self):
        self.dependencies = {}
        self.field_validators = {}
        self.field_formatters = {}
        
    def add_dependency(self, trigger_field: str, trigger_value: Any,
                      dependent_field: str, action: str, 
                      condition: Callable = None, message: str = None):
        """
        Добавляет зависимость между полями
        
        Args:
            trigger_field: Поле, которое запускает зависимость
            trigger_value: Значение, которое активирует зависимость
            dependent_field: Зависимое поле
            action: Действие ('required', 'hidden', 'disabled', 'visible')
            condition: Дополнительное условие (функция)
            message: Сообщение для пользователя
        """
        if trigger_field not in self.dependencies:
            self.dependencies[trigger_field] = []
        
        self.dependencies[trigger_field].append({
            'trigger_value': trigger_value,
            'dependent_field': dependent_field,
            'action': action,
            'condition': condition,
            'message': message
        })
    
    def add_field_validator(self, field_name: str, validator: Callable, 
                           error_message: str = None):
        """Добавляет валидатор для поля"""
        self.field_validators[field_name] = {
            'validator': validator,
            'error_message': error_message
        }
    
    def add_field_formatter(self, field_name: str, formatter: Callable):
        """Добавляет форматтер для поля"""
        self.field_formatters[field_name] = formatter
    
    def validate_field(self, field_name: str, value: Any) -> tuple:
        """Валидирует поле"""
        if field_name in self.field_validators:
            validator_info = self.field_validators[field_name]
            if not validator_info['validator'](value):
                return False, validator_info['error_message']
        return True, ""
    
    def format_field(self, field_name: str, value: Any) -> Any:
        """Форматирует значение поля"""
        if field_name in self.field_formatters:
            return self.field_formatters[field_name](value)
        return value
    
    def check_dependencies(self, field_name: str, value: Any, 
                          field_widgets: Dict) -> List[str]:
        """
        Проверяет зависимости для поля
        
        Returns:
            Список сообщений об ошибках
        """
        errors = []
        
        if field_name in self.dependencies:
            for dependency in self.dependencies[field_name]:
                # Проверяем условие
                condition_met = False
                if dependency['condition']:
                    condition_met = dependency['condition'](value)
                else:
                    condition_met = (value == dependency['trigger_value'])
                
                if condition_met:
                    dependent_field = dependency['dependent_field']
                    action = dependency['action']
                    
                    if dependent_field in field_widgets:
                        self._apply_dependency_action(
                            dependent_field, action, 
                            field_widgets[dependent_field]
                        )
                        
                        if dependency['message']:
                            errors.append(dependency['message'])
        
        return errors
    
    def _apply_dependency_action(self, field_name: str, action: str, 
                                widget_info: Dict):
        """Применяет действие зависимости к виджету"""
        widget = widget_info.get('widget')
        
        if not widget:
            return
        
        if action == 'required':
            # Обновляем метку
            label = widget_info.get('label')
            if label and isinstance(label, ctk.CTkLabel):
                current_text = label.cget('text')
                if ' *' not in current_text:
                    label.configure(text=current_text + ' *')
            
            # Делаем поле обязательным
            widget.configure(border_color="#FF9800")  # Оранжевый цвет для обязательных полей
            
        elif action == 'disabled':
            widget.configure(state="disabled")
            
        elif action == 'enabled':
            widget.configure(state="normal")
            
        elif action == 'hidden':
            if 'frame' in widget_info:
                widget_info['frame'].grid_remove()
            else:
                widget.grid_remove()
                
        elif action == 'visible':
            if 'frame' in widget_info:
                widget_info['frame'].grid()
            else:
                widget.grid()


# Глобальный экземпляр менеджера зависимостей
dependency_manager = FieldDependencyManager()


# Пример использования зависимостей для модуля клиентов
def setup_client_dependencies():
    """Настраивает зависимости для модуля клиентов"""
    
    # Если статус "потенциальный", компания становится обязательной
    dependency_manager.add_dependency(
        trigger_field='status',
        trigger_value='потенциальный',
        dependent_field='company',
        action='required',
        message='Для потенциальных клиентов обязательно указание компании'
    )
    
    # Если компания указана, имя должно быть заполнено
    dependency_manager.add_dependency(
        trigger_field='company',
        trigger_value=lambda x: bool(x and len(x) >= 2),
        dependent_field='name',
        action='required',
        message='При указании компании обязательно заполните имя'
    )
    
    # Если email указан, он должен быть валидным
    dependency_manager.add_field_validator(
        field_name='email',
        validator=lambda x: not x or ('@' in x and '.' in x),
        error_message='Неверный формат email'
    )
    
    # Форматирование телефона
    dependency_manager.add_field_formatter(
        field_name='phone',
        formatter=lambda x: _format_phone(x) if x else x
    )


def _format_phone(phone: str) -> str:
    """Форматирует телефон"""
    import re
    digits = re.sub(r'\D', '', phone)
    
    if len(digits) == 11 and digits.startswith('7'):
        return f"+7 ({digits[1:4]}) {digits[4:7]}-{digits[7:9]}-{digits[9:]}"
    elif len(digits) == 10:
        return f"+7 ({digits[0:3]}) {digits[3:6]}-{digits[6:8]}-{digits[8:]}"
    return phone