import sys
from PyQt6.QtWidgets import QApplication, QMessageBox
from gui_main import ProxyGUI
from gui_settings import SettingsDialog
from proxy_server import ProxyServer
from tor_manager import TorManager
from system_proxy import SystemProxy
from config import AppConfig

class AppController:
    def __init__(self):
        self.tor = TorManager()
        self.proxy = ProxyServer()
        self.gui = ProxyGUI()
        self.settings = SettingsDialog()
        self.gui.toggle_proxy.connect(self.toggle)
        self.gui.open_settings.connect(self.settings.exec)
        self.settings.save_settings.connect(self.apply_settings)
        self.gui.log_signal.connect(self.gui.append_log)
        self.bridge_type = "obfs4"
        self.bridge_list = AppConfig.built_in_bridges.copy()
        self.mode = "regular"
        self.is_active = False

    def apply_settings(self, b_type, b_list):
        self.bridge_type = b_type
        self.bridge_list = b_list

    def toggle(self):
        if self.is_active:
            self.stop()
        else:
            self.start()

    def start(self):
        try:
            self.gui.log_signal.emit("Initializing TOR...")
            self.tor.start(self.bridge_type, self.bridge_list)
            self.gui.log_signal.emit("Starting local proxy...")
            self.proxy.start()
            mode = self.gui.mode_combo.currentText()
            if mode == "system":
                self.gui.log_signal.emit("Setting system proxy...")
                SystemProxy.enable(AppConfig.local_host, AppConfig.local_proxy_port)
            self.gui.update_status(True)
            self.gui.log_signal.emit("Proxy active. Traffic encrypted through TOR.")
        except RuntimeError as e:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Icon.Critical)
            msg.setText("Tor не найден")
            msg.setInformativeText(str(e))
            msg.exec()
            self.gui.log_signal.emit(f"Error: {str(e)}")
        except Exception as e:
            self.gui.log_signal.emit(f"Error: {str(e)}")

    def stop(self):
        try:
            mode = self.gui.mode_combo.currentText()
            if mode == "system":
                SystemProxy.disable()
            self.proxy.stop()
            self.tor.stop()
            self.gui.update_status(False)
            self.gui.log_signal.emit("Proxy stopped.")
        except Exception as e:
            self.gui.log_signal.emit(f"Error: {str(e)}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    controller = AppController()
    controller.gui.show()
    sys.exit(app.exec())