from enum import Enum

DEBUG=True
GEN_JAVA=False
LOG_FILE='./translator.log'
#class EBNF_OP(Enum):
#    NONE = 0
#    PLUS = 1
#    MULTIPLE = 2
#    QUESTION = 3
class LOG_LEVEL(Enum):
    '''
    Grammar Element type
    '''
    INFO = 0
    WARNING = 1
    ERROR = 2

class ELE_TYPE(Enum):
    '''
    Grammar Element type
    '''
    TERM = 0
    NONTERM = 1
    COMBI = 2

class SYMBOL_TYPE(Enum):
    EVENT = 0
    CHANNEL=1
    TABLE =2
    POLICY =3
    INTERNAL = 4

class COUNTER_TYPE(Enum):
    TABLE=0
    EVENT=1
    CONDITION=2
    COMPARISON=3
    PROCEDURE=4
    MATH=5
    COUNT=6
    CAST=7

class TIME_UNIT(Enum):
    SECOND=0
    MINUTE=1
    HOUR=2
    DAY=3

#COUNTER_NAME={
#    COUNTER_TYPE.TABLE:"table",
#    COUNTER_TYPE.EVENT: "event",
#    COUNTER_TYPE.CONDITION: "condition",
#    COUNTER_TYPE.COMPARISON: "comparison",
#}


EBNF_OP_SYMBOL = ['+', '*', '?']
EMPTY = '#'
ENDMARK = '$'
TERM_BEGIN_CHARS = f'"<{EMPTY}'

# Lexer file reading buffer size
BUFFER_SIZE= 4096 #bytes

# Reserved keywords
KEYWORDS=['POLICYID' , 'THEN',  'TRUE', 'ONL', 'ATM', 'QUERY',  'CHQ', 'CNP', 'HISTORY',  'OR',  'AND',  'FALSE'
        , 'OTH', 'DD', 'IF',  'ON', 'CP', 'SEQ',]

COMMENT_SYM = '//'

# Translator related
SEQ_UNIT=TIME_UNIT.SECOND
SEQ_TIME=5
PREDEFINED_EVENTS={
    "transfer",
    "password_change",
    "login"
}

COMMON_KEYS=['id','accountnumber']


