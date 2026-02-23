import os
import platform
import subprocess
import sys

def get_platform():
    return platform.system()

def is_windows():
    return get_platform() == "Windows"

def is_linux():
    return get_platform() == "Linux"

def open_directory_and_select_file(file_path):
    """Opens the file manager and selects the given file."""
    if is_windows():
        subprocess.run(["explorer", "/select,", os.path.normpath(file_path)])
    elif is_linux():
        # Linux doesn't have a universal "select file" in file manager command
        # but we can open the directory. Some file managers support it, but
        # xdg-open just opens the folder.
        directory = os.path.dirname(file_path)
        subprocess.run(["xdg-open", directory])
    else:
        # Fallback for macOS or others
        if platform.system() == "Darwin":
            subprocess.run(["open", "-R", file_path])
        else:
            directory = os.path.dirname(file_path)
            if os.path.exists(directory):
                if is_windows():
                    os.startfile(directory)
                else:
                    subprocess.run(["xdg-open", directory])

def kill_process(pid):
    """Kills a process and its children."""
    if is_windows():
        subprocess.call(['taskkill.exe', '/F', '/T', '/PID', str(pid)],
                        creationflags=0x08000000) # CREATE_NO_WINDOW
    else:
        try:
            import signal
            os.kill(int(pid), signal.SIGKILL)
        except Exception:
            subprocess.call(['kill', '-9', str(pid)])

def get_system_language():
    """Returns the system language code."""
    if is_windows():
        try:
            import ctypes
            dll_h = ctypes.windll.kernel32
            return hex(dll_h.GetSystemDefaultUILanguage())
        except Exception:
            return None
    else:
        # On Linux, use locale
        import locale
        loc = locale.getdefaultlocale()[0] # e.g. 'en_US'
        if not loc:
            return None
        # Map some common ones to what the app expects if needed
        # The app uses hex strings like '0x804'
        language_map = {
            'ar': '401',
            'bn': '0x445',
            'zh': '0x804',
            'fr': '0x40c',
            'de': '0x407',
            'hi': '0x439',
            'ja': '0x411',
            'ko': '0x412',
            'pt': '0x816',
            'ru': '0x419',
            'es': '0x40a',
            'tr': '0x41f',
            'ur': '0x843'
        }
        prefix = loc.split('_')[0].lower()
        return language_map.get(prefix)

def set_window_on_top(hwnd=None, window=None):
    """
    Tries to set a window on top.
    If hwnd is provided, it uses Windows API.
    If window (QWidget) is provided, it uses Qt methods.
    """
    if window:
        window.showNormal()
        window.raise_()
        window.activateWindow()

    if is_windows() and hwnd:
        try:
            import win32gui
            import win32con
            win32gui.ShowWindow(hwnd, win32con.SW_NORMAL)
            win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, 0, 0, 0, 0,
                                  win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)
            win32gui.SetWindowPos(hwnd, win32con.HWND_NOTOPMOST, 0, 0, 0, 0,
                                  win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)
            win32gui.SetForegroundWindow(hwnd)
            win32gui.SetActiveWindow(hwnd)
        except Exception:
            pass
    # Linux support for external windows is complex and depends on X11/Wayland.
    # We omit it for now or use wmctrl if available.

def get_subprocess_creation_flags():
    """Returns creation flags for subprocess based on OS."""
    if is_windows():
        return 0x08000000 # CREATE_NO_WINDOW
    return 0

def open_file_with_text_editor(filepath):
    """Opens a file with the default text editor."""
    if is_windows():
        subprocess.Popen(['notepad.exe', filepath])
    elif is_linux():
        # Try some common editors or xdg-open
        try:
            subprocess.Popen(['xdg-open', filepath])
        except Exception:
            for editor in ['gedit', 'kate', 'nano', 'vi']:
                try:
                    subprocess.Popen([editor, filepath])
                    break
                except Exception:
                    continue
    else:
        if platform.system() == "Darwin":
            subprocess.Popen(['open', filepath])
        else:
            try:
                subprocess.Popen(['xdg-open', filepath])
            except Exception:
                pass
