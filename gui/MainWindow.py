from PyQt5 import QtWidgets
from PyQt5.QtGui import QKeySequence, QIcon, QTextDocument
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QSizePolicy, QVBoxLayout
import gui.resources_gen.qtresource

from constants import GUI
import gui.gui_constant as constant
from gui.CentralWidget import CentralWidget
from gui.utils import clear_log,get_log_list

from main import Main

class MainWindow(QtWidgets.QMainWindow):
    translator=Main()
    def __init__(self):
        super().__init__()
        GUI[0]=True
        self.setWindowTitle("FFML Editor")
        self.__init_menubar()
        self.__init_toolbar()
        self.__init_statusbar()
        self.__init_cwidget()
        self.__init_document()


    def __init_cwidget(self):
        self.cwidget = CentralWidget()
        # self.cwidget.setStyleSheet("background-color:green;")
        # self.cwidget.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)
        self.msg_edit=self.cwidget.ui.msgEdit
        self.code_edit=self.cwidget.ui.codeEdit
        self.setCentralWidget(self.cwidget)

    def __init_document(self):
        self.code_doc=QTextDocument("",self)
        self.code_edit.setDocument(self.code_doc)


    def __init_menubar(self):
        self.menubar=self.menuBar()
        self.file_menu = QtWidgets.QMenu("&File", self)
        self.help_menu = QtWidgets.QMenu("&Help", self)
        self.build_menu = QtWidgets.QMenu("&Build", self)
        self.menubar.addMenu(self.file_menu)
        self.menubar.addMenu(self.build_menu)
        self.menubar.addMenu(self.help_menu)

        #menu_titles = ['Open', 'Settings']
        self.file_menu.addAction("Settings", self.show_setting_dialog, QKeySequence(Qt.CTRL + Qt.ALT + Qt.Key_S))
        self.help_menu.addAction("Shortcuts", self.show_shortcuts, QKeySequence(Qt.CTRL + Qt.ALT + Qt.Key_K))
        self.help_menu.addAction("About", self.show_help)
        self.build_menu.addAction("Parse",self.parse,QKeySequence(Qt.CTRL+Qt.Key_P))
        self.build_menu.addAction("Build",self.build,QKeySequence(Qt.CTRL+Qt.Key_B))

    def __init_toolbar(self):
        self.toolbar=self.addToolBar("Tool")
        self.toolbar.setMovable(False)
        self.toolbar.addAction(QIcon(":/images/parse.png"),"Parse",self.parse)
        self.toolbar.addAction(QIcon(":/images/build2.png"),"Build",self.build)

    def __init_statusbar(self):
        self.statusbar=self.statusBar()
        #self.statusbar.setFixedHeight(20)

    def __save_tmp_file(self):
        tmp_name=constant.TMP_FILE_NAME
        with open(tmp_name,"w") as file:
            file.write(self.code_doc.toPlainText())

    # private slots
    def parse(self):
        if self.code_doc.isModified():
            self.__save_tmp_file()
            self.code_doc.setModified(False)

        clear_log()
        self.show_log(["Parsing..."])
        ok=self.translator.parse(in_file=constant.TMP_FILE_NAME)
        self.show_log(get_log_list()+(["Parsing succeed. No error reported"] if ok else ["Parsing failed."]))


    def build(self):
        clear_log()

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
    def show_log(self,log_list):
        self.msg_edit.setText("\n".join(log_list))

    def show_message(self, msg):
        self.statusbar.showMessage(str(msg), 4000)


if __name__ == '__main__':
    app=QtWidgets.QApplication([])
    w=MainWindow()
    w.show()
    app.exec()

