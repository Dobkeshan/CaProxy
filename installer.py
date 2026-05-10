import subprocess
import sys

def install_requirements():
    try:
        import requests
        import PyQt6
        print("All dependencies installed!")
        return
    except ImportError:
        pass
    
    print("Installing dependencies...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests", "PyQt6"])
    print("Done!")

if __name__ == "__main__":
    install_requirements()