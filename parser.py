from collections import deque
from constants import  ENDMARK,ELE_TYPE,EMPTY
from grammar_related import get_production_map,Element
#from lexer import Lexer
class Parser:
    def __init__(self,grammar,parse_table,start_symbol):
        self.__M=parse_table
        self.__ss=start_symbol
        self.__grammar=grammar
        self.__p_map=get_production_map(grammar)

    def __get_token_info(self,token):
        '''
        Get info form token obj for parse table comparison
        :param token:
        :return:
        '''
        if token.name == "<ID>":
            entry=token.attr['entry']
            if entry['name']=='<KEYWORD>':
                return entry['str']
            else:
                return token.name
        if token.name == '<DIGITS>' or token.name == '<STRING>':
            return token.name
        return token.attr['str']

    '''
    def __equals(self,X, token):
        if token.name == "<ID>":
            entry=token.attr['entry']
            if entry['name']=='<KEYWORD>':
                return entry['str']==X
            else:
                return token.name == X
        if token.name == '<DIGITS>' or token.name == '<STRING>':
            return X == token.name
        return X == token.attr['str']
    '''

    def __print_error_str(self,lexer):
        print(f"Syntax error at line {lexer.get_cur_line_num()}")
        print("<<<<<<<<<<<")
        print(lexer.get_error_env())
        print(">>>>>>>>>>>")

    def parse(self,lexer):
        '''
        Parse input. Raise exception if there is syntax error
        :param lexer:
        :return:
        '''
        # init parsing stack
        stack=deque()
        stack.append(Element(ENDMARK))
        stack.append(Element(self.__ss))

        token=lexer.get_next_token()
        X=stack[-1]
        while X.content!=ENDMARK:
            a=self.__get_token_info(token)
            #print(a)
            if X.type==ELE_TYPE.TERM:
                if X.content==a: # need expansion
                    stack.pop()
                    token=lexer.get_next_token()
                else:
                    self.__print_error_str(lexer)
                    print(f"Need a '{X.content}', but '{a}' is given")
                    #print(X,token)
                    raise Exception("Syntax error")
            elif a not in self.__M[X.content]:
                self.__print_error_str(lexer)
                print(f"Expect {tuple(self.__M[X.content].keys())}")
                print(f"But '{token.attr['entry']['str'] if token.name=='<ID>' else token.attr['str']}' is given")
                #print(X,token)
                raise Exception("Syntax error")
            else:
                prod=self.__p_map[self.__M[X.content][a]]
                #print(prod)
                stack.pop()
                if prod.right_elements[0].content != EMPTY:
                    stack.extend(reversed(prod.right_elements))
            X=stack[-1]



