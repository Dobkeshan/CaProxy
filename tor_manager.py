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
    requests = None

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
        arch = machine
        
        if system == "windows":
            if machine in ["amd64", "x86_64", "AMD64"]:
                return "windows-x86_64", ".zip"
            else:
                return "windows-i686", ".zip"
        elif system == "darwin":
            if machine in ["arm64", "aarch64"]:
                return "osx-arm64", ".tar.gz"
            else:
                return "osx-x86_64", ".tar.gz"
        else:
            if machine in ["amd64", "x86_64"]:
                return "linux-x86_64", ".tar.xz"
            elif machine in ["aarch64", "arm64"]:
                return "linux-aarch64", ".tar.xz"
            elif machine in ["i386", "i686"]:
                return "linux-i686", ".tar.xz"
            else:
                return "linux-x86_64", ".tar.xz"

    def _get_download_url(self):
        platform_code, ext = self._get_platform_info()
        
        urls = {
            "windows-x86_64": "https://www.torproject.org/dist/torbrowser/13.5.2/tor-browser-windows-x86_64-13.5.2.exe",
            "windows-i686": "https://www.torproject.org/dist/torbrowser/13.5.2/tor-browser-windows-i686-13.5.2.exe",
            "osx-arm64": "https://www.torproject.org/dist/torbrowser/13.5.2/tor-browser-macos-arm64-13.5.2.dmg",
            "osx-x86_64": "https://www.torproject.org/dist/torbrowser/13.5.2/tor-browser-macos-x86_64-13.5.2.dmg",
            "linux-x86_64": "https://www.torproject.org/dist/torbrowser/13.5.2/tor-browser-linux-x86_64-13.5.2.tar.xz",
            "linux-aarch64": "https://www.torproject.org/dist/torbrowser/13.5.2/tor-browser-linux-arm64-13.5.2.tar.xz",
            "linux-i686": "https://www.torproject.org/dist/torbrowser/13.5.2/tor-browser-linux-i686-13.5.2.tar.xz"
        }
        
        return urls.get(platform_code), ext

    def download_and_extract(self, progress_callback=None):
        os.makedirs(AppConfig.binary_dir, exist_ok=True)
        os.makedirs(AppConfig.data_dir, exist_ok=True)
        
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
        
        if requests is None:
            raise RuntimeError("Установите requests: pip install requests")
        
        url, ext = self._get_download_url()
        if not url:
            raise RuntimeError(f"Неподдерживаемая платформа: {platform.system()} {platform.machine()}")
        
        temp_file = os.path.join(AppConfig.runtime_dir, f"tor_download{ext}")
        extract_dir = os.path.join(AppConfig.runtime_dir, "tor_extracted")
        
        if progress_callback:
            progress_callback("Downloading Tor Browser...")
        
        try:
            response = requests.get(url, stream=True, timeout=300)
            response.raise_for_status()
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(temp_file, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if progress_callback and total_size > 0:
                            pct = downloaded * 100 // total_size
                            progress_callback(f"Downloaded: {pct}%")
        except Exception as e:
            raise RuntimeError(f"Failed to download Tor: {str(e)}")
        
        if progress_callback:
            progress_callback("Extracting Tor...")
        
        try:
            if ext == ".zip":
                self._extract_zip(temp_file, extract_dir)
            elif ext == ".tar.xz":
                self._extract_tar_xz(temp_file, extract_dir)
            elif ext == ".exe":
                self._extract_from_exe(temp_file, extract_dir)
            elif ext == ".dmg":
                raise RuntimeError("macOS DMG требует ручной установки. Используйте Homebrew: brew install tor")
            
            self._copy_tor_files(extract_dir, tor_exe, pt_exe)
            
            if os.path.exists(temp_file):
                os.remove(temp_file)
            if os.path.exists(extract_dir):
                shutil.rmtree(extract_dir)
                
        except Exception as e:
            raise RuntimeError(f"Failed to extract Tor: {str(e)}")
        
        if not os.path.exists(tor_exe):
            raise RuntimeError("Tor executable not found after extraction")
        
        self.tor_path = tor_exe
        self.pt_path = pt_exe if os.path.exists(pt_exe) else None

    def _extract_zip(self, archive, dest):
        with zipfile.ZipFile(archive, 'r') as z:
            z.extractall(dest)

    def _extract_tar_xz(self, archive, dest):
        import lzma
        with lzma.open(archive, 'rb') as f:
            tar_content = f.read()
        
        import io
        with tarfile.open(fileobj=io.BytesIO(tar_content), mode='r') as tar:
            tar.extractall(dest)

    def _extract_from_exe(self, exe_file, dest):
        import subprocess
        seven_zip = shutil.which("7z") or shutil.which("7za")
        if seven_zip:
            subprocess.run([seven_zip, "x", exe_file, f"-o{dest}", "-y"], 
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            with zipfile.ZipFile(exe_file, 'r') as z:
                z.extractall(dest)

    def _copy_tor_files(self, source_dir, tor_dest, pt_dest):
        tor_found = False
        pt_found = False
        
        for root, dirs, files in os.walk(source_dir):
            for file in files:
                if file in ['tor.exe', 'tor'] and not tor_found:
                    full_path = os.path.join(root, file)
                    if self._is_valid_executable(full_path):
                        shutil.copy(full_path, tor_dest)
                        tor_found = True
                
                if 'obfs4' in file.lower() and not pt_found:
                    full_path = os.path.join(root, file)
                    if self._is_valid_executable(full_path):
                        shutil.copy(full_path, pt_dest)
                        pt_found = True
                
                if file.lower() == 'tor.exe' and 'Browser' not in root and not tor_found:
                    full_path = os.path.join(root, file)
                    shutil.copy(full_path, tor_dest)
                    tor_found = True
        
        if not tor_found:
            for root, dirs, files in os.walk(source_dir):
                if 'Tor' in root or 'tor' in root:
                    for file in files:
                        if file in ['tor.exe', 'tor']:
                            full_path = os.path.join(root, file)
                            shutil.copy(full_path, tor_dest)
                            tor_found = True
                            break
                if tor_found:
                    break
        
        if not pt_found:
            self._download_obfs4proxy(pt_dest)

    def _is_valid_executable(self, path):
        try:
            if platform.system() != "Windows":
                result = subprocess.run([path, "--version"], 
                                       capture_output=True, timeout=5)
                return result.returncode == 0
            return True
        except:
            return False

    def _download_obfs4proxy(self, dest_path):
        try:
            system = platform.system().lower()
            machine = platform.machine().lower()
            
            if system == "windows":
                fname = "obfs4proxy-windows-amd64.exe"
            elif system == "darwin":
                fname = "obfs4proxy-darwin-amd64" if machine in ["amd64", "x86_64"] else "obfs4proxy-darwin-arm64"
            else:
                fname = "obfs4proxy-linux-amd64" if machine in ["amd64", "x86_64"] else "obfs4proxy-linux-arm64"
            
            url = f"https://gitlab.torproject.org/tpo/anti-censorship/pluggable-transports/obfs4/-/releases/download/obfs4proxy-0.0.14/{fname}"
            response = requests.get(url, timeout=60)
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
                if self.pt_path and os.path.exists(self.pt_path):
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