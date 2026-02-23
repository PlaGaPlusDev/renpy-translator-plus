import os.path
import shutil
import platform

from PySide6.QtCore import QCoreApplication
from PySide6.QtWidgets import QDialog, QFileDialog

from add_change_langauge_entrance import Ui_AddEntranceDialog
from my_log import log_print

hook_script = 'hook_add_change_language_entrance.rpy'

class MyAddChangeLanguageEntranceForm(QDialog, Ui_AddEntranceDialog):
    def __init__(self, parent=None):
        super(MyAddChangeLanguageEntranceForm, self).__init__(parent)
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
                shutil.copyfile(hook_script, target)
                log_print('add entrance success!')
        else:
            target = self.get_target()
            if target is not None:
                if os.path.isfile(target):
                    os.remove(target)
                if os.path.isfile(target + 'c'):
                    os.remove(target + 'c')
                log_print('remove entrance success!')

    def get_target(self):
        path = self.selectFileText.toPlainText()
        path = path.replace('file:///', '')
        if self.is_game_file(path):
            target = os.path.join(os.path.dirname(path), 'game')
            if os.path.isdir(target):
                target = os.path.join(target, hook_script)
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
                                                     QCoreApplication.translate('AddEntranceDialog',
                                                                                'select the game file you want to add entrance',
                                                                                None),
                                                     '',
                                                     "Game Files (*.exe *.sh);;All Files (*)")
        self.selectFileText.setText(file)
