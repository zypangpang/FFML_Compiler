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

    def parse_tree(self,lexer):
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

    def parse_AST(self,lexer):
        pass

    def __raise_syntax_error(self,token,nt_name):
        self.__print_error_str(self.lexer, tuple(self.__M[nt_name].keys()),
                               token.attr['entry']['str'] if token.name == '<ID>' else next_token.attr['str'])
        # print(X,token)
        raise Exception("Syntax error")


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
            return self.__I_A(next_token,inh+[node])
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
            return self.__I_C(next_token,inh+[node])
        elif prod_id == 8:
            return ASTNode("EventStatement","",inh)
        else:
            raise Exception("zyp: Unexpected Error")

    def __I_D(self,next_token):
        nt_name = 'I_D'
        prod_id = self.__get_prod_id(nt_name, next_token)

        if prod_id == 20:
            return None
        elif prod_id == 21:
            next_token=self.__match(next_token,'(')
            node=self.__IntegerLiteral(next_token)
            next_token=self.lexer.get_next_token()
            self.__match(next_token,')',False)
            return node
        else:
            raise Exception("zyp: Unexpected Error")
    def __I_E(self,next_token,inh):
        nt_name = 'I_E'
        prod_id = self.__get_prod_id(nt_name, next_token)

        if prod_id == 22:
            return ASTNode("EventSeq","",inh)
        elif prod_id ==23:
            next_token=self.__match(next_token,',')
            node=self.__Event(next_token)
            next_token=self.lexer.get_next_token()
            return self.__I_E(next_token,inh+[node])
        else:
            raise Exception("zyp: Unexpected Error")


    def __IntegerLiteral(self,next_token):
        nt_name = 'IntegerLiteral'
        prod_id = self.__get_prod_id(nt_name, next_token)

        if prod_id == 49:
            self.__match(next_token,'<DIGITS>',False)
            number=next_token.attr['str']
            next_token=self.lexer.get_next_token()
            return  self.__F_A(next_token,number)
        else:
            raise Exception("zyp: Unexpected Error")

    def __ConditionStatement(self,next_token):
        nt_name = 'ConditionStatement'
        prod_id = self.__get_prod_id(nt_name, next_token)

        if prod_id == 28:
            next_token=self.__match(next_token,'IF')
            node=self.__SingleCondition(next_token)
            next_token=self.lexer.get_next_token()
            return self.__I_F(next_token,[node])
        else:
            raise Exception("zyp: Unexpected Error")

    def __EventStatement(self,next_token):
        nt_name = 'EventStatement'
        prod_id = self.__get_prod_id(nt_name, next_token)

        if prod_id == 9:
            next_token=self.__match(next_token,'ON')
            node=self.__SingleEvent(next_token)
            next_token=self.lexer.get_next_token()
            return self.__I_C(next_token,[node])
        else:
            raise Exception("zyp: Unexpected Error")

    def __ActionStatement(self,next_token):
        pass

    def __String(self,next_token):
        nt_name = 'String'
        prod_id = self.__get_prod_id(nt_name, next_token)

        if prod_id == 52:
            return ASTNode("String",next_token.attr['str'].strip("'"),[])
        else:
            raise Exception("zyp: Unexpected Error")

    def __LogicalOr(self,next_token):
        pass
    def __LogicalAnd(self,next_token):
        nt_name = 'LogicalAnd'
        prod_id = self.__get_prod_id(nt_name, next_token)

        if prod_id == 20:
            pass
    def __SingleEvent(self,next_token):
        nt_name = 'SingleEvent'
        prod_id = self.__get_prod_id(nt_name, next_token)

        if prod_id == 10:
            Channel_node=self.__Channel(next_token)
            next_token=self.lexer.get_next_token()
            EventList_syn=self.__EventList(next_token)
            return ASTNode('SingleEvent',"",[Channel_node,EventList_syn])
        else:
            raise Exception("zyp: Unexpected Error")

    def __Channel(self,next_token):
        nt_name='Channel'
        self.__get_prod_id(nt_name, next_token)
        a = self.__get_token_info(next_token)
        return ASTNode("Channel",a,[])


    def __EventList(self,next_token):
        nt_name = 'EventList'
        prod_id = self.__get_prod_id(nt_name, next_token)

        if prod_id == 18:
            return self.__Sequence(next_token)
        elif prod_id == 19:
            next_token=self.__match(next_token,'[')
            node=self.__Event(next_token)
            next_token=self.lexer.get_next_token()
            self.__match(next_token,']',False)
            return node
        else:
            raise Exception("zyp: Unexpected Error")

    def __Event(self,next_token):
        pass


    def __Sequence(self,next_token):
        nt_name = 'Sequence'
        prod_id = self.__get_prod_id(nt_name, next_token)

        if prod_id == 24:
            next_token= self.__match(next_token,'SEQ')
            I_D_node=self.__I_D(next_token)
            next_token=self.lexer.get_next_token()
            next_token=self.__match(next_token,'[')
            Event1_node=self.__Event(next_token)
            next_token=self.__match(next_token,',')
            Event2_node=self.__Event(next_token)
            next_token=self.lexer.get_next_token()
            I_E_syn=self.__I_E(next_token,[Event1_node,Event2_node])
            next_token=self.lexer.get_next_token()
            self.__match(next_token,']',False)
            return ASTNode('Sequence','',[I_D_node,I_E_syn])
        else:
            raise Exception("zyp: Unexpected Error")
    def __Instance(self,next_token):
        nt_name = 'Instance'
        prod_id = self.__get_prod_id(nt_name, next_token)

        if prod_id == 25:
            self.__match(next_token,'<ID>',False)
            id_val=next_token.attr['entry']['str']
            return ASTNode('<ID>',id_val,[])
        else:
            raise Exception("zyp: Unexpected Error")

    def __I_F(self,next_token,inh):
        nt_name = 'I_F'
        prod_id = self.__get_prod_id(nt_name, next_token)

        if prod_id == 26:
            Op_syn=self.__LogicalOperator(next_token)
            next_token=self.lexer.get_next_token()
            node=self.__SingleCondition(next_token)
            next_token=self.lexer.get_next_token()
            return self.__I_F(next_token,inh+[Op_syn,node])
        elif prod_id == 27:
            return ASTNode('ConditionStatement',"",inh)
        else:
            raise Exception("zyp: Unexpected Error")

    def __LogicalOperator(self,next_token):
        nt_name = 'LogicalOperator'
        prod_id = self.__get_prod_id(nt_name, next_token)

        if prod_id == 29:
            return self.__LogicalAnd(next_token)
        elif prod_id == 30:
            return self.__LogicalOr(next_token)
        else:
            raise Exception("zyp: Unexpected Error")

    def __SingleCondition(self,next_token):
        nt_name = 'SingleCondition'
        prod_id = self.__get_prod_id(nt_name, next_token)

        if prod_id == 31:
            node1=self.__AdditiveExpression1(next_token)
            next_token=self.lexer.get_next_token()
            node2=self.__Comparison(next_token)
            next_token = self.lexer.get_next_token()
            node3=self.__AdditiveExpression1(next_token)
            return ASTNode("SingleCondition","",[node1,node2,node3])
        elif prod_id == 32:
            node1 = self.__HistoryStatement(next_token)
            next_token = self.lexer.get_next_token()
            node2 = self.__Comparison(next_token)
            next_token = self.lexer.get_next_token()
            node3 = self.__AdditiveExpression1(next_token)
            return ASTNode("SingleCondition", "", [node1, node2, node3])
        else:
            raise Exception("zyp: Unexpected Error")
    def __I_G(self,next_token,inh):
        nt_name = 'I_G'
        prod_id = self.__get_prod_id(nt_name, next_token)

        if prod_id == 33:
            return self.__FactorExpression2(next_token,inh)
        elif prod_id ==34:
            return ASTNode('Factor',"",inh)
        else:
            raise Exception("zyp: Unexpected Error")
    def __I_H(self,next_token,inh):
        nt_name = 'I_H'
        prod_id = self.__get_prod_id(nt_name, next_token)

        if prod_id == 35:
            return self.__AdditiveExpression2(next_token,inh)
        elif prod_id ==36:
            return ASTNode("Additive","",inh)

    def __AdditiveExpression1(self,next_token):
        nt_name = 'AdditiveExpression1'
        prod_id = self.__get_prod_id(nt_name, next_token)

        if prod_id == 37:
            node1=self.__FactorExpression1(next_token)
            next_token=self.lexer.get_next_token()
            return self.__I_H(next_token,[node1])
        elif prod_id==38:
            node1=self.__Query(next_token)
            next_token=self.lexer.get_next_token()
            node2=self.__I_G(next_token,[node1])
            next_token=self.lexer.get_next_token()
            return self.__I_H(next_token,[node2])
        else:
            raise Exception("zyp: Unexpected Error")

    def __AdditiveExpression2(self,next_token,inh):
        nt_name = 'AdditiveExpression2'
        prod_id = self.__get_prod_id(nt_name, next_token)

        if prod_id == 39:
            node=self.__FactorExpression1(next_token)
            next_token=self.lexer.get_next_token()
            return self.__I_H(next_token,inh+[ASTNode("AddOp","+",[]),node])
        elif prod_id ==40:
            node = self.__FactorExpression1(next_token)
            next_token=self.lexer.get_next_token()
            return self.__I_H(next_token, inh+[ASTNode("AddOp", "-", []), node])
        else:
            raise Exception("zyp: Unexpected Error")

    def __Comparison(self,next_token):
        nt_name = 'I_D'
        prod_id = self.__get_prod_id(nt_name, next_token)

        if prod_id == 20:
            pass
    def __HistoryStatement(self,next_token):
        nt_name = 'I_D'
        prod_id = self.__get_prod_id(nt_name, next_token)

        if prod_id == 20:
            pass

    def __FactorExpression1(self,next_token):
        nt_name = 'FactorExpression1'
        prod_id = self.__get_prod_id(nt_name, next_token)

        if prod_id == 41:
            node=self.__Factors(next_token)
            next_token=self.lexer.get_next_token()
            return self.__I_G(next_token,[node])
        else:
            raise Exception("zyp: Unexpected Error")

    def __FactorExpression2(self,next_token,inh):
        nt_name = 'FactorExpression2'
        prod_id = self.__get_prod_id(nt_name, next_token)

        if prod_id == 42:
            node=self.__Factors(next_token)
            next_token=self.lexer.get_next_token()
            return self.__I_G(next_token,inh+[ASTNode("MultiOp","*",[]),node])
        elif prod_id==43:
            node = self.__Factors(next_token)
            next_token = self.lexer.get_next_token()
            return self.__I_G(next_token, inh + [ASTNode("MultiOp", "/", []), node])
        else:
            raise Exception("zyp: Unexpected Error")

    def __Query(self,next_token):
        nt_name = 'I_D'
        prod_id = self.__get_prod_id(nt_name, next_token)

        if prod_id == 20:
            pass
    def __Factors(self,next_token):
        nt_name = 'Factors'
        prod_id = self.__get_prod_id(nt_name, next_token)

        if prod_id == 44:
            return self.__Boolean(next_token)
        elif prod_id ==45:
            return self.__EventParameter(next_token)
        elif prod_id == 46:
            return self.__IntegerLiteral(next_token)
        elif prod_id == 47:
            return self.__String(next_token)
        elif prod_id == 48:
            return self.__AdditiveExpression1(next_token)
        else:
            raise Exception("zyp: Unexpected Error")

    def __Boolean(self,next_token):
        nt_name = 'Boolean'
        prod_id = self.__get_prod_id(nt_name, next_token)

        if prod_id == 50:
            self.__match(next_token,'FALSE',False)
            return ASTNode("Boolean",False,[])
        elif prod_id ==51:
            self.__match(next_token, 'TRUE', False)
            return ASTNode("Boolean",True,[])
        else:
            raise Exception("zyp: Unexpected Error")

    def __EventParameter(self,next_token):
        nt_name = 'I_D'
        prod_id = self.__get_prod_id(nt_name, next_token)

        if prod_id == 20:
            pass
    def __F_A(self,next_token,inh):
        nt_name = 'I_D'
        prod_id = self.__get_prod_id(nt_name, next_token)

        if prod_id == 20:
            pass
