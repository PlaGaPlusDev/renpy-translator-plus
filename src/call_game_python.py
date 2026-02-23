import io
import os
import platform
import shutil
import subprocess


def is_64_bit():
    return platform.architecture()[0] == '64bit'


def get_python_path_from_game_dir(game_dir):
    lib_list_64 = ['windows-x86_64', 'py2-windows-x86_64', 'py3-windows-x86_64', 'linux-x86_64', 'linux-i686']
    lib_list_86 = ['windows-i686', 'py2-windows-i686', 'py3-windows-i686', 'linux-i686']
    python_path = None

    executable_names = ['python.exe', 'python']

    search_list = lib_list_64 if is_64_bit() else lib_list_86
    if is_64_bit():
        search_list.extend(lib_list_86)

    for lib_dir in search_list:
        for exe_name in executable_names:
            target = os.path.join(game_dir, 'lib', lib_dir, exe_name)
            if os.path.isfile(target):
                return target
    return None


def get_python_path_from_game_path(game_path):
    game_dir = os.path.dirname(game_path) + '/'
    return get_python_path_from_game_dir(game_dir)


def is_python2_with_python_dir(python_dir):
    paths = os.walk(python_dir, topdown=False)
    is_py2 = False
    for path, dir_lst, file_lst in paths:
        for file_name in file_lst:
            i = os.path.join(path, file_name)
            if 'python2' in i or 'py2' in i:
                is_py2 = True
                break
    return is_py2


def is_python2_from_game_dir(game_dir):
    try:
        python_dir = os.path.dirname(get_python_path_from_game_dir(game_dir))
    except Exception:
        return True
    return is_python2_with_python_dir(python_dir)


def is_python2_from_game_path(game_path):
    try:
        python_dir = os.path.dirname(get_python_path_from_game_path(game_path))
    except Exception:
        return True
    return is_python2_with_python_dir(python_dir)


def get_py_path(game_path):
    base_name = os.path.splitext(game_path)[0]
    return base_name + '.py'


def copy_files_under_directory_to_directory(src_dir, desc_dir):
    shutil.copytree(src_dir, desc_dir, dirs_exist_ok=True)


def get_game_path_from_game_dir(game_dir):
    extensions = ['.exe', '.sh']
    for item in os.listdir(game_dir):
        full_path = os.path.join(game_dir, item)
        if os.path.isfile(full_path):
            lower_item = item.lower()
            for ext in extensions:
                if lower_item.endswith(ext):
                    # For Ren'Py, there is usually a .py file with the same name as the executable
                    py_file = full_path[:-len(ext)] + '.py'
                    if os.path.isfile(py_file):
                        return full_path
            # On Linux, sometimes the binary has no extension and is executable
            if platform.system() == "Linux" and os.access(full_path, os.X_OK):
                py_file = full_path + '.py'
                if os.path.isfile(py_file):
                    return full_path
    return None
