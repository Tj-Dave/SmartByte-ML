import sys
import random
import matplotlib.pyplot as plt
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QDateEdit, QMessageBox
)
from PyQt6.QtCore import QDate
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import pandas as pd

from apiModule import get_prediction_dataframe

class FloodRiskUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Flood Risk Predictor")
        self.setMinimumSize(800, 600)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Title
        title = QLabel("🌊 Smart Flood Risk Assessment")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #2E86C1;")
        layout.addWidget(title)

        # Form layout
        form_layout = QHBoxLayout()

        self.city_input = QLineEdit()
        self.city_input.setPlaceholderText("e.g., Kampala")

        self.date_input = QDateEdit()
        self.date_input.setCalendarPopup(True)
        self.date_input.setDate(QDate.currentDate())

        submit_btn = QPushButton("Get Forecast")
        submit_btn.clicked.connect(self.on_submit)

        form_layout.addWidget(QLabel("City:"))
        form_layout.addWidget(self.city_input)
        form_layout.addWidget(QLabel("Date:"))
        form_layout.addWidget(self.date_input)
        form_layout.addWidget(submit_btn)

        layout.addLayout(form_layout)

        # Matplotlib Canvas
        self.canvas = FigureCanvas(plt.figure(figsize=(6, 4)))
        layout.addWidget(self.canvas)

        # Status label
        self.status_label = QLabel("")
        layout.addWidget(self.status_label)

        self.setLayout(layout)

    def on_submit(self):
        city = self.city_input.text().strip()
        date = self.date_input.date().toString("yyyy-MM-dd")

        if not city:
            QMessageBox.warning(self, "Input Error", "Please enter a city.")
            return

        try:
            df = get_prediction_dataframe(city, date)
            if df.empty:
                raise ValueError("No prediction returned.")

            self.plot_data(df.iloc[0])
            self.status_label.setText(f"✔️ Forecast for {city} on {date}")
        except Exception as e:
            QMessageBox.critical(self, "Prediction Error", str(e))
            self.status_label.setText("")

    def plot_data(self, row):
        self.canvas.figure.clf()
        ax = self.canvas.figure.add_subplot(111)

        labels = ['Monsoon Intensity', 'Siltation', 'Landslides']
        values = [
            row.get("MonsoonIntensity", 0),
            row.get("Siltation", 0),
            row.get("Landslides", 0)
        ]

        ax.bar(labels, values, color=['#3498db', '#e67e22', '#2ecc71'])
        ax.set_ylim(0, 100)
        ax.set_ylabel("Risk Level (%)")
        ax.set_title("Flood Risk Breakdown")
        self.canvas.draw()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FloodRiskUI()
    window.show()
    sys.exit(app.exec())
