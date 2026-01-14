"""
Модуль отчетов
"""
import customtkinter as ctk
from tkinter import messagebox, filedialog
from typing import Dict, Any, List
from datetime import datetime, timedelta
import pandas as pd
from pathlib import Path
import os

from modules.base_module import BaseModule
from ui.styles import Styles
from modules.clients import Client


class ReportsModule(BaseModule):
    """Модуль отчетов"""

    MODULE_NAME = "Отчеты"
    MODULE_VERSION = "1.0"

    def __init__(self):
        super().__init__()

    def get_ui_component(self, parent) -> ctk.CTkFrame:
        """Создает интерфейс для модуля отчетов"""
        frame = ctk.CTkFrame(parent)
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Заголовок
        title = ctk.CTkLabel(
            frame,
            text="Генерация отчетов",
            font=("Arial", 24, "bold"),
            text_color=Styles.PRIMARY_COLOR
        )
        title.pack(pady=(0, 20))

        # Scrollable area
        scrollable_frame = ctk.CTkScrollableFrame(frame)
        scrollable_frame.pack(fill="both", expand=True)

        # Типы отчетов
        ctk.CTkLabel(scrollable_frame, text="Тип отчета:", 
                     font=("Arial", 16, "bold")).pack(anchor="w", pady=(10, 5))
        
        self.report_type_var = ctk.StringVar(value="clients_summary")
        report_types_frame = ctk.CTkFrame(scrollable_frame)
        report_types_frame.pack(fill="x", pady=5)
        
        report_types = [
            ("clients_summary", "Общий отчет по клиентам"),
            ("clients_by_status", "Клиенты по статусам"),
            ("clients_by_date", "Клиенты по дате добавления"),
            ("detailed_clients", "Подробный отчет по клиентам")
        ]
        
        for value, text in report_types:
            radio = ctk.CTkRadioButton(
                report_types_frame,
                text=text,
                variable=self.report_type_var,
                value=value,
                font=("Arial", 12)
            )
            radio.pack(anchor="w", padx=10, pady=5)

        # Период отчета
        ctk.CTkLabel(scrollable_frame, text="Период отчета:", 
                     font=("Arial", 16, "bold")).pack(anchor="w", pady=(20, 5))
        
        period_frame = ctk.CTkFrame(scrollable_frame)
        period_frame.pack(fill="x", pady=5)
        
        self.period_var = ctk.StringVar(value="all")
        periods = [
            ("all", "За все время"),
            ("today", "За сегодня"),
            ("week", "За неделю"),
            ("month", "За месяц"),
            ("quarter", "За квартал"),
            ("year", "За год"),
            ("custom", "Произвольный период")
        ]
        
        for i, (value, text) in enumerate(periods):
            if i < 4:
                radio = ctk.CTkRadioButton(
                    period_frame,
                    text=text,
                    variable=self.period_var,
                    value=value,
                    font=("Arial", 12)
                )
                radio.grid(row=0, column=i, padx=10, pady=5, sticky="w")
                period_frame.grid_columnconfigure(i, weight=1)
            else:
                radio = ctk.CTkRadioButton(
                    period_frame,
                    text=text,
                    variable=self.period_var,
                    value=value,
                    font=("Arial", 12)
                )
                radio.grid(row=1, column=i-4, padx=10, pady=5, sticky="w")
                period_frame.grid_columnconfigure(i-4, weight=1)

        # Произвольный период (скрыт по умолчанию)
        self.custom_period_frame = ctk.CTkFrame(scrollable_frame)
        
        ctk.CTkLabel(self.custom_period_frame, text="С:", font=("Arial", 12)).grid(row=0, column=0, padx=5, pady=5)
        self.start_date_entry = ctk.CTkEntry(self.custom_period_frame, width=120, placeholder_text="ГГГГ-ММ-ДД")
        self.start_date_entry.grid(row=0, column=1, padx=5, pady=5)
        
        ctk.CTkLabel(self.custom_period_frame, text="По:", font=("Arial", 12)).grid(row=0, column=2, padx=5, pady=5)
        self.end_date_entry = ctk.CTkEntry(self.custom_period_frame, width=120, placeholder_text="ГГГГ-ММ-ДД")
        self.end_date_entry.grid(row=0, column=3, padx=5, pady=5)
        
        # Связываем изменение выбора периода
        self.period_var.trace("w", self._on_period_change)

        # Форматы экспорта
        ctk.CTkLabel(scrollable_frame, text="Формат экспорта:", 
                     font=("Arial", 16, "bold")).pack(anchor="w", pady=(20, 5))
        
        self.format_var = ctk.StringVar(value="excel")
        format_frame = ctk.CTkFrame(scrollable_frame)
        format_frame.pack(fill="x", pady=5)
        
        formats = [
            ("excel", "Excel (.xlsx)"),
            ("csv", "CSV (.csv)"),
            ("json", "JSON (.json)")
        ]
        
        for value, text in formats:
            radio = ctk.CTkRadioButton(
                format_frame,
                text=text,
                variable=self.format_var,
                value=value,
                font=("Arial", 12)
            )
            radio.pack(side="left", padx=10, pady=5)

        # Дополнительные параметры
        ctk.CTkLabel(scrollable_frame, text="Дополнительные параметры:", 
                     font=("Arial", 16, "bold")).pack(anchor="w", pady=(20, 5))
        
        options_frame = ctk.CTkFrame(scrollable_frame)
        options_frame.pack(fill="x", pady=5)
        
        self.include_notes_var = ctk.BooleanVar(value=True)
        include_notes_check = ctk.CTkCheckBox(
            options_frame,
            text="Включать заметки",
            variable=self.include_notes_var,
            font=("Arial", 12)
        )
        include_notes_check.pack(anchor="w", padx=10, pady=5)
        
        self.group_by_status_var = ctk.BooleanVar(value=True)
        group_by_status_check = ctk.CTkCheckBox(
            options_frame,
            text="Группировать по статусу",
            variable=self.group_by_status_var,
            font=("Arial", 12)
        )
        group_by_status_check.pack(anchor="w", padx=10, pady=5)

        # Кнопки
        button_frame = ctk.CTkFrame(scrollable_frame)
        button_frame.pack(fill="x", pady=30)

        preview_btn = ctk.CTkButton(
            button_frame,
            text="Предварительный просмотр",
            command=self._preview_report,
            width=200,
            height=45,
            fg_color=Styles.SECONDARY_COLOR,
            hover_color="#8A2C5C",
            font=("Arial", 14)
        )
        preview_btn.pack(side="left", padx=10)

        generate_btn = ctk.CTkButton(
            button_frame,
            text="Сгенерировать отчет",
            command=self._generate_report,
            width=200,
            height=45,
            fg_color=Styles.PRIMARY_COLOR,
            hover_color=Styles.HOVER_COLOR,
            font=("Arial", 14, "bold")
        )
        generate_btn.pack(side="left", padx=10)

        # Область предварительного просмотра
        ctk.CTkLabel(scrollable_frame, text="Предварительный просмотр:", 
                     font=("Arial", 16, "bold")).pack(anchor="w", pady=(20, 5))
        
        self.preview_text = ctk.CTkTextbox(scrollable_frame, height=200)
        self.preview_text.pack(fill="x", pady=5)

        return frame

    def _on_period_change(self, *args):
        """Обработчик изменения периода"""
        if self.period_var.get() == "custom":
            self.custom_period_frame.pack(fill="x", pady=10)
            
            # Устанавливаем даты по умолчанию
            today = datetime.now().strftime("%Y-%m-%d")
            week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
            
            self.start_date_entry.delete(0, "end")
            self.start_date_entry.insert(0, week_ago)
            
            self.end_date_entry.delete(0, "end")
            self.end_date_entry.insert(0, today)
        else:
            self.custom_period_frame.pack_forget()

    def _get_date_range(self):
        """Получает диапазон дат на основе выбранного периода"""
        period = self.period_var.get()
        
        if period == "all":
            return None, None
        
        now = datetime.now()
        
        if period == "today":
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = now
        elif period == "week":
            start_date = now - timedelta(days=7)
            end_date = now
        elif period == "month":
            start_date = now - timedelta(days=30)
            end_date = now
        elif period == "quarter":
            start_date = now - timedelta(days=90)
            end_date = now
        elif period == "year":
            start_date = now - timedelta(days=365)
            end_date = now
        elif period == "custom":
            try:
                start_date = datetime.strptime(self.start_date_entry.get(), "%Y-%m-%d")
                end_date = datetime.strptime(self.end_date_entry.get(), "%Y-%m-%d")
                end_date = end_date.replace(hour=23, minute=59, second=59)
            except ValueError:
                messagebox.showerror("Ошибка", "Неверный формат даты! Используйте ГГГГ-ММ-ДД")
                return None, None
        
        return start_date, end_date

    def _get_clients_data(self, start_date=None, end_date=None):
        """Получает данные клиентов для отчета"""
        clients = Client.get_all()
        
        if start_date and end_date:
            filtered_clients = []
            for client in clients:
                try:
                    client_date = datetime.fromisoformat(client.created_at.replace('Z', '+00:00'))
                    if start_date <= client_date <= end_date:
                        filtered_clients.append(client)
                except:
                    filtered_clients.append(client)
            clients = filtered_clients
        
        return clients

    def _prepare_data_for_report(self, clients):
        """Подготавливает данные для отчета"""
        data = []
        
        for client in clients:
            client_data = {
                "ID": client.id,
                "Имя": client.name,
                "Email": client.email,
                "Телефон": client.phone,
                "Компания": client.company,
                "Статус": client.status,
                "Дата создания": client.created_at,
                "Дата обновления": client.updated_at
            }
            
            if self.include_notes_var.get():
                client_data["Заметки"] = client.notes[:100] + "..." if len(client.notes) > 100 else client.notes
            
            data.append(client_data)
        
        return data

    def _generate_summary_statistics(self, clients):
        """Генерирует сводную статистику"""
        if not clients:
            return {"total": 0, "by_status": {}, "by_company": {}}
        
        stats = {
            "total": len(clients),
            "by_status": {},
            "by_company": {}
        }
        
        # Статистика по статусам
        for client in clients:
            status = client.status if client.status else "не указан"
            stats["by_status"][status] = stats["by_status"].get(status, 0) + 1
        
        # Статистика по компаниям
        for client in clients:
            company = client.company if client.company else "не указана"
            stats["by_company"][company] = stats["by_company"].get(company, 0) + 1
        
        return stats

    def _preview_report(self):
        """Предварительный просмотр отчета"""
        start_date, end_date = self._get_date_range()
        
        if start_date is None and self.period_var.get() == "custom":
            return
        
        clients = self._get_clients_data(start_date, end_date)
        
        if not clients:
            self.preview_text.delete("1.0", "end")
            self.preview_text.insert("1.0", "Нет данных для отчета.")
            return
        
        stats = self._generate_summary_statistics(clients)
        
        preview_text = f"""
=== ОТЧЕТ ПО КЛИЕНТАМ ===
Дата генерации: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Период: {self._get_period_text()}
Тип отчета: {self._get_report_type_text()}

СВОДНАЯ СТАТИСТИКА:
Всего клиентов: {stats['total']}

РАСПРЕДЕЛЕНИЕ ПО СТАТУСАМ:
"""
        for status, count in stats['by_status'].items():
            percentage = (count / stats['total']) * 100 if stats['total'] > 0 else 0
            preview_text += f"  {status}: {count} ({percentage:.1f}%)\n"
        
        preview_text += "\nРАСПРЕДЕЛЕНИЕ ПО КОМПАНИЯМ (топ 5):\n"
        sorted_companies = sorted(stats['by_company'].items(), key=lambda x: x[1], reverse=True)[:5]
        for company, count in sorted_companies:
            percentage = (count / stats['total']) * 100 if stats['total'] > 0 else 0
            preview_text += f"  {company}: {count} ({percentage:.1f}%)\n"
        
        preview_text += f"\nПЕРВЫЕ 10 ЗАПИСЕЙ:\n"
        preview_text += "ID | Имя | Компания | Статус | Дата создания\n"
        preview_text += "-" * 70 + "\n"
        
        for i, client in enumerate(clients[:10]):
            preview_text += f"{client.id} | {client.name} | {client.company} | {client.status} | {client.created_at[:10]}\n"
        
        if len(clients) > 10:
            preview_text += f"\n... и еще {len(clients) - 10} записей\n"
        
        self.preview_text.delete("1.0", "end")
        self.preview_text.insert("1.0", preview_text)

    def _get_period_text(self):
        """Получает текстовое описание периода"""
        period = self.period_var.get()
        period_texts = {
            "all": "За все время",
            "today": "За сегодня",
            "week": "За неделю",
            "month": "За месяц",
            "quarter": "За квартал",
            "year": "За год",
            "custom": f"С {self.start_date_entry.get()} по {self.end_date_entry.get()}"
        }
        return period_texts.get(period, "Неизвестный период")

    def _get_report_type_text(self):
        """Получает текстовое описание типа отчета"""
        report_type = self.report_type_var.get()
        type_texts = {
            "clients_summary": "Общий отчет по клиентам",
            "clients_by_status": "Клиенты по статусам",
            "clients_by_date": "Клиенты по дате добавления",
            "detailed_clients": "Подробный отчет по клиентам"
        }
        return type_texts.get(report_type, "Неизвестный тип отчета")

    def _generate_report(self):
        """Генерирует и сохраняет отчет"""
        start_date, end_date = self._get_date_range()
        
        if start_date is None and self.period_var.get() == "custom":
            return
        
        clients = self._get_clients_data(start_date, end_date)
        
        if not clients:
            messagebox.showwarning("Нет данных", "Нет данных для генерации отчета.")
            return
        
        # Подготавливаем данные
        data = self._prepare_data_for_report(clients)
        df = pd.DataFrame(data)
        
        # Выбираем место для сохранения
        file_ext = self._get_file_extension()
        default_name = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}{file_ext}"
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=file_ext,
            filetypes=self._get_file_types(),
            initialfile=default_name
        )
        
        if not file_path:
            return  # Пользователь отменил
        
        try:
            # Сохраняем в выбранном формате
            file_format = self.format_var.get()
            
            if file_format == "excel":
                self._save_to_excel(df, file_path, clients)
            elif file_format == "csv":
                df.to_csv(file_path, index=False, encoding='utf-8-sig')
            elif file_format == "json":
                df.to_json(file_path, orient='records', force_ascii=False, indent=2)
            
            messagebox.showinfo("Успех", f"Отчет успешно сохранен:\n{file_path}")
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить отчет: {str(e)}")

    def _save_to_excel(self, df, file_path, clients):
        """Сохраняет отчет в Excel с несколькими листами"""
        with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
            # Основные данные
            df.to_excel(writer, sheet_name='Клиенты', index=False)
            
            # Сводная статистика
            stats = self._generate_summary_statistics(clients)
            
            # Лист со статистикой
            stats_data = []
            stats_data.append(["ОБЩАЯ СТАТИСТИКА"])
            stats_data.append([f"Всего клиентов: {stats['total']}"])
            stats_data.append([f"Период: {self._get_period_text()}"])
            stats_data.append([f"Дата генерации: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"])
            stats_data.append([])
            
            stats_data.append(["РАСПРЕДЕЛЕНИЕ ПО СТАТУСАМ"])
            stats_data.append(["Статус", "Количество", "Процент"])
            for status, count in stats['by_status'].items():
                percentage = (count / stats['total']) * 100 if stats['total'] > 0 else 0
                stats_data.append([status, count, f"{percentage:.1f}%"])
            
            stats_data.append([])
            stats_data.append(["РАСПРЕДЕЛЕНИЕ ПО КОМПАНИЯМ (топ 10)"])
            stats_data.append(["Компания", "Количество", "Процент"])
            sorted_companies = sorted(stats['by_company'].items(), key=lambda x: x[1], reverse=True)[:10]
            for company, count in sorted_companies:
                percentage = (count / stats['total']) * 100 if stats['total'] > 0 else 0
                stats_data.append([company, count, f"{percentage:.1f}%"])
            
            stats_df = pd.DataFrame(stats_data)
            stats_df.to_excel(writer, sheet_name='Статистика', index=False, header=False)
            
            # Лист с диаграммой (заглушка - можно добавить реальные диаграммы позже)
            summary_data = [["Сводная информация по отчету"]]
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='Сводка', index=False, header=False)
            
            # Автонастройка ширины колонок
            for sheet_name in writer.sheets:
                worksheet = writer.sheets[sheet_name]
                for column in worksheet.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    adjusted_width = min(max_length + 2, 50)
                    worksheet.column_dimensions[column_letter].width = adjusted_width

    def _get_file_extension(self):
        """Получает расширение файла на основе формата"""
        formats = {
            "excel": ".xlsx",
            "csv": ".csv",
            "json": ".json"
        }
        return formats.get(self.format_var.get(), ".xlsx")

    def _get_file_types(self):
        """Получает типы файлов для диалога сохранения"""
        formats = {
            "excel": [("Excel files", "*.xlsx"), ("All files", "*.*")],
            "csv": [("CSV files", "*.csv"), ("All files", "*.*")],
            "json": [("JSON files", "*.json"), ("All files", "*.*")]
        }
        return formats.get(self.format_var.get(), [("All files", "*.*")])

    def initialize_database(self):
        """Инициализирует таблицы БД для модуля"""
        # Для модуля отчетов не нужна таблица в БД
        pass