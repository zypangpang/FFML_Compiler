from constants import DEBUG,LOG_FILE
try:
    from gui.gui_constant import configs
    log_file=configs.get_compiler_value(configs.LOG_FILE_PATH)
except:
    log_file=LOG_FILE

logging_config={
    'version': 1,
    'formatters':{
        'default':{
            'format':'%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        }
    },
    'handlers':{
        'console':{
            'level':"INFO",
            'class':"logging.StreamHandler",
            'formatter':"default"
        },
        'file':{
            "level":"INFO",
            "class":"logging.handlers.TimedRotatingFileHandler",
            'formatter':"default",
            "filename": log_file,
            "when":"D",
            "backupCount":7
        }
    },
    'root':{
        "level":"INFO",
        "handlers":['console'] if DEBUG else ['file']
    }
}

'''
class: logging.StreamHandler
level: DEBUG
formatter: simple
stream: ext://sys.stdout
loggers:
simpleExample:
level: DEBUG
handlers: [console]
propagate: no
root:
level: DEBUG
handlers: [console]
'''

