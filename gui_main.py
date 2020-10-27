from PyQt5 import QtWidgets
from gui.MainWindow import MainWindow
from gui.gui_constant import configs

def app_closing():
    print('app closing...')
    configs.save()

if __name__ == '__main__':
    app=QtWidgets.QApplication([])
    w=MainWindow()
    app.aboutToQuit.connect(app_closing)
    w.show()
    app.exec()
