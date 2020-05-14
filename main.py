import sys,itertools
from utils import format_print, print_set
from grammar_related import get_grammar_from_file
from first_follow_set import FirstFollowSet
from constants import EMPTY

def check_LL1(ff:FirstFollowSet):
    grammar=ff.get_grammar()
    #first_set=ff.first_set()
    follow_set=ff.follow_set()
    LL1=True
    for prod in grammar.values():
        A = prod['left']
        rights=prod['right']
        n=len(rights)
        for i in range(n-1):
            for j in range(i+1,n):
                alpha=rights[i]
                beta=rights[j]
                first_alpha=ff.elements_first_set(alpha)
                first_beta=ff.elements_first_set(beta)
                if first_alpha & first_beta:
                    print(f"first alpha x first beta: {A}")
                    LL1=False

                if EMPTY in first_alpha and first_beta & follow_set[A]:
                    print(f"first beta x follow A: {A}")
                    LL1=False

                if EMPTY in first_beta and first_alpha & follow_set[A]:
                    print(f"first alpha x follow A: {A}")
                    LL1=False
    return LL1

if __name__ == '__main__':
    EBNF_path = "grammar.txt" if len(sys.argv) <= 1 else sys.argv[1]
    global_start_symbol, global_grammar = get_grammar_from_file(EBNF_path)
    # for x in grammar:
    #    print(f"{x} -> {grammar[x]}")
    ff = FirstFollowSet(grammar=global_grammar, ss=global_start_symbol)
    first_set=ff.first_set()
    follow_set=ff.follow_set()

    #format_print(print, "start symbol")(global_start_symbol)
    #format_print(print_set, "first set", True)(first_set)
    #format_print(print_set, "follow set", True)(follow_set)
    # print_seperator(print_set, "addto")(global_addto_follow)
    print(check_LL1(ff))


