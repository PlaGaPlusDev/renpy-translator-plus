import _thread
import io
import os
import shutil
import subprocess
import threading
import time
import traceback
import platform

try:
    import win32con
    import win32gui
except ImportError:
    win32con = None
    win32gui = None

from PySide6.QtCore import QThread, Signal, QCoreApplication
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QDialog, QFileDialog, QMessageBox

from my_log import log_print
import my_log
from renpy_fonts import GenGuiFonts
from game_unpacker import Ui_GameUnpackerDialog
from call_game_python import *
from unzipdir import zip_dir, unzip_file
from os_util import get_subprocess_creation_flags, kill_process, set_window_on_top as os_set_window_on_top

hook_script = 'hook_unrpa.rpy'
finish_flag = '/unpack.finish'
pid_flag = '/game.pid'


def set_window_on_top(hwnd):
    os_set_window_on_top(hwnd=hwnd)


def get_unrpyc_command(game_path):
    python_path = get_python_path_from_game_path(game_path)
    game_dir = os.path.dirname(game_path)
    unrpyc_path = os.path.join(game_dir, 'unrpyc.py')
    command = '"' + python_path + '" -O "' + unrpyc_path + '" "' + game_dir + '"'
    return command


def clean_unrpyc(dir):
    try:
        shutil.rmtree(os.path.join(dir, 'renpy', 'common'))
    except FileNotFoundError:
        pass
    try:
        shutil.rmtree(os.path.join(dir, '__pycache__'))
    except FileNotFoundError:
        pass
    try:
        shutil.rmtree(os.path.join(dir, 'decompiler'))
    except FileNotFoundError:
        pass

    unzip_file(os.path.join(dir, 'common_backup.zip'), os.path.join(dir, 'renpy', 'common'))
    os.remove(os.path.join(dir, 'common_backup.zip'))
    os.remove(os.path.join(dir, 'deobfuscate.py'))
    os.remove(os.path.join(dir, 'unrpyc.py'))
    if os.path.isfile(os.path.join(dir, 'unrpyc.pyo')):
        os.remove(os.path.join(dir, 'unrpyc.pyo'))
    if os.path.isfile(os.path.join(dir, 'deobfuscate.pyo')):
        os.remove(os.path.join(dir, 'deobfuscate.pyo'))


class unrpycThread(threading.Thread):
    def __init__(self, dir, path, p, is_over_write, is_auto_close):
        threading.Thread.__init__(self)
        self.dir = dir
        self.p = p
        self.path = path
        self.is_over_write = is_over_write
        self.is_auto_close = is_auto_close

    def run(self):
        try:
            if self.is_auto_close and self.p is not None:
                kill_process(self.p)
            zip_dir(os.path.join(self.dir, 'renpy', 'common'), os.path.join(self.dir, 'common_backup.zip'))
            copy_files_under_directory_to_directory(os.path.join(os.getcwd(), 'resource', 'unrpyc_python'), self.dir)
            command = get_unrpyc_command(self.path)
            if self.is_over_write:
                command = command + ' --clobber'
            log_print(command)
            if os.path.isfile('unrpyc.complete'):
                os.remove('unrpyc.complete')
            p = subprocess.Popen(command, shell=True, stdout=my_log.f, stderr=my_log.f,
                                 creationflags=get_subprocess_creation_flags(), text=True, encoding='utf-8')
            p.wait()
            while True:
                if os.path.isfile('unrpyc.complete'):
                    os.remove('unrpyc.complete')
                    break
            clean_unrpyc(self.dir)
            io.open(os.path.join(self.dir, 'unren.finish'), mode='w', encoding='utf-8').close()
        except Exception as e:
            msg = traceback.format_exc()
            log_print(msg)


class MyGameUnpackerForm(QDialog, Ui_GameUnpackerDialog):
    def __init__(self, parent=None):
        super(MyGameUnpackerForm, self).__init__(parent)
        self.setupUi(self)
        self.setWindowIcon(QIcon('main.ico'))
        self.setFixedHeight(self.height())
        self.setFixedWidth(self.width())
        self.selectFileBtn.clicked.connect(self.select_file)
        self.unpackBtn.clicked.connect(self.unpack)
        if win32gui:
            self.hwnd = win32gui.GetForegroundWindow()
        else:
            self.hwnd = None
        self.parent_hwnd = None
        self.path = None
        self.dir = None
        f = io.open(hook_script, mode='r', encoding='utf-8')
        _read_lines = f.readlines()
        f.close()
        max_thread_num = 12
        is_script_only = True
        is_skip_if_exist = True
        for idx, _line in enumerate(_read_lines):
            if _line.startswith('    MAX_UNPACK_THREADS = '):
                max_thread_num = _line[len('    MAX_UNPACK_THREADS = '):].strip().strip('\n')
                break
        for idx, _line in enumerate(_read_lines):
            if _line.startswith('    SCRIPT_ONLY = '):
                is_script_only = _line[len('    SCRIPT_ONLY = '):].strip().strip('\n') == 'True'
                break
        for idx, _line in enumerate(_read_lines):
            if _line.startswith('    SKIP_IF_EXIST = '):
                is_skip_if_exist = _line[len('    SKIP_IF_EXIST = '):].strip().strip('\n') == 'True'
                break
        self.maxThreadsLineEdit.setText(str(max_thread_num))
        self.unpackAllCheckBox.setChecked(not is_script_only)
        self.overwriteCheckBox.setChecked(not is_skip_if_exist)
        _thread.start_new_thread(self.update, ())

    def closeEvent(self, event):
        self.parent.widget.show()
        self.parent.menubar.show()
        self.parent.versionLabel.show()
        self.parent.actionunpack_game.triggered.connect(lambda: self.parent.unpack_game())
        self.parent.showNormal()
        self.hide()
        event.ignore()
        return

    def select_file(self):
        file, filetype = QFileDialog.getOpenFileName(self,
                                                     QCoreApplication.translate('GameUnpackerDialog',
                                                                                'select the game file you want to unpack',
                                                                                None),
                                                     '',
                                                     "Game Files (*.exe *.sh);;All Files (*)")
        self.selectFileText.setText(file)

    def is_game_file(self, path):
        if not path or not os.path.isfile(path):
            return False
        if path.endswith('.exe') or path.endswith('.sh'):
            return True
        if platform.system() == 'Linux' and os.access(path, os.X_OK):
            return True
        return False

    def unpack(self):
        path = self.selectFileText.toPlainText()
        path = path.replace('file:///', '')
        if self.is_game_file(path):
            dir = os.path.dirname(path)
            # shutil.copyfile(hook_script, dir + '/game/' + hook_script)
            f = io.open(hook_script, mode='r', encoding='utf-8')
            _read_lines = f.readlines()
            f.close()
            for idx, _line in enumerate(_read_lines):
                if _line.startswith('    MAX_UNPACK_THREADS = '):
                    _read_lines[idx] = f'    MAX_UNPACK_THREADS = {self.maxThreadsLineEdit.text()}\n'
                    break
            for idx, _line in enumerate(_read_lines):
                if _line.startswith('    SCRIPT_ONLY = '):
                    _read_lines[idx] = f'    SCRIPT_ONLY = {str(not self.unpackAllCheckBox.isChecked())}\n'
                    break
            for idx, _line in enumerate(_read_lines):
                if _line.startswith('    SKIP_IF_EXIST = '):
                    _read_lines[idx] = f'    SKIP_IF_EXIST = {str(not self.overwriteCheckBox.isChecked())}\n'
                    break

            f = io.open(os.path.join(dir, 'game', hook_script), mode='w', encoding='utf-8')
            f.writelines(_read_lines)
            f.close()
            f = io.open(hook_script, mode='w', encoding='utf-8')
            f.writelines(_read_lines)
            f.close()
            command = '"' + path + '"'
            self.path = path
            f = io.open(os.path.join(dir, finish_flag.lstrip('/')), 'w')
            f.write('waiting')
            f.close()
            self.setDisabled(True)
            log_print('start unpacking...')
            p = subprocess.Popen(command, shell=True, stdout=my_log.f, stderr=my_log.f,
                                 creationflags=get_subprocess_creation_flags(), text=True, cwd=dir, encoding='utf-8')
            self.p = p
            if win32gui:
                self.hwnd = win32gui.GetForegroundWindow()
            self.hide()
            self.parent.showNormal()
            self.parent.raise_()
            if win32gui:
                self.parent_hwnd = win32gui.GetForegroundWindow()

    def update(self):
        thread = self.UpdateThread()
        thread.update_date.connect(self.update_progress)
        while True:
            thread.start()
            time.sleep(0.5)

    def update_progress(self):
        try:
            if self.dir is not None:
                if os.path.isfile(os.path.join(self.dir, 'unren.finish')):
                    os.remove(os.path.join(self.dir, 'unren.finish'))
                    self.show()
                    self.raise_()
                    set_window_on_top(self.hwnd)
                    self.dir = None
                    self.setEnabled(True)
                    log_print('unpack complete!')
            if self.path is None:
                return
            dir = os.path.dirname(self.path)
            target = os.path.join(dir, finish_flag.lstrip('/'))
            if not os.path.isfile(target):
                hook_script_path = os.path.join(dir, 'game', hook_script)
                if os.path.isfile(hook_script_path):
                    os.remove(hook_script_path)
                if os.path.isfile(hook_script_path + 'c'):
                    os.remove(hook_script_path + 'c')
                set_window_on_top(self.parent_hwnd)
                target = os.path.join(dir, pid_flag.lstrip('/'))
                pid = None
                if os.path.isfile(target):
                    f = io.open(target, 'r', encoding='utf-8')
                    pid = f.read()
                    f.close()
                    os.remove(target)
                t = unrpycThread(dir, self.path, pid, self.overwriteCheckBox.isChecked(), self.autoCheckBox.isChecked())
                t.start()
                self.path = None
                self.dir = dir
        except Exception:
            msg = traceback.format_exc()
            log_print(msg)

    class UpdateThread(QThread):
        update_date = Signal()

        def __init__(self):
            super().__init__()

        def __del__(self):
            self.wait()

        def run(self):
            self.update_date.emit()
