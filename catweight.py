import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import pickle
import os


class Cat:
    def __init__(self, name, breed, birth_year):
        self.name = name
        self.breed = breed
        self.birth_year = birth_year
        self.weight_data = {}  # Словарь для хранения веса по датам {дата: вес}

    @property
    def age(self):
        current_year = datetime.now().year
        return current_year - self.birth_year

    def add_weight_record(self, date, weight):
        """Добавляет запись о весе на определенную дату"""
        self.weight_data[date] = weight

    def get_weight_by_date(self, date):
        """Возвращает вес на определенную дату"""
        return self.weight_data.get(date, None)

    def get_weight_for_period(self, start_date, end_date):
        """Возвращает список дат и весов за указанный период"""
        dates = []
        weights = []
        current_date = start_date
        while current_date <= end_date:
            if current_date in self.weight_data:
                dates.append(current_date)
                weights.append(self.weight_data[current_date])
            current_date += timedelta(days=1)
        return dates, weights


class CatApp:
    def __init__(self):
        self.cats = []
        self.data_file = "cats_data.pkl"
        self.load_data()

    def add_cat(self, name, breed, birth_year):
        """Добавляет нового кота в приложение"""
        cat = Cat(name, breed, birth_year)
        self.cats.append(cat)
        self.save_data()
        return cat

    def save_data(self):
        """Сохраняет данные о котах в файл"""
        with open(self.data_file, 'wb') as f:
            pickle.dump(self.cats, f)

    def load_data(self):
        """Загружает данные о котах из файла"""
        if os.path.exists(self.data_file):
            with open(self.data_file, 'rb') as f:
                self.cats = pickle.load(f)

    def plot_weight_chart(self, cat, period='daily'):
        """Строит график веса кота за указанный период"""
        today = datetime.now().date()

        if period == 'daily':
            start_date = today - timedelta(days=1)
            title = f"Вес кота {cat.name} за день"
        elif period == 'weekly':
            start_date = today - timedelta(weeks=1)
            title = f"Вес кота {cat.name} за неделю"
        elif period == 'monthly':
            start_date = today - timedelta(days=30)
            title = f"Вес кота {cat.name} за месяц"
        elif period == 'yearly':
            start_date = today - timedelta(days=365)
            title = f"Вес кота {cat.name} за год"
        else:
            raise ValueError("Неверный период. Допустимые значения: 'daily', 'weekly', 'monthly', 'yearly'")

        dates, weights = cat.get_weight_for_period(start_date, today)

        if not dates:
            print(f"Нет данных о весе за указанный период ({period})")
            return

        plt.figure(figsize=(10, 5))
        plt.plot(dates, weights, marker='o')
        plt.title(title)
        plt.xlabel("Дата")
        plt.ylabel("Вес (кг)")
        plt.grid(True)
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.show()


def main():
    app = CatApp()

    if not app.cats:
        print("Создайте нового кота:")
        name = input("Имя кота: ")
        breed = input("Порода кота: ")
        birth_year = int(input("Год рождения кота: "))
        cat = app.add_cat(name, breed, birth_year)
    else:
        cat = app.cats[0]
        print(f"Загружен кот: {cat.name}, {cat.breed}, возраст: {cat.age} лет")

    while True:
        print("\nМеню:")
        print("1. Добавить запись о весе на сегодня")
        print("2. Добавить запись о весе на другую дату")
        print("3. Показать график веса")
        print("4. Выйти")

        choice = input("Выберите действие: ")

        if choice == '1':
            weight = float(input("Введите вес кота на сегодня (кг): "))
            today = datetime.now().date()
            cat.add_weight_record(today, weight)
            app.save_data()
            print(f"Запись добавлена: {today} - {weight} кг")

        elif choice == '2':
            date_str = input("Введите дату (ДД.ММ.ГГГГ): ")
            try:
                date = datetime.strptime(date_str, "%d.%m.%Y").date()
                weight = float(input("Введите вес кота на эту дату (кг): "))
                cat.add_weight_record(date, weight)
                app.save_data()
                print(f"Запись добавлена: {date} - {weight} кг")
            except ValueError:
                print("Неверный формат даты. Используйте ДД.ММ.ГГГГ")

        elif choice == '3':
            print("\nТип графика:")
            print("1. Подневной")
            print("2. Недельный")
            print("3. Месячный")
            print("4. Годовой")
            chart_choice = input("Выберите тип графика: ")

            periods = {'1': 'daily', '2': 'weekly', '3': 'monthly', '4': 'yearly'}
            if chart_choice in periods:
                app.plot_weight_chart(cat, periods[chart_choice])
            else:
                print("Неверный выбор")

        elif choice == '4':
            print("Выход из программы")
            break

        else:
            print("Неверный выбор. Попробуйте снова.")


if __name__ == "__main__":
    main()