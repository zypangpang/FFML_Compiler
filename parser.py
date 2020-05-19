from collections import deque
from constants import  ENDMARK,ELE_TYPE,EMPTY
from grammar_related import get_production_map,Element
from lexer import Lexer
class Parser:
    def __init__(self,grammar,parse_table,start_symbol):
        self.__M=parse_table
        self.__ss=start_symbol
        self.__grammar=grammar
        self.__p_map=get_production_map(grammar)

    def parse(self,lexer):
        # init parsing stack
        stack=deque()
        stack.append(Element(ENDMARK))
        stack.append(self.__ss)

        a=lexer.get_next_token()
        X=stack[-1]
        while X.content!=ENDMARK:
            if X.type==ELE_TYPE.TERM:
                if X==a: # need expansion
                    stack.pop()
                    a=lexer.get_next_token()
                else:
                    raise Exception("parse error")
            elif a not in self.__M[X.content]:
                raise Exception("parse error")
            else:
                prod=self.__p_map[self.__M[X.content,a]]
                stack.pop()
                if prod.right_elements[0].content != EMPTY:
                    stack.extend(prod.right_elements.reverse())
            X=stack[-1]



