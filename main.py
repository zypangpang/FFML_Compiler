from constants import EBNF_OP_SYMBOL,EMPTY


global_first_set={}
global_grammar={}
class Element:
    """The element of grammar production right part"""

    def __init__(self, symbols, op=''):
        self.symbols = symbols
        self.op = op

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
                            symbols.append(item[:-2])
                            break
                        else:
                            symbols.append(item)
                        item = next(line, None)
                    right_elements.append(Element(symbols, item[-1]))
                else:
                    right_elements.append(Element([item]))
                item = next(line, None)
            new_right.append(right_elements)
        production['right'] = new_right

def nonterminal_first_set(left):
    productions = global_grammar[left]['right']
    fset=set()
    for line in productions:
        all_empty=True
        for ele in line:
            ele_first_set=element_first_set(ele)
            fset.update(ele_first_set - {EMPTY})
            if EMPTY not in ele_first_set:
                all_empty=False
                break
        if all_empty:
            fset.add(EMPTY)
    return fset


def combination_first_set(element):
    fset = set()
    all_empty = True
    for str in element.symbols:
        str_first_set = string_first_set(str)
        fset.update(str_first_set - {EMPTY})
        if EMPTY not in str_first_set:
            all_empty = False
            break
    if all_empty:
        fset.add(EMPTY)
    if element.op == '?' or element.op == '*':
        fset.add(EMPTY)

    return fset


def string_first_set(str):
    if str[0] == '"':
        return  {str[1]}
    elif str[0] == '<':
        return {str}
    else:
        return nonterminal_first_set(str)


def element_first_set(element):
    if element.op=='':
        str=element.symbols[0]
        if str not in global_first_set:
            global_first_set[str]=string_first_set(str)
        return global_first_set[str]
    else:
        return combination_first_set(element)

def first_set(grammar):
    for nt in grammar:
        if nt not in global_first_set:
            global_first_set[nt]=nonterminal_first_set(nt)

if __name__ == '__main__':
    EBNF_path = "grammar.txt"
    global_grammar = read_EBNF(EBNF_path)
    process_right(global_grammar)
    #for x in grammar:
    #    print(f"{x} -> {grammar[x]}")
    first_set(global_grammar)
    for x in global_first_set:
        print(f"{x} -> {global_first_set[x]}")

