import PyQt5.QtWidgets as QtWidgets

from gui.CodeEditor import CodeEditor
from gui.ui.centralwidget import Ui_CentralWidget


class CentralWidget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        #self.ui = Ui_CentralWidget()
        #self.ui.setupUi(self)
        #self.ui.msgEdit.setReadOnly(True)

        self.setObjectName("CentralWidget")
        #CentralWidget.resize(750, 611)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.sizePolicy().hasHeightForWidth())
        self.setSizePolicy(sizePolicy)

        self.verticalLayout = QtWidgets.QVBoxLayout(self)
        #self.verticalLayout.setObjectName("verticalLayout")
        self.codeEdit = CodeEditor(self)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(3)
        sizePolicy.setHeightForWidth(self.codeEdit.sizePolicy().hasHeightForWidth())
        self.codeEdit.setSizePolicy(sizePolicy)
        #self.codeEdit.setObjectName("codeEdit")
        self.verticalLayout.addWidget(self.codeEdit)
        self.msgEdit = QtWidgets.QTextEdit(self)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(1)
        sizePolicy.setHeightForWidth(self.msgEdit.sizePolicy().hasHeightForWidth())
        self.msgEdit.setSizePolicy(sizePolicy)
        #self.msgEdit.setMaximumSize(QtCore.QSize(16777215, 16777215))
        #self.msgEdit.setObjectName("msgEdit")
        self.verticalLayout.addWidget(self.msgEdit)

