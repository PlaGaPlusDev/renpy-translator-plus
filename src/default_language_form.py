import io
import os.path
import platform
from PySide6.QtCore import QCoreApplication
from PySide6.QtWidgets import QDialog, QFileDialog

from my_log import log_print
from default_language import Ui_DefaultLanguageDialog

default_language_template_path = 'default_langauge_template.txt'
out_default_lanugage_script_name = 'set_default_language_at_startup.rpy'


def set_default_language_at_startup(tl_name, target):
    if os.path.isfile(default_language_template_path):
        f = io.open(default_language_template_path, 'r', encoding='utf-8')
        _read = f.read()
        f.close()
        _read = _read.replace('{language}', tl_name)
        f = io.open(target, 'w', encoding='utf-8')
        f.write(_read)
        f.close()
        log_print('set default language at startup success!')


class MyDefaultLanguageForm(QDialog, Ui_DefaultLanguageDialog):
    def __init__(self, parent=None):
        super(MyDefaultLanguageForm, self).__init__(parent)
        self.setupUi(self)
        self.setFixedHeight(self.height())
        self.setFixedWidth(self.width())
        self.selectFileBtn.clicked.connect(self.select_file)
        self.selectFileText.textChanged.connect(self.on_text_changed)
        self.addEntranceCheckBox.clicked.connect(self.on_add_entrance_checkbox_clicked)

    def is_game_file(self, path):
        if not path or not os.path.isfile(path):
            return False
        if path.endswith('.exe') or path.endswith('.sh'):
            return True
        if platform.system() == 'Linux' and os.access(path, os.X_OK):
            return True
        return False

    def on_add_entrance_checkbox_clicked(self):
        if self.addEntranceCheckBox.isChecked():
            target = self.get_target()
            if target is not None:
                tl_name = self.tlNameText.toPlainText()
                set_default_language_at_startup(tl_name, target)
        else:
            target = self.get_target()
            if target is not None:
                if os.path.isfile(target):
                    os.remove(target)
                if os.path.isfile(target + 'c'):
                    os.remove(target + 'c')
                log_print('remove default language success!')

    def get_target(self):
        path = self.selectFileText.toPlainText()
        path = path.replace('file:///', '')
        if os.path.isfile(path):
            if self.is_game_file(path):
                target = os.path.join(os.path.dirname(path), 'game')
                if os.path.isdir(target):
                    target = os.path.join(target, out_default_lanugage_script_name)
                    return target
        return None

    def on_text_changed(self):
        target = self.get_target()
        if target is not None and os.path.isfile(target):
            self.addEntranceCheckBox.setChecked(True)
        else:
            self.addEntranceCheckBox.setChecked(False)

    def select_file(self):
        file, filetype = QFileDialog.getOpenFileName(self,
                                                     QCoreApplication.translate('DefaultLanguageDialog',
                                                                                'select the game file you want to set default language at startup',
                                                                                None),
                                                     '',
                                                     "Game Files (*.exe *.sh);;All Files (*)")
        self.selectFileText.setText(file)
