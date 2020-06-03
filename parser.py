from collections import deque
from constants import  ENDMARK,ELE_TYPE,EMPTY
from grammar_related import get_production_map,Element
#from lexer import Lexer
class ASTNode:
    def __init__(self,type,value,children,parent=None):
        self.type=type
        self.value=value
        self.children=children
        self.parent=parent
        #if parent is None:
        #    self.depth=0
        #else:
        #    self.depth=parent.depth+1

class Parser:
    def __init__(self,grammar,parse_table,start_symbol,lexer):
        self.__M=parse_table
        self.__ss=start_symbol
        self.__grammar=grammar
        self.__p_map=get_production_map(grammar)
        self.lexer=lexer

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

    def nonrecursive_parse(self,lexer):
        '''
        Parse input. Raise exception if there is syntax error
        :param lexer:
        :return:
        '''
        # init parsing stack
        root=ASTNode("","",[])
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
                    X.AST_parent.children.append(ASTNode(X.content,X.content,[],X.AST_parent))

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
                tnode=ASTNode(X.content,"",[],X.AST_parent)
                X.AST_parent.children.append(tnode)

                #print(prod)
                stack.pop()
                if prod.right_elements[0].content != EMPTY:
                    for e in prod.right_elements:
                        e.AST_parent=tnode
                    stack.extend(reversed(prod.right_elements))
            X=stack[-1]
        return root.children[0]

    def __raise_syntax_error(self,token,nt_name):
        self.__print_error_str(self.lexer, tuple(self.__M[nt_name].keys()),
                               token.attr['entry']['str'] if token.name == '<ID>' else next_token.attr['str'])
        # print(X,token)
        raise Exception("Syntax error")

    def recursive_parse(self,lexer):
        pass

    def __match(self,token,terminal,shift=True):
        a=self.__get_token_info(token)
        if terminal == a:  # need expansion
            if shift:
                return self.lexer.get_next_token()
        else:
            self.__print_error_str(self.lexer, terminal, a)
            # print(X,token)
            raise Exception("Syntax error")


    def __get_prod_id(self,nt_name,next_token):
        a = self.__get_token_info(next_token)
        if a not in self.__M[nt_name]:
            self.__raise_syntax_error(next_token, nt_name)
            return
        prod_id = self.__M[nt_name][a]
        return prod_id

    def __PolicyList(self,next_token):
        nt_name='PolicyList'
        prod_id=self.__get_prod_id(nt_name,next_token)
        if prod_id==0: # 0: PolicyList -> PolicyStatement I_A
            node=self.__PolicyStatement(next_token)
            next_token=self.lexer.get_next_token()
            return self.__I_A(next_token,[node])
        else:
            raise Exception("zyp: Unexpected Error")

    def __I_A(self,next_token,inh):
        nt_name = 'I_A'
        prod_id=self.__get_prod_id(nt_name,next_token)

        if prod_id==1:
            node=self.__PolicyStatement(next_token)
            next_token=self.lexer.get_next_token()
            return self.__I_A(next_token,[inh,node])
        elif prod_id == 2:
            return ASTNode('PolicyList',"",inh)
        else:
            raise Exception("zyp: Unexpected Error")

    def __I_B(self,next_token):
        nt_name = 'I_B'
        prod_id=self.__get_prod_id(nt_name,next_token)

        if prod_id==3:
            return self.__ConditionStatement(next_token)
        elif prod_id == 4:
            return None
        else:
            raise Exception("zyp: Unexpected Error")

    def __PolicyStatement(self,next_token):
        nt_name = 'PolicyStatment'
        prod_id = self.__get_prod_id(nt_name, next_token)

        if prod_id == 5:
            PolicyId_node=self.__PolicyId(next_token)
            next_token = self.lexer.get_next_token()
            EventStatement_node = self.__EventStatement(next_token)
            next_token = self.lexer.get_next_token()
            I_B_node=self.__I_B(next_token)
            next_token = self.lexer.get_next_token()
            ActionStatement_node=self.__ActionStatement(next_token)
            if I_B_node:
                children=[PolicyId_node,EventStatement_node,I_B_node,ActionStatement_node]
            else:
                children=[PolicyId_node,EventStatement_node,ActionStatement_node]
            return ASTNode('PolicyStatement', "", children)
        else:
            raise Exception("zyp: Unexpected Error")

    def __PolicyId(self,next_token):
        nt_name = 'PolicyId'
        prod_id = self.__get_prod_id(nt_name, next_token)

        if prod_id == 6:
            next_token=self.__match(next_token,'POLICYID')
            next_token=self.__match(next_token,'[')
            node=self.__String(next_token)
            next_token=self.lexer.get_next_token()
            self.__match(next_token,']',False)
            return node
        else:
            raise Exception("zyp: Unexpected Error")

    def __I_C(self,next_token,inh):
        nt_name = 'I_C'
        prod_id = self.__get_prod_id(nt_name, next_token)

        if prod_id == 7:
            self.__LogicalOr(next_token)
            next_token=self.lexer.get_next_token()
            node=self.__SingleEvent(next_token)
            return self.__I_C(next_token,[inh,node])
        elif prod_id == 8:
            return ASTNode("EventStatement","",inh)
        else:
            raise Exception("zyp: Unexpected Error")

    def __ConditionStatement(self,next_token):
        pass

    def __EventStatement(self,next_token):
        pass

    def __ActionStatement(self,next_token):
        pass

    def __String(self,next_token):
        pass

    def __LogicalOr(self,next_token):
        pass
    def __SingleEvent(self,next_token):
        pass



