from constants import EBNF_OP_SYMBOL,EMPTY, ELE_TYPE, TERM_BEGIN_CHARS
from _collections import defaultdict
import sys


global_first_set={}
global_grammar={}

global_addto_first=defaultdict(list)
global_addto_follow=defaultdict(list)

class Element:
    """The element of grammar production right part"""

    def __init__(self, symbols, op=''):
        self.symbols = symbols
        self.op = op
        if self.op != '':
            self.type= ELE_TYPE.COMBI
        elif self.symbols[0][0] in TERM_BEGIN_CHARS:
            self.type = ELE_TYPE.TERM
        else:
            self.type = ELE_TYPE.NONTERM

    def __str__(self):
        return f"Element({self.symbols} {self.op})"

    def __repr__(self):
        return f"({self.symbols} {self.op})"


def read_EBNF(file_path):
    grammar = {}
    with open(file_path, "r") as f:
        line = f.readline()
        while line:
            left=line.split()[0]
            production = {'left': left, 'right': []}
            right = f.readline().split()
            while right[0] != ';':
                production['right'].append(right)
                right = f.readline().split()

            grammar[left]=production
            line = f.readline()
    return grammar


def process_right(grammar):
    for _,production in grammar.items():
        new_right = []
        for line in production['right']:
            right_elements = []
            line = iter(line)
            item = next(line, None)
            while item:
                if item[0] == '(':
                    item = item[1:]
                    symbols = []
                    while item:
                        if item[-1] in EBNF_OP_SYMBOL:
                            symbols.append(Element([item[:-2]]))
                            break
                        else:
                            symbols.append(Element([item]))
                        item = next(line, None)
                    right_elements.append(Element(symbols, item[-1]))
                else:
                    right_elements.append(Element([item]))
                item = next(line, None)
            new_right.append(right_elements)
        production['right'] = new_right

def elements_first_set(elements):
    fset=set()
    all_empty=True
    for ele in elements:
        ele_first_set = element_first_set(ele)
        fset.update(ele_first_set - {EMPTY})
        if EMPTY not in ele_first_set:
            all_empty = False
            break
    if all_empty:
        fset.add(EMPTY)
    return fset

def nonterminal_first_set(left):
    productions = global_grammar[left]['right']
    fset=set()
    for line in productions:
        fset.update(elements_first_set(line))
    return fset


def combination_first_set(element):
    fset = elements_first_set(element.symbols)
    if element.op == '?' or element.op == '*':
        fset.add(EMPTY)
    return fset


#def string_first_set(str):
#    if str[0] in f'"<{EMPTY}':
#        return {str}
#    else:
#        return nonterminal_first_set(str)

def element_first_set(element):
    if element.type==ELE_TYPE.TERM:
        return {element.symbols[0]}
    elif element.type == ELE_TYPE.NONTERM:
        str=element.symbols[0]
        if str not in global_first_set:
            global_first_set[str]=nonterminal_first_set(str)
        return global_first_set[str]
    elif element.type == ELE_TYPE.COMBI:
        return combination_first_set(element)
    else:
        raise Exception("invalid element type")

def first_set(grammar):
    for nt in grammar:
        if nt not in global_first_set:
            global_first_set[nt]=nonterminal_first_set(nt)

def get_addto_dict(grammar):
    productions=grammar.values()
    for prod in productions:
        for line in prod['right']:
            for i in range(0,len(line)-1):
                pass
            if line[-1].type==ELE_TYPE.COMBI and len(line[-1].symbols)>1:
                pass

if __name__ == '__main__':
    EBNF_path = "grammar.txt" if len(sys.argv)<=1 else sys.argv[1]
    global_grammar = read_EBNF(EBNF_path)
    process_right(global_grammar)
    #for x in grammar:
    #    print(f"{x} -> {grammar[x]}")
    first_set(global_grammar)
    for x in global_first_set:
        if x[0] not in f'"<{EMPTY}':
            print(f"{x} -> {global_first_set[x]}")

