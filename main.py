from constants import EBNF_OP_SYMBOL,EMPTY, ELE_TYPE, TERM_BEGIN_CHARS,ENDMARK
from utils import print_seperator, print_set
from collections import defaultdict
import sys


global_first_set={}
global_grammar={}
global_start_symbol=None

#global_addto_first=defaultdict(list)
global_addto_follow={}

global_follow_set={}

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
        first_line=f.readline().strip()
        start_symbol=first_line
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
    return start_symbol, grammar


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

def init_follow_set(grammar):
    for nt in grammar:
        global_addto_follow[nt]=set()
        global_follow_set[nt]=set()
    global_follow_set[global_start_symbol].add(ENDMARK)

def followset_rule_1(elements, follow_elements=[]):
    for i in range(0, len(elements)):
        ele = elements[i]
        if ele.type == ELE_TYPE.NONTERM:
            global_follow_set[ele.symbols[0]].update(elements_first_set(elements[i + 1:]+follow_elements) - {EMPTY})
        elif ele.type == ELE_TYPE.COMBI:
            combi_get_follow_rule1(ele, elements[i + 1:] + follow_elements)

def followset_rule_2(A:str, elements:list, follow_elements=[]):
    n=len(elements)
    for i in range(0, n):
        B:Element = elements[i]
        if B.type == ELE_TYPE.NONTERM:
            if EMPTY in elements_first_set(elements[i+1:]+follow_elements):
                global_addto_follow[A].add(B.symbols[0])
        elif B.type == ELE_TYPE.COMBI:
            #debug
            #if B.symbols[0].symbols[0]=="ConditionStatement":
            #    print(elements[i + 1:]+follow_elements)
            #    print(elements_first_set(elements[i + 1:]+follow_elements))
            #-----
            combi_get_follow_rule2(A, B, elements[i + 1:]+follow_elements)


def combi_get_follow_rule1(combi_ele, follow_elements):
    elements = combi_ele.symbols
    followset_rule_1(elements,follow_elements)
    if combi_ele.op == '+' or combi_ele.op == '*':
        if len(elements)>1:
            followset_rule_1([elements[-1]],elements+follow_elements)

def combi_get_follow_rule2(A, combi_ele,follow_elements):
    elements=combi_ele.symbols
    followset_rule_2(A, elements, follow_elements)
    if combi_ele.op == '+' or combi_ele.op == '*':
        if len(elements)>1:
            followset_rule_2(A, [elements[-1]],elements+follow_elements)


def get_rule1_followset(grammar):
    productions=grammar.values()
    for prod in productions:
        for line in prod['right']:
            followset_rule_1(line)

def get_addto_followset(grammar):
    productions = grammar.values()
    for prod in productions:
        A=prod['left']
        for line in prod['right']:
            followset_rule_2(A,line)


def followset_add(A,B, addto_dict):
    len1 = len(global_follow_set[B])
    global_follow_set[B].update(global_follow_set[A])
    if (len1 < len(global_follow_set[B])):
        follow_rule2_update_nonterm(B,addto_dict)


def follow_rule2_update_nonterm(A:str, addto_dict):
    for B in addto_dict[A]:
        followset_add(A,B,addto_dict)

def update_followset_rule2(addto_dict):
    for A,right in addto_dict.items():
        for B in right:
            followset_add(A,B,addto_dict)
def follow_set(grammar):
    init_follow_set(grammar)
    get_rule1_followset(grammar)
    get_addto_followset(grammar)
    update_followset_rule2(global_addto_follow)

if __name__ == '__main__':
    EBNF_path = "grammar.txt" if len(sys.argv)<=1 else sys.argv[1]
    global_start_symbol,global_grammar = read_EBNF(EBNF_path)
    process_right(global_grammar)
    print(global_start_symbol)
    #for x in grammar:
    #    print(f"{x} -> {grammar[x]}")
    first_set(global_grammar)
    follow_set(global_grammar)

    print_seperator(print_set,"first set")(global_first_set)
    print_seperator(print_set,"follow set")(global_follow_set)
    #print_seperator(print_set, "addto")(global_addto_follow)
    #print_seperator(print_set, "follow set")(global_follow_set)

