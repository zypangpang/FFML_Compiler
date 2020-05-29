from collections import deque
from constants import  ENDMARK,ELE_TYPE,EMPTY
from grammar_related import get_production_map,Element
#from lexer import Lexer
class ASTNode:
    def __init__(self,name,parent,children):
        self.name=name
        self.children=children
        self.parent=parent
        if parent is None:
            self.depth=0
        else:
            self.depth=parent.depth+1

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

    def __print_error_str(self,lexer,expect,given):
        print(f"Syntax error at line {lexer.get_cur_line_num()}")
        print("<<<<<<<<<<<")
        left,right=lexer.get_error_context()
        print(left,"^^",right)
        print(">>>>>>>>>>>")
        print(f"Expect {expect}")
        print(f"But '{given}' is given")

    def parse(self,lexer):
        '''
        Parse input. Raise exception if there is syntax error
        :param lexer:
        :return:
        '''
        # init parsing stack
        root=ASTNode("",None,[])
        stack=deque()
        stack.append(Element(ENDMARK))
        start_ele=Element(self.__ss,AST_parent=root)
        stack.append(start_ele)

        token=lexer.get_next_token()
        X=stack[-1]

        cur_node=root

        while X.content!=ENDMARK:
            a=self.__get_token_info(token)
            #print(a)
            if X.type==ELE_TYPE.TERM:
                if X.content==a: # need expansion

                    #cur_node['children'].append({"name":X.content,"children":[]})
                    #X.AST_parent['children'].append({"name":X.content,"children":[]})
                    X.AST_parent.children.append(ASTNode(X.content,X.AST_parent,[]))

                    stack.pop()
                    token=lexer.get_next_token()
                else:
                    self.__print_error_str(lexer,X.content,a)
                    #print(X,token)
                    raise Exception("Syntax error")
            elif a not in self.__M[X.content]:
                self.__print_error_str(lexer,tuple(self.__M[X.content].keys()),
                                       token.attr['entry']['str'] if token.name=='<ID>' else token.attr['str'])
                #print(X,token)
                raise Exception("Syntax error")
            else:
                prod=self.__p_map[self.__M[X.content][a]]

                #tnode={"name": X.content, "children": []}
                tnode=ASTNode(X.content,X.AST_parent,[])
                X.AST_parent.children.append(tnode)

                #print(prod)
                stack.pop()
                if prod.right_elements[0].content != EMPTY:
                    for e in prod.right_elements:
                        e.AST_parent=tnode
                    stack.extend(reversed(prod.right_elements))
            X=stack[-1]
        return root.children[0]



