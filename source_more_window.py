from PyQt5 import QtWidgets as qtw

from .more_window import Ui_MoreDialog

class SourceMoreWindow(qtw.QWidget, Ui_MoreDialog):
    def __init__(self):
        super().__init__()
        
        print('instance class created !')