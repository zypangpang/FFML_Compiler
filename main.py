import sys
from utils import format_print, print_dict,output_formatted_grammar
from grammar_related import get_grammar_from_file, EBNF_to_BNF,remove_same_symbols,sort_grammar,get_nullable_nonterms,remove_empty_productions,check_left_recursive
from first_follow_set import FirstFollowSet
from constants import EMPTY

def check_nullable(ff: FirstFollowSet):
    grammar = ff.get_grammar()
    first_set=ff.first_set()
    for A in grammar:
        if EMPTY in first_set[A]:
            print(A)

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
    path = "texts/grammar_BNF.txt" if len(sys.argv) <= 1 else sys.argv[1]
    start_symbol, grammar,nonterms = get_grammar_from_file('BNF',path,'|',';')
    #format_print(print_set, "BNF",True)(grammar,nonterms)
    #format_print(print_set, "BNF",True)(new_grammar)
    #format_print(print_set, "BNF",True)(new_grammar)
    #nullables=get_nullable_nonterms(grammar)
    #remove_empty_productions(grammar,nullables)
    #output_formatted_grammar(start_symbol,grammar,'->','|',';')

    rnts = check_left_recursive(grammar)
    if rnts:
        print(rnts)


    #remove_same_symbols(new_grammar)

    #ff = FirstFollowSet(grammar=grammar, ss=start_symbol)
    #first_set=ff.first_set()
    #follow_set=ff.follow_set()

    #format_print(print, "start symbol")(start_symbol)
    #format_print(print_set, "first set", True)(first_set,nonterms)
    #format_print(print_set, "follow set", True)(follow_set,nonterms)
    # print_seperator(print_set, "addto")(global_addto_follow)

    #print(check_LL1(ff))
    #check_nullable(ff)


