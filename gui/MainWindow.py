from PyQt5 import QtWidgets
from PyQt5.QtGui import QKeySequence, QIcon, QTextDocument
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtWidgets import QSizePolicy, QVBoxLayout, QFileDialog
import gui.resources_gen.qtresource

from constants import GUI
import gui.gui_constant as gconstant
from gui.CentralWidget import CentralWidget
from gui.SettingDialog import SettingDialog
from gui.utils import clear_log,get_log_list,choose_file
import constants

from main import Main

class MainWindow(QtWidgets.QMainWindow):
    translator=Main()
    def __init__(self):
        super().__init__()
        GUI[0]=True
        self.setWindowTitle("FFML Editor")
        self.setFixedSize(1000,800)

        self.load_settings()

        self.__init_data()
        self.__init_menubar()
        self.__init_toolbar()
        self.__init_statusbar()
        self.__init_cwidget()
        self.__init_document()

        # Show setting dialog for the first running
        if gconstant.SHOW_SETTING_DIALOG:
            self.show_setting_dialog()

        self.show_message("Ready")


    def __init_data(self):
        self.out_file_name=None


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
        self.file_menu.addAction("Open...", self.open_file, QKeySequence(Qt.CTRL + Qt.Key_O))
        self.file_menu.addAction("Settings", self.show_setting_dialog, QKeySequence(Qt.CTRL + Qt.ALT + Qt.Key_S))


        self.help_menu.addAction("Shortcuts", self.show_shortcuts, QKeySequence(Qt.CTRL + Qt.ALT + Qt.Key_K))
        self.help_menu.addAction("About", self.show_help)

        self.build_menu.addAction("Parse",self.parse,QKeySequence(Qt.CTRL+Qt.Key_P))
        self.build_menu.addAction("Build",self.build,QKeySequence(Qt.CTRL+Qt.Key_B))

    def __init_toolbar(self):
        self.toolbar=self.addToolBar("Tool")
        self.toolbar.setMovable(False)
        self.toolbar.addAction(QIcon(":/images/folder.png"),"Open",self.open_file)
        self.toolbar.addAction(QIcon(":/images/save-filled.png"),"Save")
        self.toolbar.addAction(QIcon(":/images/check.png"),"Parse",self.parse)
        self.toolbar.addAction(QIcon(":/images/build-filled.png"),"Build",self.build)
        self.toolbar.addAction(QIcon(":/images/play.png"),"Run")

    def __init_statusbar(self):
        self.statusbar=self.statusBar()
        #self.statusbar.setFixedHeight(20)

    def __save_tmp_file(self):
        if self.code_doc.isModified():
            tmp_name=gconstant.TMP_FILE_NAME
            with open(tmp_name,"w") as file:
                file.write(self.code_doc.toPlainText())
            self.code_doc.setModified(False)
        return gconstant.TMP_FILE_NAME

    def load_settings(self):
        constants.translator_configs['SEQ_UNIT']=gconstant.configs.get_time_unit()
        constants.translator_configs['SEQ_TIME']=gconstant.configs.get_compiler_value(gconstant.configs.SEQ_TIME)
        #constants.translator_configs['LOG_FILE']=gconstant.configs.get_compiler_value(gconstant.configs.LOG_FILE_PATH)

    # private slots
    def open_file(self):
        fileName = QFileDialog.getOpenFileName(self, "Open FFML file", str(gconstant.DEFAULT_OPEN_PATH),
                                               "FFML files (*.ffml)")
        if fileName[0]:
            with open(fileName[0],'r') as f:
                self.code_doc.setPlainText(f.read())
            self.show_log([])
            self.show_message("File opened")

    def parse(self):
        file_name=self.__save_tmp_file()

        clear_log()
        self.show_log(["Parsing..."])
        ok=self.translator.parse(in_file=file_name)
        self.show_log(get_log_list()+(["Parsing succeed. No error reported"] if ok else ["Parsing failed."]))


    def build(self):
        if not self.out_file_name:
            fileName=QFileDialog.getSaveFileName(self,"Save as", str(gconstant.DEFAULT_OUTPUT_PATH), "Flink SQL files (*.fsql)")
            if fileName[0]:
                self.out_file_name=fileName[0]
            else:
                return

        in_file=self.__save_tmp_file()
        clear_log()
        ok=self.translator.translate(in_file=in_file,out_file=self.out_file_name)
        self.show_log(get_log_list()+(["Compiling succeed. No error reported"] if ok else ["Compiling failed."]))

    def show_setting_dialog(self):
        dialog=SettingDialog(self)
        dialog.accepted.connect(self.load_settings)
        dialog.exec()

    def show_shortcuts(self):
        pass

    def show_help(self):
        msgBox = QtWidgets.QMessageBox()
        msgBox.setStyleSheet("QLabel{min-width: 600px;}")
        msgBox.setWindowTitle("Help")
        msgBox.setText(gconstant.HELP_TEXT)
        msgBox.exec()

    # Auxiliary functions ************************************#
    def show_log(self,log_list):
        self.msg_edit.setText("\n".join(log_list))

    def show_message(self, msg):
        self.statusbar.showMessage(str(msg), 2000)

    def closing(self):
        print("closing...")
        gconstant.configs.save()


if __name__ == '__main__':
    app=QtWidgets.QApplication([])
    w=MainWindow()
    w.show()
    app.exec()

