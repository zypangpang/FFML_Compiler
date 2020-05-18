import sys
from utils import format_print, print_dict, output_formatted_grammar
from grammar_related import get_grammar_from_file, left_factoring, get_production_map
from first_follow_set import FirstFollowSet
from constants import EMPTY


def check_nullable(ff: FirstFollowSet):
    grammar = ff.get_grammar()
    first_set = ff.first_set()
    for A in grammar:
        if EMPTY in first_set[A]:
            print(A)


if __name__ == '__main__':
    path = "texts/grammar_BNF.txt" if len(sys.argv) <= 1 else sys.argv[1]
    start_symbol, grammar = get_grammar_from_file('BNF', path, '|', ';')
    # format_print(print_dict, "Production",True)(grammar)
    # format_print(print_set, "BNF",True)(new_grammar)
    # format_print(print_set, "BNF",True)(new_grammar)
    # nullables=get_nullables(grammar)
    # print(nullables)
    # grammar=remove_empty_productions(grammar,nullables)
    # output_formatted_grammar(start_symbol,grammar,'->','|',';')

    # rnts = check_left_recursive(grammar)
    # print(rnts)
    grammar = left_factoring(grammar)
    # output_formatted_grammar(start_symbol,grammar,'->','|',';')
    format_print(print_dict, "Prod", True)(grammar)

    # remove_same_symbols(new_grammar)

    ff = FirstFollowSet(grammar=grammar, ss=start_symbol)
    first_set = ff.first_set()
    follow_set = ff.follow_set()

    # format_print(print, "start symbol")(start_symbol)
    # format_print(print_dict, "first set", True)(first_set)
    # format_print(print_dict, "follow set", True)(follow_set)
    # print_seperator(print_set, "addto")(global_addto_follow)

    print(ff.check_LL1())

    M = ff.get_parse_table(True)
    p_map = get_production_map(grammar)
    for X in M:
        print(f"{X}:")
        for a in M[X]:
            print(f"    {a}: {p_map[M[X][a]]}")
            # for p in M[X][a]:
            #    print(f"        {p_map[p]}")
