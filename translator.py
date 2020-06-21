from constants import SYMBOL_TYPE,COMMON_COUNTER
from parser import ASTNode
from utils import log_print
"""
Symbol Attr Memo:
Policy: obj

"""
class Symbol:
    def __init__(self, name: str, type: SYMBOL_TYPE,attr={}):
        self.name = name
        self.type = type
        self.attr = attr

    def addAttr(self, name, type):
        if name not in self.attr:
            self.attr[name] = Symbol(name, type)

    def __repr__(self):
        return f"<{self.name}:{self.type}>"

    def __str__(self):
        return f"<{self.name}:{self.type}>"

class SymbolCounter:
    def __init__(self,init_value=0):
        self.__init_val=init_value
        self.__counters={}

    def new_counter(self,name):
        if name in self.__counters:
            raise Exception("Counter already exists")
        self.__counters[name] = self.__init_val

    def get_counter(self,name):
        if name not in self.__counters:
            self.new_counter(name)
        return self.__counters[name]

    def inc_counter(self,name):
        if name not in self.__counters:
            raise Exception("No such counter")
        self.__counters[name]+=1
        return self.__counters[name]

    def add_counter(self,name,val):
        if name not in self.__counters:
            raise Exception("No such counter")
        self.__counters[name] += val
        return self.__counters[name]

    def __str__(self):
        return f"All counters: {self.__counters}"



'''
class EventSymbol(Symbol):
    def __init__(self, name, type):
        Symbol.__init__(self, name, type)
        self.attributes = {}

    def addAttr(self, name, type):
        if name not in self.attributes:
            self.attributes[name] = Symbol(name, type)

    def __repr__(self):
        return f"<{self.name}:{self.type}:{self.attributes}>"

    def __str__(self):
        return f"<{self.name}:{self.type}:{self.attributes}>"


class ChannelSymbol(Symbol):
    pass

class TableSymbol:
    pass
'''

class SymbolTable:
    def __init__(self):
        self.symbols = {}

    def define(self, sym: Symbol):
        if sym.name in self.symbols:
            raise Exception(f"Policy {sym.name} redefined")
        self.symbols[sym.name] = sym

    def resolve(self, name):
        if name in self.symbols:
            return self.symbols[name]
        else:
            return None

    def __str__(self):
        return f"GlobalScope: {self.symbols}"


class Policy:
    def __init__(self,name):
        self.name=name
        self.sql_statements=[]

    def add_sql(self,statement):
        self.sql_statements.append(statement)

    def __str__(self):
        ans=f"<{self.name}>:"
        for s in self.sql_statements:
            ans+=f"\n> {s}"
        return ans



class ASTVisitor:

    def __init__(self):
        self.counters = SymbolCounter()
        self.policies={}
        self.symbol_table=SymbolTable()

    def __reset_policy(self):
        self.events=[]
        self.policy=Policy(None)

    def visit(self, node,**kwargs):
        return getattr(self, f"visit_{node.type}")(node,**kwargs)

    def visit_PolicyList(self, node: ASTNode):
        for ps in node.children:
            self.__reset_policy()
            self.visit(ps)
        log_print(f"Generated {len(node.children)} policies.")

    def visit_PolicyStatement(self, node: ASTNode):
        self.policy.name=self.visit(node.children[0])
        self.symbol_table.define(Symbol(self.policy.name,SYMBOL_TYPE.POLICY,{'obj':self.policy}))
        for cld in node.children[1:]:
            self.visit(cld)

    def visit_String(self, node: ASTNode):
        log_print("visit String "+node.value)
        return node.value

    def visit_EventStatement(self,node:ASTNode):
        log_print("visit EventStatment")
        for c in node.children:
            self.visit(c)


    def visit_ConditionStatement(self,node:ASTNode):
        log_print("visit ConditionStatement")


    def visit_Actions(self,node:ASTNode):
        log_print("visit Actions")

    def visit_SingleEvent(self,node:ASTNode):
        log_print("visit SingleEvent")
        children=node.children
        channel=self.visit(children[0])
        final_event_table=self.visit(children[1],channel=channel)
        self.events.append(final_event_table)

    def visit_Channel(self,node:ASTNode):
        log_print("visit Channel")
        return node.value

    def visit_Event(self,node:ASTNode, channel):
        log_print("visit Event")
        ori_event_name=node.value['str']
        self.symbol_table.define(Symbol(ori_event_name,SYMBOL_TYPE.EVENT))
        t_id=self.counters.get_counter(COMMON_COUNTER['event'])
        t_name=f"event_{t_id}"
        sql=f"CREATE VIEW {t_name} AS SELECT * FROM {ori_event_name} WHERE channel = '{channel}'"
        self.policy.add_sql(sql)
        return t_name

    def visit_Sequence(self,node,channel):
        log_print("visit Sequence")



if __name__ == '__main__':
    def abc(a,b,c):
        print(a,b,c)

    def test1(**kwargs):
        abc(**kwargs)
    test1(a=1,b=2,c=3)

