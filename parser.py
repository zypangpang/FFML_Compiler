from collections import deque
from constants import  ENDMARK,ELE_TYPE,EMPTY
from grammar_related import get_production_map,Element
from utils import  SyntaxError
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
    def __str__(self):
        return f"<{self.type}: {self.value}, {len(self.children)} children>"

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

    def __get_error_str(self, lexer, expect, given):
        left,right=lexer.get_error_context()
        begin=f"Syntax error at line {lexer.get_cur_line_num()}"
        dash_num=10
        first_line=f"{'-'*dash_num}{begin}{'-'*dash_num}"
        ans=f"{first_line}\n"\
            f"{left}??{right}\n\n"\
            f">>> Expect {expect}\n"\
            f"<<< But '{given}' is given\n"\
            f"{'-'*len(first_line)}"
        return ans

    def parse_tree(self):
        '''
        Parse input. Raise exception if there is syntax error
        :param lexer:
        :return:
        '''
        # init parsing stack
        lexer=self.lexer
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
                    raise SyntaxError("TermNotMatch", self.__get_error_str(lexer, X.content, a))
                    #print(X,token)
            elif a not in self.__M[X.content]:
                error=self.__get_error_str(lexer, tuple(self.__M[X.content].keys()),
                                     token.attr['entry']['str'] if token.name=='<ID>' else token.attr['str'])
                #print(X,token)
                raise SyntaxError("NoMatchProdution",error)
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

    def parse_AST(self):
        return self.__PolicyList()

    def __raise_inner_error(self):
        raise SyntaxError("InnerError","Unexpected production ID")
        #self.__get_error_str(self.lexer, tuple(self.__M[nt_name].keys()),
                             #token.attr['entry']['str'] if token.name == '<ID>' else token.attr['str'])
        # print(X,token)
        #raise Exception("Syntax error")


    def __match(self,terminal):
        token=self.lexer.get_next_token()
        a=self.__get_token_info(token)
        if terminal == a:  # need expansion
            return token
        else:
            raise SyntaxError("TermNotMatch", self.__get_error_str(self.lexer, terminal, a))


    def __get_prod_id(self,nt_name,next_token):
        a = self.__get_token_info(next_token)
        if a not in self.__M[nt_name]:
            error=self.__get_error_str(self.lexer, tuple(self.__M[nt_name].keys()),
                                 next_token.attr['entry']['str'] if next_token.name == '<ID>' else next_token.attr['str'])
            # print(X,token)
            raise SyntaxError("NoMatchProdution",error)
        prod_id = self.__M[nt_name][a]
        return prod_id

    def __PolicyList(self):
        next_token=self.lexer.lookahead()
        nt_name='PolicyList'
        prod_id=self.__get_prod_id(nt_name,next_token)
        if prod_id==0: # 0: PolicyList -> PolicyStatement I_A
            node=self.__PolicyStatement()
            return self.__I_A([node])
        else:
            self.__raise_inner_error()

    def __I_A(self,inh):
        next_token=self.lexer.lookahead()
        nt_name = 'I_A'
        prod_id=self.__get_prod_id(nt_name,next_token)

        if prod_id==1:
            node=self.__PolicyStatement()
            return self.__I_A(inh+[node])
        elif prod_id == 2:
            return ASTNode('PolicyList',"",inh)
        else:
            self.__raise_inner_error()

    def __I_B(self):
        next_token=self.lexer.lookahead()
        nt_name = 'I_B'
        prod_id=self.__get_prod_id(nt_name,next_token)

        if prod_id==3:
            return self.__ConditionStatement()
        elif prod_id == 4:
            return None
        else:
            self.__raise_inner_error()

    def __PolicyStatement(self):
        next_token=self.lexer.lookahead()
        nt_name = 'PolicyStatement'
        prod_id = self.__get_prod_id(nt_name, next_token)

        if prod_id == 5:
            PolicyId_node=self.__PolicyId()
            EventStatement_node = self.__EventStatement()
            I_B_node=self.__I_B()
            ActionStatement_node=self.__ActionStatement()
            self.__match(';')
            if I_B_node:
                children=[PolicyId_node,EventStatement_node,I_B_node,ActionStatement_node]
            else:
                children=[PolicyId_node,EventStatement_node,ActionStatement_node]
            return ASTNode('PolicyStatement', "", children)
        else:
            self.__raise_inner_error()

    def __PolicyId(self):
        next_token=self.lexer.lookahead()
        nt_name = 'PolicyId'
        prod_id = self.__get_prod_id(nt_name, next_token)

        if prod_id == 6:
            self.__match('POLICYID')
            self.__match('[')
            node=self.__String()
            self.__match(']')
            return node
        else:
            self.__raise_inner_error()

    def __I_C(self,inh):
        next_token=self.lexer.lookahead()
        nt_name = 'I_C'
        prod_id = self.__get_prod_id(nt_name, next_token)

        if prod_id == 7:
            self.__LogicalOr()
            node=self.__SingleEvent()
            return self.__I_C(inh+[node])
        elif prod_id == 8:
            return ASTNode("EventStatement","",inh)
        else:
            self.__raise_inner_error()

    def __I_D(self):
        next_token=self.lexer.lookahead()
        nt_name = 'I_D'
        prod_id = self.__get_prod_id(nt_name, next_token)

        if prod_id == 20:
            return None
        elif prod_id == 21:
            self.__match('(')
            node=self.__IntegerLiteral()
            self.__match(')')
            return node
        else:
            self.__raise_inner_error()

    def __I_E(self,inh):
        next_token=self.lexer.lookahead()
        nt_name = 'I_E'
        prod_id = self.__get_prod_id(nt_name, next_token)

        if prod_id == 22:
            return ASTNode("EventSeq","",inh)
        elif prod_id ==23:
            self.__match(',')
            node=self.__Event()
            return self.__I_E(inh+[node])
        else:
            self.__raise_inner_error()


    def __IntegerLiteral(self):
        next_token=self.lexer.lookahead()
        nt_name = 'IntegerLiteral'
        prod_id = self.__get_prod_id(nt_name, next_token)

        if prod_id == 49:
            next_token=self.__match('<DIGITS>')
            number=next_token.attr['str']
            return  self.__F_A(number)
        else:
            self.__raise_inner_error()

    def __ConditionStatement(self):
        next_token=self.lexer.lookahead()
        nt_name = 'ConditionStatement'
        prod_id = self.__get_prod_id(nt_name, next_token)

        if prod_id == 28:
            self.__match('IF')
            node=self.__SingleCondition()
            return self.__I_F([node])
        else:
            self.__raise_inner_error()

    def __EventStatement(self):
        next_token=self.lexer.lookahead()
        nt_name = 'EventStatement'
        prod_id = self.__get_prod_id(nt_name, next_token)

        if prod_id == 9:
            self.__match('ON')
            node=self.__SingleEvent()
            return self.__I_C([node])
        else:
            self.__raise_inner_error()

    def __ActionStatement(self):
        next_token=self.lexer.lookahead()
        nt_name = 'ActionStatement'
        prod_id = self.__get_prod_id(nt_name, next_token)

        if prod_id == 69:
            self.__match("THEN")
            node = self.__Procedure()
            return self.__I_K([node])
        else:
            self.__raise_inner_error()

    def __String(self):
        next_token=self.lexer.get_next_token()
        nt_name = 'String'
        prod_id = self.__get_prod_id(nt_name, next_token)

        if prod_id == 52:
            return ASTNode("String",next_token.attr['str'].strip("'"),[])
        else:
            self.__raise_inner_error()

    def __LogicalOr(self):
        next_token=self.lexer.get_next_token()
        nt_name = 'LogicalOr'
        prod_id = self.__get_prod_id(nt_name, next_token)

        if prod_id == 74:
            return ASTNode("Or","Or",[])
        else:
            self.__raise_inner_error()

    def __LogicalAnd(self):
        next_token=self.lexer.get_next_token()
        nt_name = 'LogicalAnd'
        prod_id = self.__get_prod_id(nt_name, next_token)
        if prod_id == 73:
            return ASTNode("And","And",[])
        else:
            self.__raise_inner_error()

    def __SingleEvent(self):
        next_token=self.lexer.lookahead()
        nt_name = 'SingleEvent'
        prod_id = self.__get_prod_id(nt_name, next_token)

        if prod_id == 10:
            Channel_node=self.__Channel()
            EventList_syn=self.__EventList()
            return ASTNode('SingleEvent',"",[Channel_node,EventList_syn])
        else:
            self.__raise_inner_error()

    def __Channel(self):
        next_token=self.lexer.get_next_token()
        nt_name='Channel'
        self.__get_prod_id(nt_name, next_token)
        a = self.__get_token_info(next_token)
        return ASTNode("Channel",a,[])


    def __EventList(self):
        next_token=self.lexer.lookahead()
        nt_name = 'EventList'
        prod_id = self.__get_prod_id(nt_name, next_token)

        if prod_id == 18:
            return self.__Sequence()
        elif prod_id == 19:
            self.__match('[')
            node=self.__Event()
            self.__match(']')
            return node
        else:
            self.__raise_inner_error()

    def __Event(self,):
        next_token=self.lexer.lookahead()
        nt_name = 'Event'
        prod_id = self.__get_prod_id(nt_name, next_token)

        if prod_id == 82:
            next_token=self.__match("<ID>")
            return ASTNode("Event",next_token.attr['entry'],[])
        else:
            self.__raise_inner_error()


    def __Sequence(self):
        next_token=self.lexer.lookahead()
        nt_name = 'Sequence'
        prod_id = self.__get_prod_id(nt_name, next_token)

        if prod_id == 24:
            self.__match('SEQ')
            I_D_node=self.__I_D()
            self.__match('[')
            Event1_node=self.__Event()
            self.__match(',')
            Event2_node=self.__Event()
            I_E_syn=self.__I_E([Event1_node,Event2_node])
            self.__match(']')
            if I_D_node:
                return ASTNode('Sequence','',[I_D_node,I_E_syn])
            else:
                return ASTNode('Sequence','',[I_E_syn])

        else:
            self.__raise_inner_error()

    def __Instance(self):
        next_token=self.lexer.lookahead()
        nt_name = 'Instance'
        prod_id = self.__get_prod_id(nt_name, next_token)

        if prod_id == 25:
            next_token=self.__match('<ID>')
            id_entry=next_token.attr['entry']
            return ASTNode('Name',id_entry,[])
        else:
            self.__raise_inner_error()

    def __I_F(self,inh):
        next_token=self.lexer.lookahead()
        nt_name = 'I_F'
        prod_id = self.__get_prod_id(nt_name, next_token)

        if prod_id == 26:
            Op_syn=self.__LogicalOperator()
            node=self.__SingleCondition()
            return self.__I_F(inh+[Op_syn,node])
        elif prod_id == 27:
            return ASTNode('ConditionStatement',"",inh)
        else:
            self.__raise_inner_error()

    def __LogicalOperator(self):
        next_token=self.lexer.lookahead()
        nt_name = 'LogicalOperator'
        prod_id = self.__get_prod_id(nt_name, next_token)

        if prod_id == 29:
            return self.__LogicalAnd()
        elif prod_id == 30:
            return self.__LogicalOr()
        else:
            self.__raise_inner_error()

    def __SingleCondition(self):
        next_token=self.lexer.lookahead()
        nt_name = 'SingleCondition'
        prod_id = self.__get_prod_id(nt_name, next_token)

        if prod_id == 31:
            node1=self.__AdditiveExpression1()
            node2=self.__Comparison()
            node3=self.__AdditiveExpression1()
            return ASTNode("SingleCondition","",[node1,node2,node3])
        elif prod_id == 32:
            node1 = self.__HistoryStatement()
            node2 = self.__Comparison()
            node3 = self.__AdditiveExpression1()
            return ASTNode("SingleCondition", "", [node1, node2, node3])
        else:
            self.__raise_inner_error()

    def __I_G(self,inh):
        next_token=self.lexer.lookahead()
        nt_name = 'I_G'
        prod_id = self.__get_prod_id(nt_name, next_token)

        if prod_id == 33:
            return self.__FactorExpression2(inh)
        elif prod_id ==34:
            return ASTNode('Factor',"",inh)
        else:
            self.__raise_inner_error()

    def __I_H(self,inh):
        next_token=self.lexer.lookahead()
        nt_name = 'I_H'
        prod_id = self.__get_prod_id(nt_name, next_token)

        if prod_id == 35:
            return self.__AdditiveExpression2(inh)
        elif prod_id ==36:
            return ASTNode("Expression","",inh)
        else:
            self.__raise_inner_error()

    def __AdditiveExpression1(self):
        next_token=self.lexer.lookahead()
        nt_name = 'AdditiveExpression1'
        prod_id = self.__get_prod_id(nt_name, next_token)

        if prod_id == 37:
            node1=self.__FactorExpression1()
            return self.__I_H([node1])
        elif prod_id==38:
            node1=self.__Query()
            node2=self.__I_G([node1])
            return self.__I_H([node2])
        else:
            self.__raise_inner_error()

    def __AdditiveExpression2(self,inh):
        next_token=self.lexer.lookahead()
        nt_name = 'AdditiveExpression2'
        prod_id = self.__get_prod_id(nt_name, next_token)

        if prod_id == 39:
            self.__match('+')
            node=self.__FactorExpression1()
            return self.__I_H(inh+[ASTNode("AddOp","+",[]),node])
        elif prod_id ==40:
            self.__match('-')
            node = self.__FactorExpression1()
            return self.__I_H(inh+[ASTNode("AddOp", "-", []), node])
        else:
            self.__raise_inner_error()

    def __Comparison(self,):
        next_token=self.lexer.get_next_token()
        nt_name = 'Comparison'
        prod_id = self.__get_prod_id(nt_name, next_token)
        a=self.__get_token_info(next_token)
        return ASTNode("Comp",a,[])

    def __HistoryStatement(self):
        next_token=self.lexer.lookahead()
        nt_name = 'HistoryStatement'
        prod_id = self.__get_prod_id(nt_name, next_token)

        if prod_id == 65:
            self.__match("HISTORY")
            return self.__HistInput()
        else:
            self.__raise_inner_error()

    def __HistInput(self):
        next_token=self.lexer.lookahead()
        nt_name = 'HistInput'
        prod_id = self.__get_prod_id(nt_name, next_token)

        if prod_id == 66:
            self.__match('(')
            next_token=self.__match("<DIGITS>")
            time=int(next_token.attr['str'])
            self.__match(')')
            self.__match('[')
            node1=self.__AdditiveExpression1()
            comp=self.__Comparison()
            node2=self.__AdditiveExpression1()
            self.__match(']')
            time_node=ASTNode("Int",time,[])
            condition_node=ASTNode("Condition",'',[node1,comp,node2])
            return ASTNode("HistStatement","",[time_node,condition_node])
        else:
            self.__raise_inner_error()

    def __FactorExpression1(self):
        next_token=self.lexer.lookahead()
        nt_name = 'FactorExpression1'
        prod_id = self.__get_prod_id(nt_name, next_token)

        if prod_id == 41:
            node=self.__Factors()
            return self.__I_G([node])
        else:
            self.__raise_inner_error()

    def __FactorExpression2(self,inh):
        next_token=self.lexer.lookahead()
        nt_name = 'FactorExpression2'
        prod_id = self.__get_prod_id(nt_name, next_token)

        if prod_id == 42:
            self.__match('*')
            node=self.__Factors()
            return self.__I_G(inh+[ASTNode("MultiOp","*",[]),node])
        elif prod_id==43:
            self.__match('/')
            node = self.__Factors()
            return self.__I_G(inh + [ASTNode("MultiOp", "/", []), node])
        else:
            self.__raise_inner_error()

    def __Query(self):
        next_token=self.lexer.lookahead()
        nt_name = 'Query'
        prod_id = self.__get_prod_id(nt_name, next_token)

        if prod_id == 53:
            self.__match('QUERY')
            syn=self.__StoredProcedure()
            return syn
        else:
            self.__raise_inner_error()

    def __Factors(self,):
        next_token=self.lexer.lookahead()
        nt_name = 'Factors'
        prod_id = self.__get_prod_id(nt_name, next_token)

        if prod_id == 44:
            return self.__Boolean()
        elif prod_id ==45:
            return self.__EventParameter()
        elif prod_id == 46:
            return self.__IntegerLiteral()
        elif prod_id == 47:
            return self.__String()
        elif prod_id == 48:
            self.__match('(')
            node=self.__AdditiveExpression1()
            self.__match(')')
            return node
        else:
            self.__raise_inner_error()

    def __Boolean(self,):
        next_token=self.lexer.lookahead()
        nt_name = 'Boolean'
        prod_id = self.__get_prod_id(nt_name, next_token)

        if prod_id == 50:
            self.__match('FALSE')
            return ASTNode("Boolean",False,[])
        elif prod_id ==51:
            self.__match('TRUE')
            return ASTNode("Boolean",True,[])
        else:
            self.__raise_inner_error()

    def __EventParameter(self,):
        next_token=self.lexer.lookahead()
        nt_name = 'EventParameter'
        prod_id = self.__get_prod_id(nt_name, next_token)

        if prod_id == 81:
            next_token=self.__match("<ID>")
            id1=next_token.attr['entry']
            self.__match('.')
            next_token=self.__match("<ID>")
            id2=next_token.attr['entry']
            return ASTNode("EventParam",[id1,id2],[])
        else:
            self.__raise_inner_error()

    def __F_A(self,inh):
        next_token=self.lexer.lookahead()
        nt_name = 'F_A'
        prod_id = self.__get_prod_id(nt_name, next_token)

        if prod_id == 83:
            return ASTNode("Digits",float(inh),[])
        elif prod_id == 84:
            self.__match(".")
            next_token=self.__match("<DIGITS>")
            number2=next_token.attr['str']
            number=float(inh+'.'+number2)
            return ASTNode("Digits",number,[])
        else:
            self.__raise_inner_error()

    def __StoredProcedure(self,):
        next_token=self.lexer.lookahead()
        nt_name = 'StoredProcedure'
        prod_id = self.__get_prod_id(nt_name, next_token)

        if prod_id == 54:
            name=self.__Instance()
            self.__match('(')
            param=self.__Parameters()
            self.__match(')')
            return ASTNode("Query","",[name,param])

    def __Parameters(self,):
        next_token=self.lexer.lookahead()
        nt_name = 'Parameters'
        prod_id = self.__get_prod_id(nt_name, next_token)

        if prod_id == 57:
            syn=self.__ParamInput()
            return self.__I_I([syn])
        else:
            self.__raise_inner_error()

    def __I_I(self,inh):
        next_token=self.lexer.lookahead()
        nt_name = 'I_I'
        prod_id = self.__get_prod_id(nt_name, next_token)

        if prod_id == 55:
            return ASTNode("Params","",inh)
        elif prod_id==56:
            self.__match(',')
            syn=self.__ParamInput()
            return self.__I_I(inh+[syn])
        else:
            self.__raise_inner_error()

    def __ParamInput(self):
        next_token=self.lexer.lookahead()
        nt_name = 'ParamInput'
        prod_id = self.__get_prod_id(nt_name, next_token)

        if prod_id == 58:
            return self.__ChannelList()
        elif prod_id == 59:
            return self.__EventParameter()
        elif prod_id == 60:
            return self.__IntegerLiteral()
        else:
            self.__raise_inner_error()

    def __I_J(self,inh):
        next_token=self.lexer.lookahead()
        nt_name = 'I_J'
        prod_id = self.__get_prod_id(nt_name, next_token)

        if prod_id == 61:
            return ASTNode("ChannelList","",inh)
        elif prod_id == 62:
            self.__match(',')
            node=self.__Channel()
            return self.__I_J(inh+[node])
        else:
            self.__raise_inner_error()

    def __ChannelList(self,):
        next_token=self.lexer.lookahead()
        nt_name = 'ChannelList'
        prod_id = self.__get_prod_id(nt_name, next_token)

        if prod_id == 63:
            return self.__Channel()
        elif prod_id == 64:
            self.__match('(')
            node=self.__Channel()
            syn=self.__I_J([node])
            self.__match(')')
            return syn
        else:
            self.__raise_inner_error()

    def __I_K(self,inh):
        next_token=self.lexer.lookahead()
        nt_name = 'I_K'
        prod_id = self.__get_prod_id(nt_name, next_token)

        if prod_id == 67:
            self.__LogicalAnd()
            node=self.__Procedure()
            return self.__I_K(inh+[node])
        elif prod_id == 68:
            return ASTNode("Actions","",inh)
        else:
            self.__raise_inner_error()

    def __Procedure(self,):
        next_token=self.lexer.lookahead()
        nt_name = 'Procedure'
        prod_id = self.__get_prod_id(nt_name, next_token)

        if prod_id == 72:
            name=self.__Instance()
            self.__match('(')
            node=self.__I_L()
            self.__match(")")
            if node:
                return ASTNode("Procedure","",[name,node])
            else:
                return ASTNode("Procedure", "", [name])
        else:
            self.__raise_inner_error()

    def __I_L(self):
        next_token=self.lexer.lookahead()
        nt_name = 'I_L'
        prod_id = self.__get_prod_id(nt_name, next_token)

        if prod_id == 70:
            return self.__Parameters()
        elif prod_id == 71:
            return None
        else:
            self.__raise_inner_error()
