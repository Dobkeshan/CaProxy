from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QLineEdit, QPushButton, QTextEdit, QGroupBox
from PyQt6.QtCore import pyqtSignal

class ProxyGUI(QMainWindow):
    bridge_changed = pyqtSignal(str, str)
    mode_changed = pyqtSignal(str)
    toggle_proxy = pyqtSignal()
    log_signal = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Tor Proxy Bridge")
        self.resize(550, 450)
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        bridge_group = QGroupBox("Bridge Settings")
        bridge_layout = QVBoxLayout()
        self.bridge_type = QComboBox()
        self.bridge_type.addItems(["none", "obfs4", "meek"])
        self.bridge_address = QLineEdit()
        self.bridge_address.setPlaceholderText("IP:PORT FINGERPRINT")
        bridge_layout.addWidget(QLabel("Type"))
        bridge_layout.addWidget(self.bridge_type)
        bridge_layout.addWidget(QLabel("Address"))
        bridge_layout.addWidget(self.bridge_address)
        bridge_group.setLayout(bridge_layout)

        mode_group = QGroupBox("Operation Mode")
        mode_layout = QHBoxLayout()
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["regular", "system"])
        mode_layout.addWidget(QLabel("Mode"))
        mode_layout.addWidget(self.mode_combo)
        mode_group.setLayout(mode_layout)

        control_layout = QHBoxLayout()
        self.start_btn = QPushButton("Start")
        self.status_label = QLabel("Stopped")
        control_layout.addWidget(self.start_btn)
        control_layout.addWidget(self.status_label)

        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)

        layout.addWidget(bridge_group)
        layout.addWidget(mode_group)
        layout.addLayout(control_layout)
        layout.addWidget(self.log_box)

        self.start_btn.clicked.connect(self.toggle_proxy.emit)
        self.bridge_type.currentTextChanged.connect(self._emit_bridge)
        self.bridge_address.textChanged.connect(self._emit_bridge)
        self.mode_combo.currentTextChanged.connect(self.mode_changed.emit)

    def _emit_bridge(self):
        self.bridge_changed.emit(self.bridge_type.currentText(), self.bridge_address.text())

    def update_status(self, running):
        self.status_label.setText("Running" if running else "Stopped")
        self.start_btn.setText("Stop" if running else "Start")

    def append_log(self, message):
        self.log_box.append(message)