"""
Build script: packages blog_updater.py into a standalone EXE.
Run: python build_exe.py
"""
import subprocess
import sys
import os

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    script_path = os.path.join(script_dir, "blog_updater.py")

    # Ensure PyInstaller is installed
    try:
        import PyInstaller
    except ImportError:
        print("PyInstaller not found, installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",           # single EXE
        "--windowed",          # no console window
        "--name", "博客自动更新工具",
        "--icon", os.path.join(script_dir, "icon.ico") if os.path.exists(os.path.join(script_dir, "icon.ico")) else "",
        "--clean",
        "--noconfirm",
        script_path,
    ]

    # Remove empty icon arg
    if not os.path.exists(os.path.join(script_dir, "icon.ico")):
        cmd = [c for c in cmd if c != "--icon" and os.path.basename(c) != "icon.ico"]

    print("Building EXE...")
    subprocess.check_call(cmd)
    print("\nDone! EXE is at: dist/博客自动更新工具.exe")


if __name__ == "__main__":
    main()
