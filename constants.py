from enum import Enum

class EBNF_OP(Enum):
    NONE=0
    PLUS = 1
    MULTIPLE = 2
    QUESTION = 3

class ELE_TYPE(Enum):
    TERM=0
    NONTERM = 1
    COMBI = 2

EBNF_OP_SYMBOL=['+','*','?']
EMPTY='#'
ENDMARK='$'
TERM_BEGIN_CHARS= f'"<{EMPTY}'