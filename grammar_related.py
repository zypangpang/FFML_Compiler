from functools import reduce

from constants import EBNF_OP_SYMBOL, ELE_TYPE, TERM_BEGIN_CHARS,EMPTY
from utils import nonterm_name_generator,int_id_generator
#from global_var import  new_name_gen
from collections import defaultdict
#from global_var import global_int_id_gen
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


class Production:
    def __init__(self,id:int,left:str,elements:list):
        self.id=id
        self.left=left
        self.right_elements=elements

    def __str__(self):
        right_str = " ".join([ele.content for ele in self.right_elements])
        return f"{self.left}->{right_str}"

    def __repr__(self):
        right_str = " ".join([ele.content for ele in self.right_elements])
        return f"({self.id}:{self.left}->{right_str})"

    def __lt__(self, other):
        if not isinstance(other, Production):
           # don't attempt to compare against unrelated types
            return NotImplemented
        return self.right_elements<other.right_elements


'''
class Grammar:
    def __init__(self,ss,grammar):
        self.start_symbol=ss
        self.grammar=grammar

        self.production_map={}
        for x in grammar:
            for prod in grammar[x]:
                self.production_map[prod.id]=prod
'''

def get_production_map(grammar):
    production_map={}
    for x in grammar:
        for prod in grammar[x]:
            production_map[prod.id] = prod
    return production_map

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
            #production = {'left': left, 'right': []}
            productions=[]
            nonterms.append(left)
            right = f.readline().strip(strip_chars).split()
            while right[0] != endmark:
                productions.append({'left':left,'right':right})
                right = f.readline().strip(strip_chars).split()

            grammar[left] = productions
            line = f.readline().strip(strip_chars)
    return start_symbol, grammar,nonterms


def get_all_productions(grammar):
    return reduce(lambda prev, next: prev + next, grammar.values())


def process_right(grammar):
    int_id_gen=int_id_generator()

    grammar_new=defaultdict(list)
    all_productions=get_all_productions(grammar)
    for production in all_productions:
        left=production['left']
        line=production['right']
        right_elements=[]
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
        grammar_new[left].append(Production(int_id_gen.__next__(),left,right_elements))
    return grammar_new


def get_grammar_from_file(type, file_path,begin_alter,endmark):
    # EBNF_path = "grammar.txt" if len(sys.argv) <= 1 else sys.argv[1]
    start_symbol, grammar,nonterms = read_grammar(file_path, begin_alter, endmark)
    grammar=process_right(grammar)

    if type == 'EBNF':
        grammar=EBNF_to_BNF(grammar)
    elif type == 'BNF':
        pass
    else:
        raise Exception("Invalid grammar file type")

    sort_grammar(grammar)
    return start_symbol, grammar


def EBNF_to_BNF(grammar):
    int_id_gen=int_id_generator()
    new_name_gen = nonterm_name_generator("R_")

    def remove_EBNF_repetition(name_map, elements):
        new_grammar = {}
        new_elements = []
        for ele in elements:
            # Nested grouping is not supported
            if ele.type == ELE_TYPE.COMBI:

                symbol_str = " ".join([e.content for e in ele.content] + [ele.op])
                if symbol_str not in name_map:
                    name_map[symbol_str] = new_name_gen.__next__()
                new_name = name_map[symbol_str]

                #new_grammar[new_name] = {'left': new_name, 'right': []}
                new_grammar[new_name] = []
                new_rights = new_grammar[new_name]
                if ele.op == '?':
                    new_rights.append(Production(int_id_gen.__next__(), new_name,[Element(e.content) for e in ele.content]))
                    new_rights.append(Production(int_id_gen.__next__(),new_name,[Element(EMPTY)]))
                else:
                    if ele.op == '+':
                        new_elements.extend(ele.content)
                    new_rights.append(Production(int_id_gen.__next__(),new_name,[Element(e.content) for e in ele.content] + [Element(new_name)]))
                    new_rights.append(Production(int_id_gen.__next__(),new_name,[Element(EMPTY)]))
                new_elements.append(Element(new_name))
            else:
                new_elements.append(ele)
        return new_elements, new_grammar

    grammar_new={}
    name_map={}
    for X in grammar:
        prods=grammar[X]
        new_prods=[]
        for prod in prods:
            new_elements,new_grammar = remove_EBNF_repetition(name_map,prod.right_elements)
            new_prods.append(Production(int_id_gen.__next__(),X,new_elements))
            grammar_new={**grammar_new, **new_grammar}
        grammar_new[X]=new_prods
    return grammar_new

# deprecated. Not correct anymore.
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
    for prods in grammar.values():
        prods.sort()


def get_nullables(grammar):
    nullables = set()
    len1 = len(nullables)
    all_prods=get_all_productions(grammar)
    while True:
        for prod in all_prods:
            null = True
            for ele in prod.right_elements:
                if ele.content != EMPTY and ele.content not in nullables:
                    null = False
                    break
            if null:
                nullables.add(prod.left)
        if len(nullables) > len1:
            len1 = len(nullables)
        else:
            return nullables
'''
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
'''

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
    int_id_gen=int_id_generator()

    def replace_empty_nt(prod, i, cur_prod:list,res_prods):
        elements=prod.right_elements
        if i>=len(elements):
            res_prods.append(Production(int_id_gen.__next__(),prod.left, cur_prod.copy()))
            return
        cur_prod.append(elements[i])
        replace_empty_nt(prod,i+1,cur_prod,res_prods)
        cur_prod.pop()

        if elements[i].content in nullable_set:
            replace_empty_nt(prod,i+1,cur_prod,res_prods)

    new_grammar={}
    for X in grammar:
        prods=grammar[X]
        new_prods=[]
        for prod in prods:
            cur_prod=[]
            res_prods=[]
            if prod.right_elements[0].content != EMPTY:
                replace_empty_nt(prod,0,cur_prod,res_prods)
                new_prods.extend(res_prods)
        if new_prods:
            new_grammar[X]=new_prods
    return  new_grammar


def check_left_recursive(grammar,nullables=None):
    def check_recursive(nt, begin):
        prods = grammar[nt]
        for prod in prods:
            for ele in prod.right_elements:
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

    recursive_nts=set()
    #first_nonterms=defaultdict(set)
    for A in grammar:
        if check_recursive(A, A):
            recursive_nts.add(A)
    return recursive_nts

def left_factoring(grammar):
    max_id=max([prod.id for prod in get_all_productions(grammar)])
    int_id_gen = int_id_generator(max_id+1)

    def longest_prefix(prods):
        n=len(prods)
        longest_prefix=[]
        for i in range(n-1):
            cur_line=prods[i].right_elements
            for j in range(i+1,n):
                comp_line=prods[j].right_elements
                k=0
                while k<len(cur_line):
                    if k>=len(comp_line) or  cur_line[k]!=comp_line[k]:
                        break
                    k=k+1

                if k > len(longest_prefix):
                    longest_prefix=cur_line[:k]
        return longest_prefix

    new_name_gen = nonterm_name_generator("F_")
    changed_nts=set(grammar.keys())
    while changed_nts:
        new_changed=set()
        new_grammar={}
        for x in changed_nts:
            prods=grammar[x]
            lprefix=longest_prefix(prods)
            if lprefix:
                n = len(lprefix)
                new_changed.add(x)
                new_name=new_name_gen.__next__()
                new_grammar[new_name]=[]
                new_prods=[Production(int_id_gen.__next__(),x,[*lprefix, Element(new_name)])]
                for prod in prods:
                    line=prod.right_elements
                    if line[:n]==lprefix:
                        new_grammar[new_name].append(Production(int_id_gen.__next__(),new_name,
                                                                line[n:] if line[n:] else [Element(EMPTY)]))
                    else:
                        new_prods.append(prod)
                grammar[x]=new_prods
        changed_nts=new_changed
        grammar={**grammar,**new_grammar}
    return grammar





if __name__ == '__main__':
    a=[Element("X"),Element('"abc"')]
    for x in a:
        print(x.type)
    a.sort()
    print(a)
