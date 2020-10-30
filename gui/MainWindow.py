from PyQt5 import QtWidgets
from PyQt5.QtGui import QKeySequence, QIcon, QTextDocument, QFont, QFontDatabase
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtWidgets import QSizePolicy, QVBoxLayout, QFileDialog, QMessageBox, QPlainTextDocumentLayout
import gui.resources_gen.qtresource

from constants import GUI
import gui.gui_constant as gconstant
from gui.CentralWidget import CentralWidget
from gui.Highlighter import Highlighter
from gui.SettingDialog import SettingDialog
from gui.utils import clear_log,get_log_list,choose_file
import constants

from main import Main
from utils import LexicalError,SyntaxError


class MainWindow(QtWidgets.QMainWindow):
    translator=Main()
    def __init__(self):
        super().__init__()
        GUI[0]=True
        self.setWindowTitle("FFML Editor")
        self.setFixedSize(1000,800)


        self.__init_data()
        self.__init_menubar()
        self.__init_toolbar()
        self.__init_statusbar()
        self.__init_cwidget()
        self.__init_document()


        # Show setting dialog for the first running
        if gconstant.SHOW_SETTING_DIALOG:
            self.show_setting_dialog()

        self.load_settings()

        self.show_message("Ready")


    def __init_data(self):
        self.out_file_name=None
        self.cur_file_name=None
        self.file_modified=False


    def __init_cwidget(self):
        self.cwidget = CentralWidget()
        # self.cwidget.setStyleSheet("background-color:green;")
        # self.cwidget.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)
        self.msg_edit=self.cwidget.msgEdit
        self.code_edit=self.cwidget.codeEdit
        #db=QFontDatabase()
        #print(db.families())
        font=QFont()
        font.setFixedPitch(True)
        font.setFamily("DejaVu Sans Mono")
        self.code_edit.setFont(font)
        self.msg_edit.setFont(font)
        self.setCentralWidget(self.cwidget)

    def __init_document(self):
        self.code_doc=QTextDocument("",self)
        layout=QPlainTextDocumentLayout(self.code_doc)
        self.code_doc.setDocumentLayout(layout)
        self.highlighter=Highlighter(self.code_doc)
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
        self.file_menu.addAction("Save", self.save, QKeySequence(Qt.CTRL + Qt.Key_S))
        self.file_menu.addAction("Save as...", self.save_as, QKeySequence(Qt.CTRL +Qt.SHIFT + Qt.Key_S))
        self.file_menu.addAction("Settings", self.show_setting_dialog, QKeySequence(Qt.CTRL + Qt.ALT + Qt.Key_S))


        self.help_menu.addAction("Shortcuts", self.show_shortcuts, QKeySequence(Qt.CTRL + Qt.ALT + Qt.Key_K))
        self.help_menu.addAction("About", self.show_help)

        self.build_menu.addAction("Parse",self.parse,QKeySequence(Qt.CTRL+Qt.Key_P))
        self.build_menu.addAction("Compile", self.compile, QKeySequence(Qt.CTRL + Qt.Key_B))

    def __init_toolbar(self):
        self.toolbar=self.addToolBar("Tool")
        self.toolbar.setMovable(False)
        self.toolbar.addAction(QIcon(":/images/folder.png"),"Open",self.open_file)
        self.toolbar.addAction(QIcon(":/images/save-filled.png"),"Save",self.save)
        self.toolbar.addAction(QIcon(":/images/check.png"),"Parse",self.parse)
        self.toolbar.addAction(QIcon(":/images/build-filled.png"),"Compile", self.compile)
        self.toolbar.addAction(QIcon(":/images/play.png"),"Run")

    def __init_statusbar(self):
        self.statusbar=self.statusBar()
        #self.statusbar.setFixedHeight(20)

    def __save_tmp_file(self,first=False):
        if self.code_doc.isModified():
            if not first:
                self.file_modified=True
            tmp_name=gconstant.TMP_FILE_NAME
            with open(tmp_name,"w") as file:
                file.write(self.code_doc.toPlainText())
            self.code_doc.setModified(False)
        return gconstant.TMP_FILE_NAME

    def file_is_modified(self):
        return self.file_modified or self.code_doc.isModified()

    def load_settings(self):
        constants.translator_configs['SEQ_UNIT']=gconstant.configs.get_time_unit()
        constants.translator_configs['SEQ_TIME']=gconstant.configs.get_compiler_value(gconstant.configs.SEQ_TIME)
        #constants.translator_configs['LOG_FILE']=gconstant.configs.get_compiler_value(gconstant.configs.LOG_FILE_PATH)
        font_size=int(gconstant.configs.get_ide_value(gconstant.configs.FONT_SIZE))

        #font = self.code_edit.currentFont()
        font=QFont()
        font.setFamily("DejaVu Sans Mono")
        font.setPointSize(font_size)
        self.code_edit.setFont(font)
        self.msg_edit.setFont(font)

        #font=self.msg_edit.currentFont()
        #font.setPointSize(font_size)
        #self.msg_edit.setFont(font)

    def reset_file_state(self):
        self.file_modified=False
        self.cur_file_name=None
        self.out_file_name=None

    # private slots
    def open_file(self):
        fileName = QFileDialog.getOpenFileName(self, "Open FFML file", str(gconstant.DEFAULT_OPEN_PATH),
                                               "FFML files (*.ffml)")
        if fileName[0]:
            if not self.close_file(): return
            with open(fileName[0],'r') as f:
                self.code_doc.setPlainText(f.read())
            self.cur_file_name=fileName[0]
            self.__save_tmp_file(True)
            self.show_log([])
            self.show_message("File opened")

    def save_as(self):
       fileName=QFileDialog.getSaveFileName(self,"Save as", self.cur_file_name if self.cur_file_name  else str(gconstant.DEFAULT_OPEN_PATH), "FFML files (*.ffml)")
       if fileName[0]:
           save_file=fileName[0]
           with open(save_file,'w') as f:
               f.write(self.code_doc.toPlainText())
           self.cur_file_name=save_file
           return True
       else:
           return False

    def save(self):
        if self.cur_file_name:
            with open(self.cur_file_name,'w') as f:
                f.write(self.code_doc.toPlainText())
            return True
        else:
            return self.save_as()

    def close_file(self):
        #if not self.cur_file_name: return True
        if self.file_is_modified():
            btn=QMessageBox.question(self,"Save file?","The file has been changed. Save file?",
                                     buttons=QMessageBox.Cancel|QMessageBox.Yes|QMessageBox.No,defaultButton=QMessageBox.Yes)
            if btn==QMessageBox.Yes:
                if not self.save():
                    return False
            elif btn==QMessageBox.Cancel:
                return False
        self.reset_file_state()
        self.code_doc.clear()
        self.msg_edit.clear()
        return True

    def parse(self):
        file_name=self.__save_tmp_file()

        clear_log()
        self.show_log(["Parsing..."])
        e=self.translator.parse(in_file=file_name)
        if e:
            self.show_log(get_log_list() + ["Parsing failed."])
            if isinstance(e,(SyntaxError,LexicalError)):
                lineNum=e.line_number
                print(lineNum)
                self.code_edit.setHighLightColor(True)
                self.code_edit.moveToLine(lineNum)
                self.code_edit.setHighLightColor(False)
        else:
            self.show_log(get_log_list()+["Parsing succeed. No error reported"])
        self.show_message("Parsing finished")



    def compile(self):
        if not self.out_file_name:
            fileName=QFileDialog.getSaveFileName(self,"Save as", str(gconstant.DEFAULT_OUTPUT_PATH), "Flink SQL files (*.fsql)")
            if fileName[0]:
                self.out_file_name=fileName[0]
            else:
                return

        in_file=self.__save_tmp_file()
        clear_log()
        e=self.translator.translate(in_file=in_file,out_file=self.out_file_name)
        if e:
            self.show_log(get_log_list() + ["Compiling failed."])
            if isinstance(e, (SyntaxError, LexicalError)):
                lineNum = e.line_number
                print(lineNum)
                self.code_edit.setHighLightColor(True)
                self.code_edit.moveToLine(lineNum)
                self.code_edit.setHighLightColor(False)
        else:
            self.show_log(get_log_list() + ["Compiling succeed. No error reported"])
        self.show_message("Compiling finished")


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

    # Override
    def closeEvent(self, event) -> None:
        if not self.close_file():
            event.ignore()
            return
        super().closeEvent(event)

    #def closing(self):
    #    print("app closing...")
    #    gconstant.configs.save()


if __name__ == '__main__':
    app=QtWidgets.QApplication([])
    w=MainWindow()
    w.show()
    app.exec()

