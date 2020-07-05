import sys
from utils import print_tree,SyntaxError,LexicalError
from grammar_related import get_grammar_from_file, left_factoring, get_production_map,get_all_terms,get_all_productions
from first_follow_set import FirstFollowSet
from constants import EMPTY
from lexer import Lexer,get_symbol_table,get_dfa_from_file
from parser import  Parser
from preprocess import Preprocessor
from translator import ASTVisitor


def check_nullable(ff: FirstFollowSet):
    grammar = ff.get_grammar()
    first_set = ff.first_set()
    for A in grammar:
        if EMPTY in first_set[A]:
            print(A)

def get_parse_table(grammar):
     grammar = left_factoring(grammar)
     ff = FirstFollowSet(grammar=grammar, ss=start_symbol)
     #first_set = ff.first_set()
     #follow_set = ff.follow_set()

     #format_print(print, "start symbol")(start_symbol)
     #format_print(print_dict, "first set", True)(first_set)
     #format_print(print_dict, "follow set", True)(follow_set)
     #print_seperator(print_set, "addto")(global_addto_follow)

     #print(ff.check_LL1())

     M = ff.get_parse_table()
     return M
     #p_map = get_production_map(grammar)
     #for X in M:
     #   print(f"{X}:")
     #   for a in M[X]:
     #       print(f"    {a}: {p_map[M[X][a]]}")
    # for p in M[X][a]:
    #    print(f"        {p_map[p]}")
def output_parse_table(M,endmark):
    for x in M:
        print(f"{x} :")
        for a,b in M[x].items():
            print(f"    {a} {b}")
        print(endmark)
def read_parse_table(file_path,endmark):
    M = {}
    strip_chars = '\n\t '
    with open(file_path, "r") as f:
        line = f.readline().strip(strip_chars)
        while line:
            row = line.split()[0]
            # production = {'left': left, 'right': []}
            col = {}
            right = f.readline().strip(strip_chars).split()
            while right[0] != endmark:
                col[right[0]]=int(right[1])
                right = f.readline().strip(strip_chars).split()
            M[row] = col
            line = f.readline().strip(strip_chars)
    return M

if __name__ == '__main__':
    path = "texts/grammar_LL1.txt" if len(sys.argv) <= 1 else sys.argv[1]
    M_path="texts/LL1_table.txt"
    start_symbol, grammar = get_grammar_from_file('BNF', path, '|', ';')

    #t=get_all_productions(grammar)
    #t.sort()
    #for p in t:
    #    print(p)

    #grammar=left_factoring(grammar)
    #output_formatted_grammar(start_symbol,grammar,'->','|',';')

    #parse_table=get_parse_table(grammar)
    #output_parse_table(parse_table,"#")

    parse_table=read_parse_table(M_path,'#')

    dfa_path = 'lexer/dfa.txt'
    code_path = 'test_code.txt'
    preprocessor=Preprocessor(code_path)
    new_code_path=preprocessor.process()
    code_file = open(new_code_path, 'r')

    lexer = Lexer(code_file, get_dfa_from_file(dfa_path), get_symbol_table())
    parser=Parser(grammar,parse_table,start_symbol,lexer)
    root = parser.parse_AST()
    code_file.close()

    '''
    try:
        root=parser.parse_AST()
    except SyntaxError as e:
        print("Syntax Error")
        print(e.desc)
    except LexicalError as e:
        print("Lexical Error")
        print(e.desc)
    else:
        print_tree(root,0)
    '''
    #print_tree(root, 0)

    visitor=ASTVisitor()
    policies=visitor.visit(root)
    policy_num=len(policies)
    print(f"Generated {policy_num} {'policies' if policy_num > 1 else 'policy'}.")
    #print(visitor.symbol_table)
    #for p in policies:
    #    print(p)

    print("Done.")

