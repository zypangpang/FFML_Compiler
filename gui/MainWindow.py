from PyQt5 import QtWidgets
from PyQt5.QtGui import QKeySequence
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QSizePolicy, QVBoxLayout

import gui.gui_constant as constant
from gui.CentralWidget import CentralWidget


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FFML Editor")
        self.__init_menubar()
        self.__init_toolbar()
        self.__init_statusbar()

        self.cwidget=CentralWidget()
        self.cwidget.setStyleSheet("background-color:green;")
        #self.cwidget.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)
        self.setCentralWidget(self.cwidget)

    def __init_menubar(self):
        self.menubar=self.menuBar()
        self.file_menu = QtWidgets.QMenu("&File", self)
        self.help_menu = QtWidgets.QMenu("&Help", self)
        self.menubar.addMenu(self.file_menu)
        self.menubar.addMenu(self.help_menu)

        #menu_titles = ['Open', 'Settings']
        self.file_menu.addAction("Settings", self.show_setting_dialog, QKeySequence(Qt.CTRL + Qt.ALT + Qt.Key_S))
        self.help_menu.addAction("Shortcuts", self.show_shortcuts, QKeySequence(Qt.CTRL + Qt.ALT + Qt.Key_K))
        self.help_menu.addAction("About", self.show_help)

    def __init_toolbar(self):
        self.toolbar=self.addToolBar("File")
        self.toolbar.addAction("Build")

    def __init_statusbar(self):
        self.statusbar=self.statusBar()
        self.statusbar.setFixedHeight(20)

    # private slots
    def show_setting_dialog(self):
        self.show_message("hello")

    def show_shortcuts(self):
        pass

    def show_help(self):
        msgBox = QtWidgets.QMessageBox()
        msgBox.setStyleSheet("QLabel{min-width: 600px;}")
        msgBox.setWindowTitle("Help")
        msgBox.setText(constant.HELP_TEXT)
        msgBox.exec()

    # Auxiliary functions ************************************#
    def show_message(self, msg):
        self.statusbar.showMessage(str(msg), 4000)


if __name__ == '__main__':
    app=QtWidgets.QApplication([])
    w=MainWindow()
    w.show()
    app.exec()

