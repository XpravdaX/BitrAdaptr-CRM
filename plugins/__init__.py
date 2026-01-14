"""
Система плагинов
"""
import importlib.util
import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging
from tkinter import messagebox

PLUGINS_DIR = Path(__file__).parent
ENABLED_PLUGINS_FILE = PLUGINS_DIR / "enabled_plugins.json"


class PluginManager:
    """Менеджер плагинов"""
    
    def __init__(self):
        self.plugins = {}
        self.enabled_plugins = self._load_enabled_plugins()
        self.loaded_plugins = {}
        
    def _load_enabled_plugins(self) -> Dict[str, bool]:
        """Загружает список включенных плагинов"""
        if ENABLED_PLUGINS_FILE.exists():
            try:
                with open(ENABLED_PLUGINS_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def _save_enabled_plugins(self):
        """Сохраняет список включенных плагинов"""
        try:
            with open(ENABLED_PLUGINS_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.enabled_plugins, f, indent=4, ensure_ascii=False)
        except Exception as e:
            logging.error(f"Ошибка сохранения плагинов: {e}")
    
    def discover_plugins(self):
        """Обнаруживает все доступные плагины"""
        self.plugins = {}
        
        for item in PLUGINS_DIR.iterdir():
            if item.is_dir() and not item.name.startswith('__') and not item.name.startswith('.'):
                plugin_info_file = item / "plugin.json"
                plugin_file = item / "plugin.py"
                
                if plugin_info_file.exists() and plugin_file.exists():
                    try:
                        with open(plugin_info_file, 'r', encoding='utf-8') as f:
                            plugin_info = json.load(f)
                            plugin_info['path'] = str(item)
                            plugin_info['module_path'] = str(plugin_file)
                            self.plugins[plugin_info['id']] = plugin_info
                    except Exception as e:
                        logging.error(f"Ошибка загрузки плагина {item.name}: {e}")
    
    def get_plugin_info(self, plugin_id: str) -> Optional[Dict[str, Any]]:
        """Получает информацию о плагине"""
        return self.plugins.get(plugin_id)
    
    def _load_plugin_module(self, plugin_id: str):
        """Динамически загружает модуль плагина"""
        if plugin_id not in self.plugins:
            return None
        
        plugin_info = self.plugins[plugin_id]
        plugin_path = plugin_info['module_path']
        
        try:
            # Динамически загружаем модуль
            spec = importlib.util.spec_from_file_location(
                f"plugins.{plugin_id}.plugin",
                plugin_path
            )
            
            if spec is None or spec.loader is None:
                raise ImportError(f"Не удалось создать спецификацию для {plugin_id}")
            
            module = importlib.util.module_from_spec(spec)
            
            # Добавляем модуль в sys.modules для возможности повторного импорта
            sys.modules[f"plugins.{plugin_id}.plugin"] = module
            
            # Выполняем загрузку
            spec.loader.exec_module(module)
            
            return module
            
        except Exception as e:
            logging.error(f"Ошибка загрузки модуля плагина {plugin_id}: {e}")
            return None
    
    def enable_plugin(self, plugin_id: str) -> bool:
        """Включает плагин"""
        if plugin_id not in self.plugins:
            return False
        
        try:
            # Загружаем модуль плагина
            plugin_module = self._load_plugin_module(plugin_id)
            
            if plugin_module is None:
                raise ImportError(f"Не удалось загрузить модуль плагина {plugin_id}")
            
            # Получаем класс Plugin из модуля
            if not hasattr(plugin_module, 'Plugin'):
                raise AttributeError(f"Модуль {plugin_id} не содержит класса Plugin")
            
            # Инициализируем плагин
            plugin_instance = plugin_module.Plugin()
            
            # Сохраняем экземпляр
            self.loaded_plugins[plugin_id] = plugin_instance
            self.enabled_plugins[plugin_id] = True
            
            # Инициализируем БД плагина
            plugin_instance.initialize_database()
            
            # Сохраняем состояние
            self._save_enabled_plugins()
            
            return True
            
        except Exception as e:
            logging.error(f"Ошибка включения плагина {plugin_id}: {e}")
            messagebox.showerror("Ошибка", f"Не удалось включить плагин {plugin_id}:\n{str(e)}")
            return False
    
    def disable_plugin(self, plugin_id: str) -> bool:
        """Выключает плагин"""
        if plugin_id in self.loaded_plugins:
            # Уничтожаем экземпляр плагина
            del self.loaded_plugins[plugin_id]
        
        self.enabled_plugins[plugin_id] = False
        self._save_enabled_plugins()
        return True
    
    def is_plugin_enabled(self, plugin_id: str) -> bool:
        """Проверяет, включен ли плагин"""
        return self.enabled_plugins.get(plugin_id, False)
    
    def get_enabled_plugins(self) -> List[Dict[str, Any]]:
        """Получает список включенных плагинов"""
        enabled = []
        for plugin_id, plugin_info in self.plugins.items():
            if self.is_plugin_enabled(plugin_id):
                plugin_info_copy = plugin_info.copy()
                plugin_info_copy['instance'] = self.loaded_plugins.get(plugin_id)
                enabled.append(plugin_info_copy)
        return enabled
    
    def get_plugin_module(self, plugin_id: str):
        """Получает модуль плагина"""
        return self.loaded_plugins.get(plugin_id)
    
    def reload_plugin(self, plugin_id: str) -> bool:
        """Перезагружает плагин"""
        if self.disable_plugin(plugin_id):
            return self.enable_plugin(plugin_id)
        return False


# Глобальный экземпляр менеджера плагинов
plugin_manager = PluginManager()