import sys
from utils import format_print, print_set
from grammar_related import get_grammar_from_file
from first_follow_set import FirstFollowSet

if __name__ == '__main__':
    EBNF_path = "grammar.txt" if len(sys.argv) <= 1 else sys.argv[1]
    global_start_symbol, global_grammar = get_grammar_from_file(EBNF_path)
    # for x in grammar:
    #    print(f"{x} -> {grammar[x]}")
    ff = FirstFollowSet(grammar=global_grammar, ss=global_start_symbol)

    format_print(print, "start symbol")(global_start_symbol)
    format_print(print_set, "first set", True)(ff.first_set())
    format_print(print_set, "follow set", True)(ff.follow_set())
    # print_seperator(print_set, "addto")(global_addto_follow)
