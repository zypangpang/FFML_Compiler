from constants import ELE_TYPE
from grammar_related import Element
def remove_left_recursive(grammar):
    nonterminals=[A for A in grammar]
    n=len(nonterminals)
    for i in range(n):
        Ai = nonterminals[i]
        rights = grammar[Ai]['right']
        for j in range(i):
            Aj=nonterminals[j]
            change_dict={}
            for k in range(len(rights)):
                rhs=rights[k]
                if rhs[0].type == ELE_TYPE.NONTERM:
                    first_nt=rhs[0].symbols[0]
                    if first_nt == Aj:
                        new_prods=[Aj_prod + rhs[1:] for Aj_prod in grammar[Aj]['right']]
                        change_dict[k]=new_prods

                elif rhs[0].type == ELE_TYPE.COMBI:
                    first_nt = rhs[0].symbols[0].symbols[0]
                    if first_nt == Aj:
                        new_prods = []
                        for prod in grammar[Aj]['right']:
                            new_first_combi=Element([prod]+rhs[0].symbols[1:], rhs[0].op)
                            new_prods.append([new_first_combi]+rhs[1:])
                        change_dict[k]=new_prods
            for pos in change_dict:
                rights[pos:pos+1]=change_dict[pos]

        nt_prods=[]
        term_prods=[]
        for rhs in rights:
            if rhs[0].type==ELE_TYPE.NONTERM:
                if rhs[0].symbols[0]

        for rhs in rights:
            if rhs[0].type == ELE_TYPE.NONTERM:
                first_nt=rhs[0].symbols[0]
                if first_nt == Ai:
                    nt_prods=[]



