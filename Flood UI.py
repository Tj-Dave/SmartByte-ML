import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout,
    QComboBox, QPushButton, QDateEdit, QMessageBox
)
from PyQt6.QtCore import QDate, Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import pandas as pd
import numpy as np
import rasterio
from matplotlib.cm import ScalarMappable
from matplotlib.colors import Normalize
from apiModule import get_prediction_dataframe  # Assumed external module

class FloodRiskUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Flood Risk Predictor")
        self.setMinimumSize(1200, 800)  # Large window for map
        self.setStyleSheet("background-color: #f5f6fa;")
        self.init_ui()

    def init_ui(self):
        main_layout = QHBoxLayout()
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Sidebar for inputs and legend
        sidebar = QWidget()
        sidebar.setStyleSheet("""
            background-color: #2c3e50;
            border-radius: 10px;
            padding: 10px;
        """)
        sidebar_layout = QVBoxLayout()
        sidebar_layout.setSpacing(10)
        sidebar_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Title
        title = QLabel("🌊 Flood Risk Predictor")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #ffffff; margin: 10px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sidebar_layout.addWidget(title)

        # City input
        city_label = QLabel("Select City:")
        city_label.setStyleSheet("font-size: 14px; color: #ffffff;")
        self.city_input = QComboBox()
        self.city_input.addItems(["Kampala", "Kabale", "Kasese"])
        self.city_input.setStyleSheet("""
            QComboBox {
                padding: 8px;
                border: 1px solid #ccc;
                border-radius: 5px;
                background-color: #ffffff;
                color: #333333;
                font-size: 14px;
            }
        """)
        self.city_input.setFixedWidth(200)

        # Date input
        date_label = QLabel("Year-Month:")
        date_label.setStyleSheet("font-size: 14px; color: #ffffff;")
        self.date_input = QDateEdit()
        self.date_input.setCalendarPopup(True)
        self.date_input.setDisplayFormat("yyyy-MM")
        self.date_input.setDate(QDate.currentDate())
        self.date_input.setStyleSheet("""
            QDateEdit {
                padding: 8px;
                border: 1px solid #ccc;
                border-radius: 5px;
                background-color: #ffffff;
                color: #333333;
                font-size: 14px;
            }
        """)
        self.date_input.setFixedWidth(200)

        # Submit button
        submit_btn = QPushButton("Get Forecast")
        submit_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 10px;
                border-radius: 5px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        submit_btn.clicked.connect(self.on_submit)

        # Legend
        legend_label = QLabel("""
            <h3 style='color: #ffffff;'>Legend</h3>
            <p style='color: #ffffff;'>
                <b>Vulnerability Index:</b><br>
                Blue (0) to Red (1)<br>
                <b>Flood Probability:</b><br>
                Opacity (0.2 to 0.8)<br>
                <b>Flood Size:</b><br>
                Circle size (0 to 500 km²)
            </p>
        """)
        legend_label.setStyleSheet("font-size: 12px; color: #ffffff; margin-top: 20px;")

        sidebar_layout.addWidget(city_label)
        sidebar_layout.addWidget(self.city_input)
        sidebar_layout.addWidget(date_label)
        sidebar_layout.addWidget(self.date_input)
        sidebar_layout.addWidget(submit_btn)
        sidebar_layout.addWidget(legend_label)
        sidebar_layout.addStretch()
        sidebar.setLayout(sidebar_layout)
        sidebar.setFixedWidth(250)

        # Map canvas
        self.map_canvas = FigureCanvas(plt.figure(figsize=(14, 14), dpi=200))
        self.map_canvas.setStyleSheet("background-color: white; border: 1px solid #ddd;")
        main_layout.addWidget(sidebar)
        main_layout.addWidget(self.map_canvas, stretch=1)

        # Status label
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("font-size: 14px; color: #ffffff; margin: 10px;")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sidebar_layout.addWidget(self.status_label)

        self.setLayout(main_layout)

    def on_submit(self):
        selected_city = self.city_input.currentText()
        date_qdate = self.date_input.date()
        year = date_qdate.year()
        month = date_qdate.month()
        date_str = f"{year:04d}-{month:02d}-01"

        try:
            df = get_prediction_dataframe(selected_city, date_str)
            if not df.empty:
                print(f"City: {selected_city}, Columns: {list(df.columns)}")
                print(f"Data types: {df.dtypes}")
                print(f"Sample row: {df.iloc[0][['FloodProbability_result', 'FloodSizeScore_result', 'VulnerabilityIndex_result']].to_dict()}")
                row = df.iloc[0]
                prediction = {
                    'city': selected_city,
                    'size_score': float(row['FloodSizeScore_result']) if 'FloodSizeScore_result' in row else 0.0,
                    'vulnerability': float(row['VulnerabilityIndex_result']) if 'VulnerabilityIndex_result' in row else 0.0,
                    'probability': float(row['FloodProbability_result']) if 'FloodProbability_result' in row else 0.0
                }
                self.plot_map([prediction])
                self.status_label.setText(f"✔️ Forecast for {selected_city} on {date_str}")
            else:
                raise ValueError("No prediction data available for the selected city.")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
            self.clear_display()

    def plot_map(self, predictions):
        self.map_canvas.figure.clf()
        fig = self.map_canvas.figure
        ax = fig.add_subplot(111)

        # City coordinates (latitude, longitude in WGS84)
        city_positions = {
            "Kampala": (0.3163, 32.5822),
            "Kabale": (-1.2419, 29.9856),
            "Kasese": (0.1833, 30.0833)
        }

        # Load GeoTIFF for georeferencing
        try:
            with rasterio.open('maps/uganda.tiff') as src:
                bounds = src.bounds
                extent = [bounds.left, bounds.right, bounds.bottom, bounds.top]
                print(f"GeoTIFF bounds: {extent}")
                for city, (lat, lon) in city_positions.items():
                    print(f"City {city}: lat={lat}, lon={lon}, within bounds? "
                          f"{bounds.left <= lon <= bounds.right and bounds.bottom <= lat <= bounds.top}")
        except Exception as e:
            print(f"Error loading GeoTIFF: {e}")
            ax.text(0.5, 0.5, "GeoTIFF not found or invalid", ha='center', va='center', fontsize=12, color='#333333')
            ax.axis('off')
            fig.tight_layout()
            self.map_canvas.draw()
            return

        # Load PNG for visualization
        try:
            map_image = plt.imread('maps/uganda.png')
            ax.imshow(map_image, extent=extent, aspect='equal')
        except Exception as e:
            print(f"Error loading PNG: {e}")
            ax.text(0.5, 0.5, "PNG map not found", ha='center', va='center', fontsize=12, color='#333333')
            ax.axis('off')
            fig.tight_layout()
            self.map_canvas.draw()
            return

        x, y, sizes, colors = [], [], [], []
        for pred in predictions:
            city = pred['city']
            if pred['size_score'] is not None and city in city_positions:
                lat, lon = city_positions[city]
                flood_area_km2 = pred['size_score'] * 500  # Convert to km²
                vulnerability = pred['vulnerability']
                probability = max(0.2, min(0.8, pred['probability']))  # Opacity 0.2-0.8

                # Main marker
                x.append(lon)
                y.append(lat)
                sizes.append(flood_area_km2 * 10)  # Scale for visibility
                color = plt.cm.coolwarm(vulnerability)
                color = list(color)
                color[3] = probability
                colors.append(color)

                # Glow effect (larger, semi-transparent circle)
                glow = patches.Circle((lon, lat), radius=0.05, color=color, alpha=probability * 0.3, transform=ax.transData)
                ax.add_patch(glow)

                # Dynamic label
                label_text = f"{city}\nFlood Size: {flood_area_km2:.1f} km²\nProb: {probability:.2f}\nVuln: {vulnerability:.2f}"
                ax.text(lon + 0.05, lat + 0.05, label_text, fontsize=10, color='#333333', 
                        bbox=dict(facecolor='white', alpha=0.8, edgecolor='#333333', boxstyle='round,pad=0.3'))

        if x:
            ax.scatter(x, y, s=sizes, c=colors, edgecolor='black', linewidth=0.5)

        ax.axis('off')  # No grid, ticks, or labels
        ax.set_title("Flood Risk Map - Uganda", fontsize=16, color='#333333', pad=10)

        # Legends
        norm_vuln = Normalize(vmin=0, vmax=1)
        cmap_vuln = plt.cm.coolwarm
        sm_vuln = ScalarMappable(cmap=cmap_vuln, norm=norm_vuln)
        cbar_vuln = fig.colorbar(sm_vuln, ax=ax, orientation='vertical', fraction=0.05, pad=0.02)
        cbar_vuln.set_label('Vulnerability Index', fontsize=12, color='#333333')
        cbar_vuln.ax.tick_params(labelcolor='#333333')

        opacity_patches = []
        for alpha in [0.2, 0.5, 0.8]:
            opacity_patches.append(plt.Line2D([0], [0], marker='o', color='none',
                                             markerfacecolor='gray', markeredgecolor='black',
                                             markersize=10, alpha=alpha, label=f'{alpha:.1f}'))
        opacity_legend = ax.legend(handles=opacity_patches, title='Flood Probability',
                                  loc='lower right', fontsize=10, title_fontsize=12,
                                  framealpha=0.8, edgecolor='#333333')
        for text in opacity_legend.get_texts():
            text.set_color('#333333')
        opacity_legend.get_title().set_color('#333333')

        fig.tight_layout()
        self.map_canvas.draw()

    def clear_display(self):
        self.status_label.setText("")
        self.map_canvas.figure.clf()
        self.map_canvas.draw()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FloodRiskUI()
    window.show()
    sys.exit(app.exec())