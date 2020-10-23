import PyQt5.QtWidgets as QtWidgets

from .ConfigManager import GuiConfigs
from .gui_constant import configs
from gui.ui.setting_dialog import Ui_SettingDialog
from .utils import get_widget_value,set_widget_value


class SettingDialog(QtWidgets.QDialog):
    def __init__(self,parent):
        super().__init__(parent)
        self.ui = Ui_SettingDialog()
        self.ui.setupUi(self)

        self.compiler_widgets = {}
        self.ide_widgets = {}

        self.__organize_widgets()

        self.__load_settings()

    #def set_bg_color(self, color):
    #    self.staged_settings['set_bg_color'] = color

    def __organize_widgets(self):
        # compiler
        self.compiler_widgets[configs.SEQ_TIME] = self.ui.seq_time_box
        self.compiler_widgets[configs.TIME_UNIT] = self.ui.time_unit_box
        self.compiler_widgets[configs.LOG_FILE_PATH] = self.ui.log_file_edit
        # ide
        self.ide_widgets[configs.OUT_FILE_PATH] = self.ui.out_file_edit

    def __load_settings(self):
        for key, widget in self.compiler_widgets.items():
            set_widget_value(widget, configs.get_compiler_value(key))
        for key, widget in self.ide_widgets.items():
            set_widget_value(widget, configs.get_ide_value(key))

    def __export_settings(self):
        ide_settings = {}
        compiler_settings = {}
        for key, widget in self.compiler_widgets.items():
            compiler_settings[key] = get_widget_value(widget)

        for name, widget in self.ide_widgets.items():
            ide_settings[name] = get_widget_value(widget)

        return compiler_settings, ide_settings

    def accept(self) -> None:
        server_s, client_s = self.__export_settings()
        GuiConfigs.need_write_back = True
        configs.set_compiler_config(server_s)
        configs.set_ide_config(client_s)
        # for func,val in self.staged_settings.items():
        #    getattr(configs,func)(val)
        super().accept()

