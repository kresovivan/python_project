import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from typing import List, Dict


class ProgrammingDictionaryApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Словарь программирования")
        self.root.geometry("400x700")
        self.root.configure(bg="#f0f0f0")

        # Данные словаря
        self.terms = self.load_terms()
        self.current_filter = "Все"
        self.search_query = ""
        self.learned_terms = set()

        self.setup_ui()
        self.show_terms()

    def load_terms(self) -> List[Dict]:
        """Загрузка терминов из встроенных данных"""
        return [
            # Основные концепции
            {
                "term": "Algorithm",
                "definition": "Пошаговая процедура решения задачи",
                "translation": "Алгоритм",
                "category": "Основные концепции",
                "level": "High",
            },
            {
                "term": "Data Structure",
                "definition": "Способ организации и хранения данных",
                "translation": "Структура данных",
                "category": "Основные концепции",
                "level": "High",
            },
            {
                "term": "Variable",
                "definition": "Именованная область памяти для хранения данных",
                "translation": "Переменная",
                "category": "Основные концепции",
                "level": "High",
            },
            {
                "term": "Function",
                "definition": "Блок кода, выполняющий конкретную задачу",
                "translation": "Функция",
                "category": "Основные концепции",
                "level": "High",
            },
            {
                "term": "Class",
                "definition": "Шаблон для создания объектов в ООП",
                "translation": "Класс",
                "category": "Основные концепции",
                "level": "High",
            },
            # Базы данных
            {
                "term": "SQL",
                "definition": "Язык для работы с реляционными базами данных",
                "translation": "SQL",
                "category": "Базы данных",
                "level": "High",
            },
            {
                "term": "NoSQL",
                "definition": "Нереляционные базы данных",
                "translation": "NoSQL",
                "category": "Базы данных",
                "level": "Medium",
            },
            {
                "term": "Index",
                "definition": "Структура для ускорения поиска в БД",
                "translation": "Индекс",
                "category": "Базы данных",
                "level": "High",
            },
            # Веб-разработка
            {
                "term": "REST",
                "definition": "Архитектурный стиль для веб-сервисов",
                "translation": "REST",
                "category": "Веб-разработка",
                "level": "High",
            },
            {
                "term": "JSON",
                "definition": "Формат обмена данными",
                "translation": "JSON",
                "category": "Веб-разработка",
                "level": "High",
            },
            {
                "term": "API",
                "definition": "Интерфейс для взаимодействия между программами",
                "translation": "API",
                "category": "Веб-разработка",
                "level": "High",
            },
            # Добавьте больше терминов по необходимости
        ]

    def setup_ui(self):
        """Настройка пользовательского интерфейса"""
        # Заголовок
        title_label = tk.Label(
            self.root,
            text="📚 Словарь программирования",
            font=("Arial", 16, "bold"),
            bg="#f0f0f0",
            fg="#2c3e50",
        )
        title_label.pack(pady=10)

        # Панель управления
        control_frame = tk.Frame(self.root, bg="#f0f0f0")
        control_frame.pack(pady=5, fill="x", padx=10)

        # Фильтр по категориям
        categories = ["Все"] + list(set(term["category"] for term in self.terms))
        self.category_var = tk.StringVar(value="Все")

        category_label = tk.Label(control_frame, text="Категория:", bg="#f0f0f0")
        category_label.grid(row=0, column=0, sticky="w")

        self.category_combo = ttk.Combobox(
            control_frame,
            textvariable=self.category_var,
            values=categories,
            state="readonly",
            width=15,
        )
        self.category_combo.grid(row=0, column=1, padx=5)
        self.category_combo.bind("<<ComboboxSelected>>", self.on_category_change)

        # Поиск
        search_label = tk.Label(control_frame, text="Поиск:", bg="#f0f0f0")
        search_label.grid(row=1, column=0, sticky="w", pady=5)

        self.search_entry = tk.Entry(control_frame, width=20)
        self.search_entry.grid(row=1, column=1, padx=5, pady=5)
        self.search_entry.bind("<KeyRelease>", self.on_search)

        # Кнопка режима обучения
        button_frame = tk.Frame(self.root, bg="#f0f0f0")
        button_frame.pack(pady=10)

        self.learn_btn = tk.Button(
            button_frame,
            text="📖 Режим обучения",
            command=self.start_learning_mode,
            bg="#27ae60",
            fg="white",
            font=("Arial", 12),
            width=15,
            height=2,
        )
        self.learn_btn.pack()

        # Прогресс
        self.progress_label = tk.Label(
            self.root,
            text="Изучено: 0/0 (0%)",
            font=("Arial", 10),
            bg="#f0f0f0",
            fg="#27ae60",
        )
        self.progress_label.pack(pady=5)

        # Поле для терминов
        terms_frame = tk.Frame(self.root)
        terms_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Scrollable text area
        self.terms_text = scrolledtext.ScrolledText(
            terms_frame,
            wrap=tk.WORD,
            width=40,
            height=20,
            font=("Arial", 10),
            bg="white",
            fg="#2c3e50",
        )
        self.terms_text.pack(fill="both", expand=True)

        self.update_progress()

    def on_category_change(self, event):
        """Обработчик изменения категории"""
        self.current_filter = self.category_var.get()
        self.show_terms()

    def on_search(self, event):
        """Обработчик поиска"""
        self.search_query = self.search_entry.get().lower()
        self.show_terms()

    def show_terms(self):
        """Отображение отфильтрованных терминов"""
        self.terms_text.delete(1.0, tk.END)

        filtered_terms = self.get_filtered_terms()

        if not filtered_terms:
            self.terms_text.insert(tk.END, "Термины не найдены\n")
            return

        for term in filtered_terms:
            # Термин
            self.terms_text.insert(tk.END, f"🔹 {term['term']}\n", "term")

            # Перевод
            self.terms_text.insert(
                tk.END, f"   Перевод: {term['translation']}\n", "translation"
            )

            # Категория и уровень
            self.terms_text.insert(
                tk.END, f"   Категория: {term['category']}\n", "meta"
            )
            self.terms_text.insert(tk.END, f"   Уровень: {term['level']}\n", "meta")

            # Определение
            self.terms_text.insert(
                tk.END, f"   Определение: {term['definition']}\n\n", "definition"
            )

        # Настройка стилей текста
        self.terms_text.tag_configure(
            "term", foreground="#2c3e50", font=("Arial", 11, "bold")
        )
        self.terms_text.tag_configure(
            "translation", foreground="#2980b9", font=("Arial", 10)
        )
        self.terms_text.tag_configure("meta", foreground="#7f8c8d", font=("Arial", 9))
        self.terms_text.tag_configure(
            "definition", foreground="#2c3e50", font=("Arial", 10)
        )

    def get_filtered_terms(self) -> List[Dict]:
        """Фильтрация терминов по категории и поисковому запросу"""
        filtered = self.terms

        if self.current_filter != "Все":
            filtered = [
                term for term in filtered if term["category"] == self.current_filter
            ]

        if self.search_query:
            filtered = [
                term
                for term in filtered
                if (
                    self.search_query in term["term"].lower()
                    or self.search_query in term["translation"].lower()
                    or self.search_query in term["definition"].lower()
                )
            ]

        return filtered

    def start_learning_mode(self):
        """Запуск режима обучения"""
        filtered_terms = self.get_filtered_terms()
        if not filtered_terms:
            messagebox.showinfo("Информация", "Нет терминов для изучения")
            return

        LearningModeWindow(self.root, filtered_terms)

    def update_progress(self):
        """Обновление прогресса изучения"""
        total = len(self.terms)
        learned = len(self.learned_terms)
        percentage = (learned / total * 100) if total > 0 else 0
        self.progress_label.config(
            text=f"Изучено: {learned}/{total} ({percentage:.1f}%)"
        )


class LearningModeWindow:
    def __init__(self, parent, terms):
        self.terms = terms
        self.current_index = 0
        self.show_answer = False

        self.window = tk.Toplevel(parent)
        self.window.title("Режим обучения")
        self.window.geometry("400x500")
        self.window.configure(bg="#f8f9fa")

        self.setup_learning_ui()
        self.show_current_card()

    def setup_learning_ui(self):
        """Настройка интерфейса режима обучения"""
        # Прогресс
        self.progress_label = tk.Label(
            self.window, text="", font=("Arial", 12, "bold"), bg="#f8f9fa", fg="#2c3e50"
        )
        self.progress_label.pack(pady=10)

        # Карточка
        card_frame = tk.Frame(self.window, bg="#ffffff", relief="raised", bd=2)
        card_frame.pack(pady=20, padx=20, fill="both", expand=True)

        # Термин
        self.term_label = tk.Label(
            card_frame,
            text="",
            font=("Arial", 16, "bold"),
            bg="#ffffff",
            fg="#2c3e50",
            wraplength=350,
        )
        self.term_label.pack(pady=20)

        # Ответ (изначально скрыт)
        self.answer_frame = tk.Frame(card_frame, bg="#ffffff")
        self.answer_frame.pack(pady=10, fill="x")

        self.translation_label = tk.Label(
            self.answer_frame,
            text="",
            font=("Arial", 14),
            bg="#ffffff",
            fg="#2980b9",
            wraplength=350,
        )
        self.translation_label.pack()

        self.definition_label = tk.Label(
            self.answer_frame,
            text="",
            font=("Arial", 12),
            bg="#ffffff",
            fg="#2c3e50",
            wraplength=350,
            justify="left",
        )
        self.definition_label.pack(pady=10)

        # Кнопки управления
        button_frame = tk.Frame(self.window, bg="#f8f9fa")
        button_frame.pack(pady=20)

        self.prev_btn = tk.Button(
            button_frame,
            text="⬅️ Назад",
            command=self.previous_card,
            bg="#e67e22",
            fg="white",
            font=("Arial", 10),
        )
        self.prev_btn.pack(side="left", padx=5)

        self.show_btn = tk.Button(
            button_frame,
            text="🔍 Показать ответ",
            command=self.toggle_answer,
            bg="#3498db",
            fg="white",
            font=("Arial", 10),
        )
        self.show_btn.pack(side="left", padx=5)

        self.next_btn = tk.Button(
            button_frame,
            text="Вперед ➡️",
            command=self.next_card,
            bg="#27ae60",
            fg="white",
            font=("Arial", 10),
        )
        self.next_btn.pack(side="left", padx=5)

        # Кнопка выхода
        exit_btn = tk.Button(
            self.window,
            text="Выход",
            command=self.window.destroy,
            bg="#e74c3c",
            fg="white",
            font=("Arial", 10),
        )
        exit_btn.pack(pady=10)

    def show_current_card(self):
        """Показать текущую карточку"""
        if not self.terms:
            return

        term = self.terms[self.current_index]

        # Обновление прогресса
        self.progress_label.config(text=f"{self.current_index + 1}/{len(self.terms)}")

        # Термин
        self.term_label.config(text=term["term"])

        # Перевод и определение
        self.translation_label.config(text=f"Перевод: {term['translation']}")
        self.definition_label.config(text=f"Определение: {term['definition']}")

        # Скрыть ответ
        self.show_answer = False
        self.answer_frame.pack_forget()
        self.show_btn.config(text="🔍 Показать ответ")

    def toggle_answer(self):
        """Показать/скрыть ответ"""
        self.show_answer = not self.show_answer
        if self.show_answer:
            self.answer_frame.pack(pady=10, fill="x")
            self.show_btn.config(text="🙈 Скрыть ответ")
        else:
            self.answer_frame.pack_forget()
            self.show_btn.config(text="🔍 Показать ответ")

    def next_card(self):
        """Следующая карточка"""
        self.current_index = (self.current_index + 1) % len(self.terms)
        self.show_current_card()

    def previous_card(self):
        """Предыдущая карточка"""
        self.current_index = (self.current_index - 1) % len(self.terms)
        self.show_current_card()


def main():
    root = tk.Tk()
    app = ProgrammingDictionaryApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
