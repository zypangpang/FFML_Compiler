from constants import DEBUG
log_file="./translator.log"
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

