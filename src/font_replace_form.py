import os
import subprocess
import threading
import traceback

from PySide6.QtCore import QCoreApplication, QThread, Signal
from PySide6.QtWidgets import QDialog, QFileDialog

from font_replace import Ui_FontReplaceDialog
from my_log import log_print
import my_log
from renpy_fonts import GenGuiFonts
from os_util import get_subprocess_creation_flags, open_file_with_text_editor


class replaceFontThread(threading.Thread):
    def __init__(self, select_dir, font_path, is_rtl):
        threading.Thread.__init__(self)
        self.select_dir = select_dir
        self.font_path = font_path
        self.is_rtl = is_rtl

    def run(self):
        try:
            log_print('start replace font...')
            GenGuiFonts(self.select_dir, self.font_path, self.is_rtl)
            log_print('replace font complete!')
        except Exception as e:
            msg = traceback.format_exc()
            log_print(msg)


class MyFontReplaceForm(QDialog, Ui_FontReplaceDialog):
    def __init__(self, parent=None):
        super(MyFontReplaceForm, self).__init__(parent)
        self.setupUi(self)
        self.setFixedHeight(self.height())
        self.setFixedWidth(self.width())
        self.selectDirBtn.clicked.connect(self.select_directory)
        self.selectFontBtn.clicked.connect(self.select_font)
        self.replaceBtn.clicked.connect(self.replace_font)
        self.openGuiBtn.clicked.connect(self.open_gui_rpy)
        self.replace_font_thread = None
        _thread = threading.Thread(target=self.update)
        _thread.daemon = True
        _thread.start()

    def select_directory(self):
        directory = QFileDialog.getExistingDirectory(self, QCoreApplication.translate('MainWindow',
                                                                                      'select the directory you want to translate',
                                                                                      None))
        self.selectDirText.setText(directory)

    def select_font(self):
        file, filetype = QFileDialog.getOpenFileName(self,
                                                     QCoreApplication.translate("FontReplaceDialog",
                                                                                "select the file font which supports the translated language",
                                                                                None),
                                                     '',
                                                     "Font Files (*.ttf || *.otf);;All Files (*)")
        self.selectFontText.setText(file)

    def replace_font(self):
        select_dir = self.selectDirText.toPlainText()
        select_dir = select_dir.replace('file:///', '')
        if len(select_dir) > 0:
            if select_dir[len(select_dir) - 1] != '/' and select_dir[len(select_dir) - 1] != '\\':
                select_dir = select_dir + '/'
            font_path = self.selectFontText.toPlainText()
            font_path = font_path.replace('file:///', '')
            t = replaceFontThread(select_dir, font_path, self.rtlCheckBox.isChecked())
            self.replace_font_thread = t
            t.start()
            self.setDisabled(True)
            self.replaceBtn.setText(QCoreApplication.translate('FontReplaceDialog', 'is replacing font...', None))

    def open_gui_rpy(self):
        select_dir = self.selectDirText.toPlainText()
        select_dir = select_dir.replace('file:///', '')
        if len(select_dir) > 0:
            if select_dir[len(select_dir) - 1] != '/' and select_dir[len(select_dir) - 1] != '\\':
                select_dir = select_dir + '/'
            open_file_with_text_editor(os.path.join(select_dir, 'gui.rpy'))

    def update(self):
        thread = self.UpdateThread()
        thread.update_date.connect(self.update_progress)
        while True:
            thread.start()
            time.sleep(0.5)

    def update_progress(self):
        try:
            if self.replace_font_thread is not None:
                if not self.replace_font_thread.is_alive():
                    self.replaceBtn.setText(QCoreApplication.translate('FontReplaceDialog', 'replace font', None))
                    self.setEnabled(True)
                    self.replace_font_thread = None

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
