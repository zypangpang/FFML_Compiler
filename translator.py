from constants import SYMBOL_TYPE
from parser import ASTNode
class Symbol:
    def __init__(self,name:str,type:SYMBOL_TYPE):
        self.name=name
        self.type=type

    def __repr__(self):
        return f"<{self.name}:{self.type}>"

    def __str__(self):
        return f"<{self.name}:{self.type}>"

class EventSymbol(Symbol):
    def __init__(self,name,type):
        Symbol.__init__(self,name,type)
        self.attributes={}
    def addAttr(self,name,type):
        if name not in self.attributes:
            self.attributes[name]=Symbol(name,type)
    def __repr__(self):
        return f"<{self.name}:{self.type}:{self.attributes}>"
    def __str__(self):
        return f"<{self.name}:{self.type}:{self.attributes}>"

class ChannelSymbol(Symbol):
    pass

class SymbolTable:
    def __init__(self):
        self.symbols={}
    def define(self,sym:Symbol):
        self.symbols[sym.name]=sym
    def resolve(self,name):
        if name in self.symbols:
            return self.symbols[name]
        else:
            return None
    def __str__(self):
        return f"GlobalScope: {self.symbols}"

class ASTVisitor:
    def __init__(self):
        pass

    def visit(self,node):
        getattr(self,f"visit_{node.type}")(node)

    def visit_PolicyList(self,node:ASTNode):
        for ps in node.children:
            self.visit(ps)
        print('Tree walking done.')
    def visit_PolicyStatement(self,node:ASTNode):
        print(f'Statement {node.children[0].value}')
