from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QSlider, QPushButton, QComboBox
from PyQt6.QtCore import Qt
from backend.config_manager import config
from ui.styles import get_settings_style

class SettingsWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        config.updated.connect(self.load_from_config)

    def init_ui(self):
        self.setWindowTitle("Options")
        self.resize(320, 250)
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        
        layout = QVBoxLayout()
        layout.setSpacing(15)

        self.theme_label = QLabel("Theme of widjet:")
        self.theme_combo = QComboBox()
        self.theme_combo.addItem("Black theme", "dark")
        self.theme_combo.addItem("White theme", "light")
        
        self.files_label = QLabel()
        self.files_slider = QSlider(Qt.Orientation.Horizontal)
        self.files_slider.setMinimum(1)
        self.files_slider.setMaximum(50)
        self.files_slider.valueChanged.connect(self.update_labels)

        self.delay_label = QLabel()
        self.delay_slider = QSlider(Qt.Orientation.Horizontal)
        self.delay_slider.setMinimum(1)
        self.delay_slider.setMaximum(20)
        self.delay_slider.valueChanged.connect(self.update_labels)

        self.save_btn = QPushButton("Save")
        self.save_btn.clicked.connect(self.save_settings)

        layout.addWidget(self.theme_label)
        layout.addWidget(self.theme_combo)
        layout.addWidget(self.files_label)
        layout.addWidget(self.files_slider)
        layout.addWidget(self.delay_label)
        layout.addWidget(self.delay_slider)
        layout.addStretch()
        layout.addWidget(self.save_btn)

        self.setLayout(layout)
        self.load_from_config()

    def load_from_config(self):
        self.setStyleSheet(get_settings_style(config.theme))
        
        self.files_slider.setValue(config.max_files)
        self.delay_slider.setValue(int(config.hover_delay * 10))
        
        idx = self.theme_combo.findData(config.theme)
        if idx >= 0:
            self.theme_combo.setCurrentIndex(idx)
            
        self.update_labels()

    def update_labels(self):
        self.files_label.setText(f"Max files: {self.files_slider.value()}")
        self.delay_label.setText(f"Time to show: {self.delay_slider.value() / 10.0} seconds")

    def save_settings(self):
        config.update_settings(
            max_files=self.files_slider.value(),
            hover_delay=self.delay_slider.value() / 10.0,
            theme=self.theme_combo.currentData()
        )
        self.hide()