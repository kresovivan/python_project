import sys
import pickle
from datetime import datetime, timedelta
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QLineEdit, QComboBox, QWidget, QScrollArea, QMessageBox)
from PyQt5.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.dates as mdates


class Cat:
    def __init__(self, name, breed, birth_year):
        self.name = name
        self.breed = breed
        self.birth_year = birth_year
        self.weight_data = {}  # {дата: вес}

    @property
    def age(self):
        return datetime.now().year - self.birth_year

    def add_weight(self, date, weight):
        self.weight_data[date] = weight

    def get_weight_changes(self, start_date, end_date):
        dates = []
        weights = []
        colors = []
        prev_weight = None

        current_date = start_date
        while current_date <= end_date:
            if current_date in self.weight_data:
                current_weight = self.weight_data[current_date]
                dates.append(current_date)
                weights.append(current_weight)

                if prev_weight is None:
                    colors.append('blue')  # Первая точка
                elif current_weight > prev_weight:
                    colors.append('red')  # Увеличение веса
                elif current_weight < prev_weight:
                    colors.append('green')  # Уменьшение веса
                else:
                    colors.append('blue')  # Без изменений

                prev_weight = current_weight
            current_date += timedelta(days=1)

        return dates, weights, colors


class CatApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.cat = None
        self.data_file = "cat_data.pkl"
        self.init_ui()
        self.load_data()

    def init_ui(self):
        self.setWindowTitle("Учет веса кота")
        self.setGeometry(100, 100, 800, 600)

        # Главный виджет и layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout()
        main_widget.setLayout(main_layout)

        # Информация о коте
        self.info_layout = QHBoxLayout()
        main_layout.addLayout(self.info_layout)

        # Форма ввода данных
        self.form_layout = QVBoxLayout()
        self.name_input = QLineEdit()
        self.breed_input = QLineEdit()
        self.birth_year_input = QLineEdit()

        self.form_layout.addWidget(QLabel("Имя кота:"))
        self.form_layout.addWidget(self.name_input)
        self.form_layout.addWidget(QLabel("Порода:"))
        self.form_layout.addWidget(self.breed_input)
        self.form_layout.addWidget(QLabel("Год рождения:"))
        self.form_layout.addWidget(self.birth_year_input)

        # Кнопки
        self.save_cat_btn = QPushButton("Сохранить данные кота")
        self.save_cat_btn.clicked.connect(self.save_cat_data)
        self.form_layout.addWidget(self.save_cat_btn)

        self.add_weight_btn = QPushButton("Добавить вес на сегодня")
        self.add_weight_btn.clicked.connect(self.add_weight_today)
        self.form_layout.addWidget(self.add_weight_btn)

        self.weight_input = QLineEdit()
        self.form_layout.addWidget(QLabel("Вес (кг):"))
        self.form_layout.addWidget(self.weight_input)

        # Выбор периода для графика
        self.period_combo = QComboBox()
        self.period_combo.addItems(["День", "Неделя", "Месяц", "Год"])
        self.form_layout.addWidget(QLabel("Период графика:"))
        self.form_layout.addWidget(self.period_combo)

        self.plot_btn = QPushButton("Построить график")
        self.plot_btn.clicked.connect(self.plot_weight_chart)
        self.form_layout.addWidget(self.plot_btn)

        # График с прокруткой
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.canvas)

        # Основной layout
        main_layout.addLayout(self.form_layout)
        main_layout.addWidget(scroll)

        # Обновляем интерфейс
        self.update_ui()

    def update_ui(self):
        if self.cat:
            self.name_input.setText(self.cat.name)
            self.breed_input.setText(self.cat.breed)
            self.birth_year_input.setText(str(self.cat.birth_year))
            self.add_weight_btn.setEnabled(True)
            self.plot_btn.setEnabled(True)
        else:
            self.add_weight_btn.setEnabled(False)
            self.plot_btn.setEnabled(False)

    def save_cat_data(self):
        name = self.name_input.text()
        breed = self.breed_input.text()
        try:
            birth_year = int(self.birth_year_input.text())
            if birth_year < 1900 or birth_year > datetime.now().year:
                raise ValueError
        except ValueError:
            QMessageBox.warning(self, "Ошибка", "Введите корректный год рождения")
            return

        self.cat = Cat(name, breed, birth_year)
        self.save_data()
        self.update_ui()
        QMessageBox.information(self, "Сохранено", "Данные кота сохранены")

    def add_weight_today(self):
        try:
            weight = float(self.weight_input.text())
            if weight <= 0:
                raise ValueError
        except ValueError:
            QMessageBox.warning(self, "Ошибка", "Введите корректный вес (положительное число)")
            return

        today = datetime.now().date()
        self.cat.add_weight(today, weight)
        self.save_data()
        QMessageBox.information(self, "Сохранено", f"Вес на {today}: {weight} кг")
        self.weight_input.clear()

    def plot_weight_chart(self):
        if not self.cat or not self.cat.weight_data:
            QMessageBox.warning(self, "Ошибка", "Нет данных о весе для построения графика")
            return

        today = datetime.now().date()
        period = self.period_combo.currentText()

        if period == "День":
            start_date = today - timedelta(days=1)
        elif period == "Неделя":
            start_date = today - timedelta(weeks=1)
        elif period == "Месяц":
            start_date = today - timedelta(days=30)
        else:  # Год
            start_date = today - timedelta(days=365)

        dates, weights, colors = self.cat.get_weight_changes(start_date, today)

        if not dates:
            QMessageBox.warning(self, "Ошибка", f"Нет данных о весе за выбранный период ({period})")
            return

        self.figure.clear()
        ax = self.figure.add_subplot(111)

        # Рисуем линии между точками с разными цветами
        for i in range(len(dates) - 1):
            ax.plot([dates[i], dates[i + 1]], [weights[i], weights[i + 1]],
                    color=colors[i + 1], marker='o', linestyle='-')

        # Первая точка
        if len(dates) > 0:
            ax.plot(dates[0], weights[0], 'bo')

        # Форматирование графика
        ax.set_title(f"Вес кота {self.cat.name} за {period.lower()}")
        ax.set_xlabel("Дата")
        ax.set_ylabel("Вес (кг)")
        ax.grid(True)

        # Формат дат на оси X
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%d.%m.%Y'))
        self.figure.autofmt_xdate()

        self.canvas.draw()

    def save_data(self):
        with open(self.data_file, 'wb') as f:
            pickle.dump(self.cat, f)

    def load_data(self):
        try:
            with open(self.data_file, 'rb') as f:
                self.cat = pickle.load(f)
                self.update_ui()
        except (FileNotFoundError, EOFError):
            pass


def main():
    app = QApplication(sys.argv)
    window = CatApp()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()