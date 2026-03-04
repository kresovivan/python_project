import sys
import pickle
from datetime import datetime, timedelta
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QLineEdit,
    QComboBox,
    QWidget,
    QScrollArea,
    QMessageBox,
    QCalendarWidget,
    QGraphicsDropShadowEffect,
)
from PyQt5.QtCore import QDate, Qt, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QColor, QFont
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.dates as mdates


class Cat:
    def __init__(self, name, breed, birth_year):
        self.name = name
        self.breed = breed
        self.birth_year = birth_year
        self.weight_data = {}

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
                    colors.append("blue")
                elif current_weight > prev_weight:
                    colors.append("red")
                elif current_weight < prev_weight:
                    colors.append("green")
                else:
                    colors.append("blue")

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
        self.setGeometry(100, 100, 1100, 900)

        # Устанавливаем глобальный шрифт 12pt
        app_font = QFont()
        app_font.setPointSize(12)
        QApplication.setFont(app_font)

        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout()
        main_widget.setLayout(main_layout)

        # Форма ввода данных
        self.form_layout = QVBoxLayout()
        self.form_layout.setSpacing(15)

        # Поля для информации о коте
        name_label = QLabel("Имя кота:")
        self.name_input = QLineEdit()
        self.form_layout.addWidget(name_label)
        self.form_layout.addWidget(self.name_input)

        breed_label = QLabel("Порода:")
        self.breed_input = QLineEdit()
        self.form_layout.addWidget(breed_label)
        self.form_layout.addWidget(self.breed_input)

        year_label = QLabel("Год рождения:")
        self.birth_year_input = QLineEdit()
        self.form_layout.addWidget(year_label)
        self.form_layout.addWidget(self.birth_year_input)

        # Кнопка сохранения данных кота
        self.save_cat_btn = QPushButton("💾 Сохранить данные кота")
        self.save_cat_btn.clicked.connect(self.save_cat_data)
        self.save_cat_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #6a11cb, stop:1 #2575fc);
                color: white;
                border-radius: 10px;
                padding: 15px 25px;
                font-weight: bold;
                border: 2px solid #6a11cb;
                min-width: 250px;
                min-height: 50px;
                font-size: 12pt;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #2575fc, stop:1 #6a11cb);
                border: 2px solid #2575fc;
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4a00e0, stop:1 #2d00b3);
            }
        """)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setXOffset(3)
        shadow.setYOffset(3)
        shadow.setColor(QColor(0, 0, 0, 150))
        self.save_cat_btn.setGraphicsEffect(shadow)
        self.form_layout.addWidget(self.save_cat_btn)

        # Календарь с черным текстом
        calendar_label = QLabel("Выберите дату измерения:")
        self.calendar = QCalendarWidget()
        self.calendar.setGridVisible(True)
        self.calendar.setMinimumDate(QDate(2000, 1, 1))
        self.calendar.setMaximumDate(QDate.currentDate())

        # Стилизация календаря с черным текстом
        self.calendar.setStyleSheet("""
            /* Основные настройки */
            QCalendarWidget {
                font-size: 12pt;
                color: black;
            }

            /* Панель навигации */
            QCalendarWidget QWidget#qt_calendar_navigationbar {
                background: #f0f0f0;
                min-height: 50px;
                color: black;
            }

            /* Месяц и год - черный текст */
            QCalendarWidget QToolButton#qt_calendar_monthbutton {
                color: black;
                font-size: 12pt;
                min-width: 100px;
            }

            QCalendarWidget QToolButton#qt_calendar_yearbutton {
                color: black;
                font-size: 12pt;
                min-width: 70px;
            }

            /* Стрелки навигации */
            QCalendarWidget QToolButton#qt_calendar_prevmonth,
            QCalendarWidget QToolButton#qt_calendar_nextmonth {
                color: black;
                font-size: 12pt;
            }

            /* Дни недели */
            QCalendarWidget QAbstractItemView {
                color: black;
                font-size: 12pt;
            }

            /* Даты */
            QCalendarWidget QTableView {
                color: black;
                font-size: 12pt;
            }

            /* Выбранная дата */
            QCalendarWidget QAbstractItemView:selected {
                background-color: #6a11cb;
                color: white;
            }

            /* Выпадающие списки */
            QCalendarWidget QComboBox {
                color: black;
                font-size: 12pt;
            }

            /* Увеличенные ячейки */
            QCalendarWidget QTableView::item {
                height: 35px;
            }
        """)

        self.form_layout.addWidget(calendar_label)
        self.form_layout.addWidget(self.calendar)

        # Остальные элементы интерфейса
        weight_label = QLabel("Вес (кг):")
        self.weight_input = QLineEdit()
        self.form_layout.addWidget(weight_label)
        self.form_layout.addWidget(self.weight_input)

        self.add_weight_btn = QPushButton("➕ Добавить вес на выбранную дату")
        self.add_weight_btn.clicked.connect(self.add_weight_on_date)
        self.add_weight_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border-radius: 8px;
                padding: 12px 24px;
                font-weight: bold;
                border: 1px solid #388E3C;
                min-width: 250px;
                font-size: 12pt;
            }
            QPushButton:hover {
                background-color: #388E3C;
            }
            QPushButton:pressed {
                background-color: #2E7D32;
            }
        """)
        self.form_layout.addWidget(self.add_weight_btn)

        period_label = QLabel("Период графика:")
        self.period_combo = QComboBox()
        self.period_combo.addItems(["День", "Неделя", "Месяц", "Год"])
        self.form_layout.addWidget(period_label)
        self.form_layout.addWidget(self.period_combo)

        self.plot_btn = QPushButton("📊 Построить график")
        self.plot_btn.clicked.connect(self.plot_weight_chart)
        self.plot_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border-radius: 8px;
                padding: 12px 24px;
                font-weight: bold;
                border: 1px solid #1976D2;
                min-width: 250px;
                font-size: 12pt;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #0D47A1;
            }
        """)
        self.form_layout.addWidget(self.plot_btn)

        # График с прокруткой
        self.figure = Figure(figsize=(10, 5), dpi=100)
        self.canvas = FigureCanvas(self.figure)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.canvas)

        main_layout.addLayout(self.form_layout)
        main_layout.addWidget(scroll)

        self.update_ui()

    def load_data(self):
        try:
            with open(self.data_file, "rb") as f:
                self.cat = pickle.load(f)
                self.update_ui()
        except (FileNotFoundError, EOFError):
            self.cat = None

    def save_data(self):
        with open(self.data_file, "wb") as f:
            pickle.dump(self.cat, f)

    def save_cat_data(self):
        name = self.name_input.text().strip()
        breed = self.breed_input.text().strip()
        birth_year = self.birth_year_input.text().strip()

        if not name or not breed or not birth_year:
            QMessageBox.warning(self, "Ошибка", "Все поля должны быть заполнены!")
            return

        try:
            birth_year = int(birth_year)
            if birth_year < 1900 or birth_year > datetime.now().year:
                raise ValueError
        except ValueError:
            QMessageBox.warning(
                self, "Ошибка", "Год рождения должен быть корректным числом!"
            )
            return

        self.cat = Cat(name, breed, birth_year)
        self.save_data()
        self.update_ui()
        QMessageBox.information(self, "Успех", "Данные кота сохранены!")

    def add_weight_on_date(self):
        if not self.cat:
            QMessageBox.warning(self, "Ошибка", "Сначала сохраните данные кота!")
            return

        weight_text = self.weight_input.text().strip()
        if not weight_text:
            QMessageBox.warning(self, "Ошибка", "Введите вес кота!")
            return

        try:
            weight = float(weight_text)
            if weight <= 0:
                raise ValueError
        except ValueError:
            QMessageBox.warning(self, "Ошибка", "Вес должен быть положительным числом!")
            return

        qdate = self.calendar.selectedDate()
        date = datetime(qdate.year(), qdate.month(), qdate.day()).date()

        self.cat.add_weight(date, weight)
        self.save_data()
        self.update_ui()
        QMessageBox.information(
            self, "Успех", f"Вес {weight} кг добавлен на {date.strftime('%d.%m.%Y')}!"
        )

    def plot_weight_chart(self):
        if not self.cat or not self.cat.weight_data:
            QMessageBox.warning(self, "Ошибка", "Нет данных для построения графика!")
            return

        period = self.period_combo.currentText()
        end_date = datetime.now().date()

        if period == "День":
            start_date = end_date
        elif period == "Неделя":
            start_date = end_date - timedelta(days=7)
        elif period == "Месяц":
            start_date = end_date - timedelta(days=30)
        else:  # Год
            start_date = end_date - timedelta(days=365)

        dates, weights, colors = self.cat.get_weight_changes(start_date, end_date)

        if not dates:
            QMessageBox.warning(self, "Ошибка", "Нет данных за выбранный период!")
            return

        self.figure.clear()
        ax = self.figure.add_subplot(111)

        # Преобразуем даты в формат matplotlib
        mdates_dates = mdates.date2num(dates)

        # Рисуем график с разными цветами точек
        for i in range(len(dates)):
            ax.plot(mdates_dates[i], weights[i], "o", color=colors[i], markersize=10)

        # Соединяем точки линиями
        ax.plot(mdates_dates, weights, "b-", alpha=0.3)

        # Форматируем оси
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%d.%m.%Y"))
        ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        self.figure.autofmt_xdate()

        ax.set_title(f"Изменение веса кота {self.cat.name} за {period.lower()}")
        ax.set_xlabel("Дата")
        ax.set_ylabel("Вес (кг)")
        ax.grid(True)

        self.canvas.draw()

    def update_ui(self):
        if self.cat:
            self.name_input.setText(self.cat.name)
            self.breed_input.setText(self.cat.breed)
            self.birth_year_input.setText(str(self.cat.birth_year))
        else:
            self.name_input.clear()
            self.breed_input.clear()
            self.birth_year_input.clear()


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = CatApp()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
