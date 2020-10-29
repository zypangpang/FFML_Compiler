import PyQt5.QtWidgets as QtWidgets

from gui.CodeEditor import CodeEditor
from gui.ui.centralwidget import Ui_CentralWidget


class CentralWidget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        #self.ui = Ui_CentralWidget()
        #self.ui.setupUi(self)
        #self.ui.msgEdit.setReadOnly(True)

        self.verticalLayout = QtWidgets.QVBoxLayout(self)
        self.codeEdit = CodeEditor(self)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setVerticalStretch(3)
        self.codeEdit.setSizePolicy(sizePolicy)
        self.verticalLayout.addWidget(self.codeEdit)

        self.msgEdit = QtWidgets.QTextEdit(self)
        self.msgEdit.setReadOnly(True)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setVerticalStretch(1)
        self.msgEdit.setSizePolicy(sizePolicy)
        self.verticalLayout.addWidget(self.msgEdit)

