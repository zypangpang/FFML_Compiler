import configparser,os,copy
from pathlib import Path
import constants
import gui.gui_constant as gconstants

COMPILER_SECTION = 'compiler'
IDE_SECTION = 'ide'

def write_back(func):
    def inner_func(*args,**kwargs):
        GuiConfigs.need_write_back=True
        func(*args,**kwargs)
    return inner_func

class GuiConfigs():
    need_write_back=False

    TIME_UNIT = "time unit"
    SEQ_TIME = 'seq time'
    LOG_FILE_PATH='log file path'
    #HTTP_HOST = "http host"
    OPT_LEVEL='opt level'

    OUT_FILE_PATH='out file path'
    FONT_SIZE='font size'
    EDITOR='external editor'
    FLINK_HOME='flink home'
    JOB_JAR='job jar'


    @classmethod
    def check_config_file(cls,file_path):
        return os.path.exists(file_path)

    @classmethod
    def generate_init_configs(cls,file_path):
        #index_folder = DEFAULT_CONFIG_PATH.parent.joinpath("index")
        configs = configparser.ConfigParser()
        configs[COMPILER_SECTION] = {
            cls.TIME_UNIT: constants.get_config_value('SEQ_UNIT').name,
            cls.SEQ_TIME: constants.get_config_value('SEQ_TIME'),
            cls.LOG_FILE_PATH: constants.get_config_value('LOG_FILE'),
            cls.OPT_LEVEL: constants.get_config_value('OPT_LEVEL'),
        }
        configs[IDE_SECTION] = {
            cls.OUT_FILE_PATH: gconstants.DEFAULT_OUTPUT_PATH,
            cls.FONT_SIZE:gconstants.DEFAULT_FONT_SIZE,
            cls.EDITOR:gconstants.DEFAULT_EXTERNAL_EDITOR,
            cls.FLINK_HOME:gconstants.DEFAULT_FLINK_HOME,
            cls.JOB_JAR:gconstants.DEFAULT_JOB_JAR
        }
        with open(file_path, "w") as f:
            configs.write(f)
        return file_path

    def __init__(self,file_path):
        self.config_path=file_path
        self.config=configparser.ConfigParser()
        self.config.read(file_path)
        #self.ori_config=copy.deepcopy(self.config)

    def save(self):
        #if self.config is self.ori_config:
        #    return
        if not GuiConfigs.need_write_back:
            return
        print("config write back")
        with open(self.config_path, "w") as f:
            self.config.write(f)

    def get_time_unit(self):
        time_unit_str=self.config[COMPILER_SECTION].get(self.TIME_UNIT)
        return getattr(constants.TIME_UNIT,time_unit_str)

    def set_compiler_config(self, config_dict):
        for key,val in config_dict.items():
            self.set_compiler_value(key, val)

    def set_ide_config(self, config_dict):
        for key, val in config_dict.items():
            self.set_ide_value(key, val)

    def set_compiler_value(self, key, value):
        self.config[COMPILER_SECTION][key]=str(value)

    def set_ide_value(self, key, value):
        self.config[IDE_SECTION][key]=str(value)

    def get_compiler_value(self, key):
        return self.config[COMPILER_SECTION][key]

    def get_ide_value(self, key):
        return self.config[IDE_SECTION][key]


'''
    def __set_value_both(self,key,val):
        try:
            self.config[IDE_SECTION][key]=val
        except:
            self.config[IDE_SECTION]={
                key:val
            }

        try:
            self.ori_config[IDE_SECTION][key]=val
        except:
            self.ori_config[IDE_SECTION]={
                key:val
            }

    @write_back
    def set_zoom_factor(self,val):
        self.__set_value_both(self.ZOOM_FACTOR,val)


    @write_back
    def set_bg_color(self,color):
        self.__set_value_both(self.BG_COLOR,color)
'''


#def set_dicts(self,dicts:dict):
    #    #dict_names=[Path(x).stem for x in dict_paths]
    ##    self.config[CONFIG_DAEMON_SECTION][self.DICT_FILED]=','.join(dicts.values())
    #    self.config[CONFIG_DAEMON_SECTION][self.ENABLED_FILED]=','.join(dicts.keys())
    #    with open(self.config_path,"w") as f:
    #        self.config.write(f)
    #    return dicts.keys()

    #def add_dict(self,dict_path):
    #    dict_name=Path(dict_path).stem
    #    self.config[CONFIG_DAEMON_SECTION][self.DICT_FILED]+=f",{dict_path}"
    #    self.config[CONFIG_DAEMON_SECTION][self.ENABLED_FILED]+=f",{dict_name}"
    #    with open(self.config_path,"w") as f:
    #        self.config.write(f)
    #    return dict_name


    #def get_section(self,section_name):
    #    if section_name in self.config.sections():
    #        return self.config[section_name]
    #    raise Exception(f"No config section {section_name}")

    #def get_value(self, section, key):
    #    return self.config[section][key]

    #def get_daemon_value(self, key):
    #    return self.config[CONFIG_DAEMON_SECTION][key]

    #def get_frontend_value(self, key):
    #    return self.config[CONFIG_FRONTEND_SECTION][key]

    #def get_dictionary_paths(self):
    #    dicts = self.get_value("dictionary daemon", "dictionaries").split(",")
    ##    dicts=[x.strip() for x in dicts]
    #    index_folder=Path(self.get_daemon_value("index folder"))
    #    ans={}
    #    for path in dicts:
    #        path=Path(path)
    #        name=path.stem
    #        data_folder=str(index_folder.joinpath(name))
    #        ans[name]=[str(path),data_folder]
    #    return ans


    #def get_enabled_dicts(self):
    #    try:
    #        dicts=self.get_daemon_value("enabled dictionaries")
    #    except Exception as e:
    #        return []
    #    return [x.strip() for x in dicts.split(',')] if dicts else []



if __name__ == '__main__':
    pass
