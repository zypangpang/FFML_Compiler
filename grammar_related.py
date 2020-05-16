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


def read_grammar(file_path, begin_alter, endmark):
    grammar = {}
    nonterms=[]
    strip_chars='\n\t '+begin_alter
    with open(file_path, "r") as f:
        first_line = f.readline().strip(strip_chars)
        start_symbol = first_line
        line = f.readline().strip(strip_chars)
        while line:
            left = line.split()[0]
            production = {'left': left, 'right': []}
            nonterms.append(left)
            right = f.readline().strip(strip_chars).split()
            while right[0] != endmark:
                production['right'].append([Element(str) for str in right])
                right = f.readline().strip(strip_chars).split()

            grammar[left] = production
            line = f.readline().strip(strip_chars)
    return start_symbol, grammar,nonterms


def process_right(grammar):
    for _, production in grammar.items():
        new_right = []
        for line in production['right']:
            line = [e.content for e in line]
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


def get_grammar_from_file(type, file_path,begin_alter,endmark):
    # EBNF_path = "grammar.txt" if len(sys.argv) <= 1 else sys.argv[1]
    start_symbol, grammar,nonterms = read_grammar(file_path, begin_alter, endmark)
    if type == 'EBNF':
        process_right(grammar)
        grammar=EBNF_to_BNF(grammar)
    elif type == 'BNF':
        pass
    else:
        raise Exception("Invalid grammar file type")
    sort_grammar(grammar)
    return start_symbol, grammar,nonterms



def remove_EBNF_repetition(name_map,elements):
    new_grammar={}
    new_elements=[]
    for ele in elements:
        # Nested grouping is not supported
        if ele.type == ELE_TYPE.COMBI:

            symbol_str=" ".join([e.content for e in ele.content]+[ele.op])
            if symbol_str not in name_map:
                name_map[symbol_str]=new_name_gen.__next__()
            new_name = name_map[symbol_str]

            new_grammar[new_name]={'left':new_name,'right':[]}
            new_rights=new_grammar[new_name]['right']
            if ele.op == '?':
                new_rights.append([Element(e.content) for e in ele.content])
                new_rights.append([Element(EMPTY)])
            else:
                if ele.op == '+':
                    new_elements.extend(ele.content)
                new_rights.append([Element(e.content) for e in ele.content]+[Element(new_name)] )
                new_rights.append([Element(EMPTY)])
            new_elements.append(Element(new_name))
        else:
            new_elements.append(ele)
    return new_elements, new_grammar


def EBNF_to_BNF(grammar):
    grammar_new={}
    name_map={}
    for X in grammar:
        rights=grammar[X]['right']
        new_rights=[]
        for line in rights:
            new_elements,new_grammar = remove_EBNF_repetition(name_map,line)
            new_rights.append(new_elements)
            grammar_new={**grammar_new, **new_grammar}
        grammar_new[X]={'left':X,'right':new_rights}
    return grammar_new

def remove_same_symbols(grammar):
    def dfs(G, name,group,visited):
        if name in group:
            return
        group.add(name)
        visited.add(name)
        for node in G[name]:
            dfs(G, node, group,visited)

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
    visited=set()
    for x in nonterms:
        if x not in visited:
            ans[x]=set()
            dfs(same,x,ans[x],visited)
    print(ans)

def sort_grammar(grammar):
    for prod in grammar.values():
        prod['right'].sort()

def get_nullables(grammar):
    nullables=set()
    len1=len(nullables)
    while True:
        for prod in grammar.values():
            A=prod['left']
            rights = prod['right']
            for line in rights:
                null=True
                for ele in line:
                    if ele.content != EMPTY and ele.content not in nullables:
                        null=False
                        break
                if null:
                    nullables.add(A)
                    break
        if len(nullables) > len1:
            len1=len(nullables)
        else:
            return nullables

# deprecated. Use get_nullables instead.
def get_nullable_nonterms(grammar):
    nullable_nts=set()
    def is_nullable(element):
        if element.content == EMPTY:
            return True
        if element.type == ELE_TYPE.TERM:
            return False
        if element.content in nullable_nts:
            return True
        for line in grammar[element.content]['right']:
            nullable = True
            for ele in line:
                if not is_nullable(ele):
                    nullable=False
                    break
            if nullable:
                nullable_nts.add(element.content)
                return True
        return False
    for x in grammar:
        if x not in nullable_nts and is_nullable(Element(x)):
            nullable_nts.add(x)
    return nullable_nts


def remove_empty_productions(grammar,nullable_set):
    def replace_empty_nt(elements, i, cur_prod:list,res_prods):
        if i>=len(elements):
            res_prods.append(cur_prod.copy())
            return
        cur_prod.append(elements[i])
        replace_empty_nt(elements,i+1,cur_prod,res_prods)
        cur_prod.pop()

        if elements[i].content in nullable_set:
            replace_empty_nt(elements,i+1,cur_prod,res_prods)

    for prod in grammar.values():
        rights=prod['right']
        new_rights=[]
        for line in rights:
            cur_prod=[]
            res_prods=[]
            if line[0].content != EMPTY:
                replace_empty_nt(line,0,cur_prod,res_prods)
                new_rights.extend(res_prods)
        prod['right']=new_rights


def check_left_recursive(grammar,nullables=None):
    def check_recursive(nt, begin):
        rights = grammar[nt]['right']
        for line in rights:
            for ele in line:
                if ele.type == ELE_TYPE.TERM:
                    break
                if ele.content == begin:
                    return True
                if check_recursive(ele.content, begin):
                    return True
                if ele.content not in nullables:
                    break
        return False

    if not nullables:
        nullables=get_nullables(grammar)
        print(nullables)
    recursive_nts=set()
    #first_nonterms=defaultdict(set)
    for A in grammar:
        if check_recursive(A, A):
            recursive_nts.add(A)
    return recursive_nts



if __name__ == '__main__':
    a=[Element("X"),Element('"abc"')]
    for x in a:
        print(x.type)
    a.sort()
    print(a)
