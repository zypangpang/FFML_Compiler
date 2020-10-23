from PyQt5 import QtWidgets
from gui.MainWindow import MainWindow

if __name__ == '__main__':
    app=QtWidgets.QApplication([])
    w=MainWindow()
    app.aboutToQuit.connect(w.closing)
    w.show()
    app.exec()
