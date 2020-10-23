import PyQt5.QtWidgets as QtWidgets
from PyQt5.QtWidgets import QFileDialog
from .gui_constant import DEFAULT_OUTPUT_PATH

log_str_list=[]

def clear_log():
    log_str_list.clear()

def get_log_list():
    return log_str_list

def add_log(content,level):
    log_str_list.append(level.upper() + ": " + content)

def choose_file(parent):
    #dialog=QFileDialog(parent,"Save as",DEFAULT_OUTPUT_PATH,"Flink SQL files (*.fsql)")
    #dialog.setFileMode(QFileDialog.AnyFile)
    return QFileDialog.getSaveFileUrl(parent,"Save as",DEFAULT_OUTPUT_PATH,"Flink SQL files (*.fsql)")

def get_widget_value(widget):
    if isinstance(widget,QtWidgets.QComboBox):
        return widget.currentText()
    elif isinstance(widget,QtWidgets.QLineEdit):
        return widget.text()
    elif isinstance(widget,QtWidgets.QSpinBox):
        return widget.value()
    elif isinstance(widget,QtWidgets.QDoubleSpinBox):
        return widget.value()

def set_widget_value(widget,val):
    if isinstance(widget, QtWidgets.QComboBox):
        widget.setCurrentText(val)
    elif isinstance(widget, QtWidgets.QLineEdit):
        widget.setText(val)
    elif isinstance(widget, QtWidgets.QSpinBox):
        widget.setValue(int(val))
    elif isinstance(widget, QtWidgets.QDoubleSpinBox):
        widget.setValue(float(val))

