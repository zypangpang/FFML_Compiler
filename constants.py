from enum import Enum

class EBNF_OP(Enum):
    NONE=0
    PLUS = 1
    MULTIPLE = 2
    QUESTION = 3

EBNF_OP_SYMBOL=['+','*','?']
EMPTY='#'