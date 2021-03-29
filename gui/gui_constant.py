from pathlib import Path
import os

from gui.ConfigManager import GuiConfigs

HELP_TEXT="nihao"
TMP_FILE_NAME='.code.tmp'

DEFAULT_OPEN_PATH=Path.home()
DEFAULT_OUTPUT_PATH=Path.home().joinpath("flink_sql/out.fsql")
DEFAULT_CONFIG_PATH=Path.home().joinpath(".ffml_compiler/configs.ini")
DEFAULT_FONT_SIZE=14
DEFAULT_EXTERNAL_EDITOR='mousepad'
DEFAULT_FLINK_HOME=Path.home().joinpath("flink")
DEFAULT_JOB_JAR=Path.home().joinpath('flink/flinkSQLJob.jar')

configs=None
SHOW_SETTING_DIALOG=False

if not GuiConfigs.check_config_file(DEFAULT_CONFIG_PATH):
    os.makedirs(DEFAULT_CONFIG_PATH.parent, 0o0755,True)
    path = GuiConfigs.generate_init_configs(DEFAULT_CONFIG_PATH)
    SHOW_SETTING_DIALOG = True
    print(f"Cannot find the config file. Auto generated a config file {path}.")

configs = GuiConfigs(DEFAULT_CONFIG_PATH)


