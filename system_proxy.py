import platform
import subprocess

class SystemProxy:
    @staticmethod
    def enable(host, port):
        os_name = platform.system()
        if os_name == "Windows":
            SystemProxy._win_enable(host, port)
        elif os_name == "Darwin":
            SystemProxy._mac_enable(host, port)
        else:
            SystemProxy._linux_enable(host, port)

    @staticmethod
    def disable():
        os_name = platform.system()
        if os_name == "Windows":
            SystemProxy._win_disable()
        elif os_name == "Darwin":
            SystemProxy._mac_disable()
        else:
            SystemProxy._linux_disable()

    @staticmethod
    def _win_enable(host, port):
        import winreg
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Internet Settings"
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_ALL_ACCESS)
        winreg.SetValueEx(key, "ProxyEnable", 0, winreg.REG_DWORD, 1)
        winreg.SetValueEx(key, "ProxyServer", 0, winreg.REG_SZ, f"{host}:{port}")
        winreg.CloseKey(key)
        subprocess.run(["taskkill", "/f", "/im", "explorer.exe"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.Popen("explorer.exe")

    @staticmethod
    def _win_disable():
        import winreg
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Internet Settings"
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_ALL_ACCESS)
        winreg.SetValueEx(key, "ProxyEnable", 0, winreg.REG_DWORD, 0)
        winreg.CloseKey(key)

    @staticmethod
    def _mac_enable(host, port):
        output = subprocess.check_output(["networksetup", "-listallnetworkservices"]).decode()
        networks = [n.strip() for n in output.splitlines() if n.strip() and "*" not in n]
        for net in networks:
            subprocess.run(["networksetup", "-setwebproxy", net, host, str(port), "off"])
            subprocess.run(["networksetup", "-setsecurewebproxy", net, host, str(port), "off"])

    @staticmethod
    def _mac_disable():
        output = subprocess.check_output(["networksetup", "-listallnetworkservices"]).decode()
        networks = [n.strip() for n in output.splitlines() if n.strip() and "*" not in n]
        for net in networks:
            subprocess.run(["networksetup", "-setwebproxystate", net, "off"])
            subprocess.run(["networksetup", "-setsecurewebproxystate", net, "off"])

    @staticmethod
    def _linux_enable(host, port):
        subprocess.run(["gsettings", "set", "org.gnome.system.proxy", "mode", "manual"])
        subprocess.run(["gsettings", "set", "org.gnome.system.proxy.http", "host", host])
        subprocess.run(["gsettings", "set", "org.gnome.system.proxy.http", "port", str(port)])
        subprocess.run(["gsettings", "set", "org.gnome.system.proxy.https", "host", host])
        subprocess.run(["gsettings", "set", "org.gnome.system.proxy.https", "port", str(port)])

    @staticmethod
    def _linux_disable():
        subprocess.run(["gsettings", "set", "org.gnome.system.proxy", "mode", "none"])