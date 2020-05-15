from constants import EBNF_OP_SYMBOL, ELE_TYPE, TERM_BEGIN_CHARS,EMPTY
from global_var import  new_name_gen
from collections import defaultdict


class Element:
    """The element of grammar production right part"""

    def __init__(self, content, op=''):
        self.content = content
        self.op = op
        if self.op != '':
            self.type = ELE_TYPE.COMBI
        elif self.content[0] in TERM_BEGIN_CHARS:
            self.type = ELE_TYPE.TERM
        else:
            self.type = ELE_TYPE.NONTERM

    def __str__(self):
        return f"Element({self.content} {self.op})"

    def __repr__(self):
        return f"({self.content} {self.op})"

    def __eq__(self, other):
        if not isinstance(other, Element):
            # don't attempt to compare against unrelated types
            return NotImplemented

        return self.content == other.content and self.type == other.type

    def __lt__(self, other):
        if not isinstance(other, Element):
           # don't attempt to compare against unrelated types
            return NotImplemented
        if self.type==ELE_TYPE.NONTERM and other.type==ELE_TYPE.TERM:
            return True
        if self.type==ELE_TYPE.TERM and other.type==ELE_TYPE.NONTERM:
            return False

        return self.content < other.content


def read_EBNF(file_path):
    grammar = {}
    with open(file_path, "r") as f:
        first_line = f.readline().strip()
        start_symbol = first_line
        line = f.readline()
        while line:
            left = line.split()[0]
            production = {'left': left, 'right': []}
            right = f.readline().strip('\n\t |').split()
            while right[0] not in ';.':
                production['right'].append(right)
                right = f.readline().split()

            grammar[left] = production
            line = f.readline()
    return start_symbol, grammar


def process_right(grammar):
    for _, production in grammar.items():
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
                            symbols.append(Element(item[:-2]))
                            break
                        else:
                            symbols.append(Element(item))
                        item = next(line, None)
                    right_elements.append(Element(symbols, item[-1]))
                else:
                    right_elements.append(Element(item))
                item = next(line, None)
            new_right.append(right_elements)
        production['right'] = new_right


def get_grammar_from_file(EBNF_path):
    # EBNF_path = "grammar.txt" if len(sys.argv) <= 1 else sys.argv[1]
    start_symbol, grammar = read_EBNF(EBNF_path)
    process_right(grammar)
    return start_symbol, grammar



def remove_EBNF_repetition(elements):
    new_grammar={}
    new_elements=[]
    for ele in elements:
        if ele.type == ELE_TYPE.COMBI:
            new_name=new_name_gen.__next__()
            new_grammar[new_name]={'left':new_name,'right':[]}
            new_rights=new_grammar[new_name]['right']
            new_elements.append(Element(new_name))
            if ele.op == '?':
                new_rights.append([Element(e.content) for e in ele.content])
                new_rights.append([Element(EMPTY)])
            elif ele.op == '*':
                new_rights.append([Element(new_name)]+[Element(e.content) for e in ele.content])
                new_rights.append([Element(EMPTY)])
            elif ele.op == '+':
                new_rights.append([Element(new_name)]+[Element(e.content) for e in ele.content])
        else:
            new_elements.append(ele)
    return new_elements, new_grammar


def EBNF_to_BNF(grammar):
    grammar_new={}
    for X in grammar:
        rights=grammar[X]['right']
        new_rights=[]
        for line in rights:
            new_elements,new_grammar = remove_EBNF_repetition(line)
            new_rights.append(new_elements)
            grammar_new={**grammar_new, **new_grammar}
        grammar_new[X]={'left':X,'right':new_rights}
    return grammar_new

def remove_same_symbols(grammar):
    def dfs(G, name,group):
        if name in group:
            return
        group.add(name)
        for node in G[name]:
            dfs(G, node, group)

    same=defaultdict(list)
    nonterms=[x for x in grammar]
    n=len(nonterms)
    for i in range(n-1):
        A=nonterms[i]
        for j in range(i+1,n):
            B=nonterms[j]
            if(grammar[A]['right']==grammar[B]['right']):
                same[A].append(B)
                same[B].append(A)
    ans={}
    for x in nonterms:
        if x not in ans:
            ans[x]=set()
            dfs(same,x,ans[x])
    print(ans)

def sort_grammar(grammar):
    for prod in grammar.values():
        prod['right'].sort()

if __name__ == '__main__':
    a=[Element("X"),Element('"abc"')]
    for x in a:
        print(x.type)
    a.sort()
    print(a)
