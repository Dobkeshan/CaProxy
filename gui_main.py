from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton, QTextEdit, QGroupBox, QProgressBar
from PyQt6.QtCore import pyqtSignal

class ProxyGUI(QMainWindow):
    mode_changed = pyqtSignal(str)
    toggle_proxy = pyqtSignal()
    log_signal = pyqtSignal(str)
    open_settings = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Tor Proxy Bridge")
        self.resize(550, 500)
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        mode_group = QGroupBox("Operation Mode")
        mode_layout = QHBoxLayout()
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["regular", "system"])
        mode_layout.addWidget(QLabel("Mode"))
        mode_layout.addWidget(self.mode_combo)
        mode_group.setLayout(mode_layout)

        control_layout = QHBoxLayout()
        self.start_btn = QPushButton("Start")
        self.settings_btn = QPushButton("Settings")
        self.status_label = QLabel("Stopped")
        control_layout.addWidget(self.start_btn)
        control_layout.addWidget(self.settings_btn)
        control_layout.addWidget(self.status_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)

        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)

        layout.addWidget(mode_group)
        layout.addLayout(control_layout)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.log_box)

        self.start_btn.clicked.connect(self.toggle_proxy.emit)
        self.settings_btn.clicked.connect(self.open_settings.emit)
        self.mode_combo.currentTextChanged.connect(self.mode_changed.emit)

    def update_status(self, running):
        self.status_label.setText("Running" if running else "Stopped")
        self.start_btn.setText("Stop" if running else "Start")
        self.progress_bar.setVisible(False)

    def show_progress(self, visible=True):
        self.progress_bar.setVisible(visible)
        if visible:
            self.progress_bar.setRange(0, 0)

    def set_progress(self, value):
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(value)

    def append_log(self, message):
        self.log_box.append(message)