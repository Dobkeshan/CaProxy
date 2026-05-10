from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QRadioButton, QListWidget, QLineEdit, QPushButton, QGroupBox
from PyQt6.QtCore import pyqtSignal
from config import AppConfig

class SettingsDialog(QDialog):
    save_settings = pyqtSignal(str, list)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Settings")
        self.resize(600, 400)
        layout = QVBoxLayout(self)

        type_group = QGroupBox("Bridge Type")
        type_layout = QVBoxLayout()
        self.rb_none = QRadioButton("None")
        self.rb_obfs4 = QRadioButton("obfs4")
        self.rb_meek = QRadioButton("meek")
        self.rb_obfs4.setChecked(True)
        type_layout.addWidget(self.rb_none)
        type_layout.addWidget(self.rb_obfs4)
        type_layout.addWidget(self.rb_meek)
        type_group.setLayout(type_layout)

        bridge_group = QGroupBox("Bridge List")
        bridge_layout = QVBoxLayout()
        self.bridge_list = QListWidget()
        for bridge in AppConfig.built_in_bridges:
            self.bridge_list.addItem(bridge)
        self.bridge_input = QLineEdit()
        self.bridge_input.setPlaceholderText("obfs4 IP:PORT FINGERPRINT cert=... iat-mode=0")
        add_btn = QPushButton("Add")
        remove_btn = QPushButton("Remove Selected")
        input_layout = QHBoxLayout()
        input_layout.addWidget(self.bridge_input)
        input_layout.addWidget(add_btn)
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(remove_btn)
        bridge_layout.addLayout(input_layout)
        bridge_layout.addLayout(btn_layout)
        bridge_layout.addWidget(self.bridge_list)
        bridge_group.setLayout(bridge_layout)

        save_btn = QPushButton("Save & Close")

        layout.addWidget(type_group)
        layout.addWidget(bridge_group)
        layout.addWidget(save_btn)

        add_btn.clicked.connect(self._add_bridge)
        remove_btn.clicked.connect(self._remove_bridge)
        save_btn.clicked.connect(self._save)
        self.rb_none.toggled.connect(self._update_list_state)
        self._update_list_state()

    def _update_list_state(self):
        enabled = not self.rb_none.isChecked()
        self.bridge_list.setEnabled(enabled)
        self.bridge_input.setEnabled(enabled)

    def _add_bridge(self):
        text = self.bridge_input.text().strip()
        if text:
            self.bridge_list.addItem(text)
            self.bridge_input.clear()

    def _remove_bridge(self):
        for item in self.bridge_list.selectedItems():
            self.bridge_list.takeItem(self.bridge_list.row(item))

    def _save(self):
        bridge_type = "none"
        if self.rb_obfs4.isChecked():
            bridge_type = "obfs4"
        elif self.rb_meek.isChecked():
            bridge_type = "meek"
        bridges = [self.bridge_list.item(i).text() for i in range(self.bridge_list.count())]
        self.save_settings.emit(bridge_type, bridges)
        self.close()