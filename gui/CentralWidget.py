import PyQt5.QtWidgets as QtWidgets

from gui.ui.centralwidget import Ui_CentralWidget


class CentralWidget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.ui = Ui_CentralWidget()
        self.ui.setupUi(self)
        self.ui.msgEdit.setReadOnly(True)
