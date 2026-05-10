import os
import subprocess
import threading
import shutil
import platform
import zipfile
import tarfile
import stat
from pathlib import Path
try:
    import requests
except ImportError:
    pass
from config import AppConfig

class TorManager:
    def __init__(self):
        self.process = None
        self.is_running = False
        self.lock = threading.Lock()
        self.tor_path = None
        self.pt_path = None

    def _get_platform_info(self):
        system = platform.system().lower()
        machine = platform.machine().lower()
        
        if system == "windows":
            return "win64" if machine in ["amd64", "x86_64"] else "win32"
        elif system == "darwin":
            return "osx64" if machine in ["amd64", "x86_64"] else "osx-arm64"
        else:
            if machine in ["amd64", "x86_64"]:
                return "linux64"
            elif machine in ["aarch64", "arm64"]:
                return "linux-aarch64"
            else:
                return "linux32"

    def _get_download_url(self):
        platform_code = self._get_platform_info()
        version = "0.4.8.10"
        
        urls = {
            "win64": f"https://dist.torproject.org/torbrowser/{version}/tor-expert-bundle-{platform_code}-{version}.zip",
            "win32": f"https://dist.torproject.org/torbrowser/{version}/tor-expert-bundle-{platform_code}-{version}.zip",
            "osx64": f"https://dist.torproject.org/torbrowser/{version}/tor-expert-bundle-{platform_code}-{version}.tar.gz",
            "osx-arm64": f"https://dist.torproject.org/torbrowser/{version}/tor-expert-bundle-{platform_code}-{version}.tar.gz",
            "linux64": f"https://dist.torproject.org/torbrowser/{version}/tor-expert-bundle-{platform_code}-{version}.tar.gz",
            "linux-aarch64": f"https://dist.torproject.org/torbrowser/{version}/tor-expert-bundle-{platform_code}-{version}.tar.gz",
            "linux32": f"https://dist.torproject.org/torbrowser/{version}/tor-expert-bundle-{platform_code}-{version}.tar.gz"
        }
        
        return urls.get(platform_code)

    def download_and_extract(self, progress_callback=None):
        os.makedirs(AppConfig.binary_dir, exist_ok=True)
        
        if platform.system() == "Windows":
            tor_exe = os.path.join(AppConfig.binary_dir, "tor.exe")
            pt_exe = os.path.join(AppConfig.binary_dir, "obfs4proxy.exe")
        else:
            tor_exe = os.path.join(AppConfig.binary_dir, "tor")
            pt_exe = os.path.join(AppConfig.binary_dir, "obfs4proxy")
        
        if os.path.exists(tor_exe) and os.path.exists(pt_exe):
            self.tor_path = tor_exe
            self.pt_path = pt_exe
            return
        
        url = self._get_download_url()
        if not url:
            raise RuntimeError(f"Неподдерживаемая платформа: {platform.system()} {platform.machine()}")
        
        try:
            import requests
        except ImportError:
            raise RuntimeError("Установите requests: pip install requests")
        
        temp_archive = os.path.join(AppConfig.runtime_dir, "tor_bundle.zip" if "zip" in url else "tor_bundle.tar.gz")
        
        if progress_callback:
            progress_callback("Downloading Tor...")
        
        response = requests.get(url, stream=True)
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        with open(temp_archive, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if progress_callback and total_size > 0:
                        progress_callback(f"Downloading: {downloaded * 100 // total_size}%")
        
        if progress_callback:
            progress_callback("Extracting...")
        
        if url.endswith('.zip'):
            with zipfile.ZipFile(temp_archive, 'r') as zip_ref:
                zip_ref.extractall(AppConfig.runtime_dir)
        else:
            with tarfile.open(temp_archive, 'r:gz') as tar_ref:
                tar_ref.extractall(AppConfig.runtime_dir)
        
        extracted_dir = None
        for item in os.listdir(AppConfig.runtime_dir):
            item_path = os.path.join(AppConfig.runtime_dir, item)
            if os.path.isdir(item_path) and 'tor' in item.lower():
                extracted_dir = item_path
                break
        
        if not extracted_dir:
            for root, dirs, files in os.walk(AppConfig.runtime_dir):
                if 'tor' in root.lower() and os.path.isdir(root):
                    extracted_dir = root
                    break
        
        if not extracted_dir:
            raise RuntimeError("Не удалось найти извлечённые файлы Tor")
        
        for root, dirs, files in os.walk(extracted_dir):
            for file in files:
                if file in ['tor', 'tor.exe']:
                    shutil.copy(os.path.join(root, file), tor_exe)
                elif file in ['obfs4proxy', 'obfs4proxy.exe']:
                    shutil.copy(os.path.join(root, file), pt_exe)
        
        if os.path.exists(temp_archive):
            os.remove(temp_archive)
        
        if not os.path.exists(tor_exe):
            raise RuntimeError("Файл tor не найден после извлечения")
        
        if not os.path.exists(pt_exe):
            pt_fallback = self._find_obfs4_in_extracted(extracted_dir)
            if pt_fallback:
                shutil.copy(pt_fallback, pt_exe)
            else:
                self._download_obfs4proxy(pt_exe)
        
        if platform.system() != "Windows":
            os.chmod(tor_exe, stat.S_IRWXU)
            if os.path.exists(pt_exe):
                os.chmod(pt_exe, stat.S_IRWXU)
        
        self.tor_path = tor_exe
        self.pt_path = pt_exe

    def _find_obfs4_in_extracted(self, base_dir):
        for root, dirs, files in os.walk(base_dir):
            for file in files:
                if 'obfs4' in file.lower():
                    return os.path.join(root, file)
        return None

    def _download_obfs4proxy(self, dest_path):
        try:
            import requests
            system = platform.system().lower()
            machine = platform.machine().lower()
            
            if system == "windows":
                fname = "obfs4proxy-windows-amd64.exe"
            elif system == "darwin":
                fname = "obfs4proxy-darwin-amd64" if machine in ["amd64", "x86_64"] else "obfs4proxy-darwin-arm64"
            else:
                fname = "obfs4proxy-linux-amd64" if machine in ["amd64", "x86_64"] else "obfs4proxy-linux-arm64"
            
            url = f"https://gitlab.torproject.org/tpo/anti-censorship/pluggable-transports/obfs4/-/releases/download/obfs4proxy-0.0.14/{fname}"
            response = requests.get(url)
            if response.status_code == 200:
                with open(dest_path, 'wb') as f:
                    f.write(response.content)
                if system != "windows":
                    os.chmod(dest_path, stat.S_IRWXU)
        except Exception:
            pass

    def prepare_runtime(self):
        os.makedirs(AppConfig.runtime_dir, exist_ok=True)
        os.makedirs(AppConfig.data_dir, exist_ok=True)
        if not self.tor_path:
            self.download_and_extract()

    def generate_config(self, bridge_type, bridge_list):
        with open(AppConfig.torrc_path, "w") as f:
            f.write(f"SocksPort {AppConfig.tor_socks_port} IsolateDestAddr IsolateDestPort\n")
            f.write(f"ControlPort {AppConfig.tor_control_port}\n")
            f.write(f"DataDirectory {AppConfig.data_dir}\n")
            f.write("ClientOnly 1\n")
            f.write("SafeLogging 0\n")
            f.write("GeoIPFile /dev/null\n")
            f.write("GeoIPv6File /dev/null\n")
            if bridge_type != "none" and bridge_list:
                f.write("UseBridges 1\n")
                if self.pt_path:
                    f.write(f"ClientTransportPlugin {bridge_type} exec {self.pt_path}\n")
                f.write("ClientUseIPv4 1\n")
                f.write("ClientUseIPv6 0\n")
                for bridge in bridge_list:
                    line = bridge if bridge.startswith("Bridge ") else f"Bridge {bridge}"
                    f.write(f"{line}\n")
            else:
                f.write("UseBridges 0\n")

    def start(self, bridge_type, bridge_list, progress_callback=None):
        with self.lock:
            if self.is_running:
                return
            self.prepare_runtime()
            self.generate_config(bridge_type, bridge_list)
            env = os.environ.copy()
            env["TOR_PT_STATE_LOCATION"] = AppConfig.runtime_dir
            self.process = subprocess.Popen(
                [self.tor_path, "-f", AppConfig.torrc_path],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
            )
            self.is_running = True

    def stop(self):
        with self.lock:
            if self.process and self.is_running:
                self.process.terminate()
                try:
                    self.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.process.kill()
                self.is_running = False