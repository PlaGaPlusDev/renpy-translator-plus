import os
import platform
import subprocess

def get_font_path(font_name):
    if platform.system() == "Windows":
        import winreg
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows NT\CurrentVersion\Fonts")
            for i in range(0, winreg.QueryInfoKey(key)[1]):
                value = winreg.EnumValue(key, i)
                if font_name in value[0]:
                    return os.path.join(os.environ.get('SystemRoot', 'C:\\Windows'), 'Fonts', value[1])
        except Exception:
            pass
    return None


def get_default_font_name():
    if platform.system() == "Windows":
        try:
            import win32gui
            import win32con
            nonclient_metrics = win32gui.SystemParametersInfo(win32con.SPI_GETNONCLIENTMETRICS)
            font_name = nonclient_metrics['lfMessageFont'].lfFaceName
            return font_name
        except Exception:
            pass
    return "Sans"


def get_default_font_path():
    if platform.system() == "Windows":
        return get_font_path(get_default_font_name())
    elif platform.system() == "Linux":
        # Try to use fc-match to find a default font path
        try:
            result = subprocess.run(['fc-match', '-f', '%{file}', 'sans-serif'],
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass
        # Fallback common locations
        fallbacks = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/TTF/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
        ]
        for f in fallbacks:
            if os.path.exists(f):
                return f
    return None
