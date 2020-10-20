import sys,fire,logging.config

from log_config import logging_config
logging.config.dictConfig(logging_config)

from utils import out_tree,SyntaxError,LexicalError
from grammar_related import get_grammar_from_file, left_factoring, get_production_map,get_all_terms,get_all_productions
from first_follow_set import FirstFollowSet
from constants import EMPTY
from lexer import Lexer,get_symbol_table,get_dfa_from_file
from parser import  Parser
from preprocess import Preprocessor
#from translator import ASTVisitor
from translator_adv import ASTVisitor


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

class Main:
    """
    FFML parser and translator.
    """
    def parse(self, in_file=None, ast:bool=False, output:bool=False, out_file=None):
        '''
        Parse input from in_file or stdin
        :param in_file: input code file path. If None, read from stdin.
        :param ast: bool. output ast or syntax tree.
        :param output: bool. output or only check grammar.
        :param out_file: output file path. If None, output to stdout.
        :return:
        '''
        try:
            self.__parse(in_file,ast,output,out_file)
        except SyntaxError as e:
            print(e)
        except LexicalError as e:
            print(e)
        except:
            print("Unexpected error.")
            raise


    def __parse(self, in_file, ast, output, out_file):
        path = "texts/grammar_LL1.txt"
        start_symbol, grammar = get_grammar_from_file('BNF', path, '|', ';')

        M_path = "texts/LL1_table.txt"
        parse_table = read_parse_table(M_path, '#')

        preprocessor = Preprocessor(in_file)
        new_code_path = preprocessor.process()

        with open(new_code_path,'r') as code_file:
            dfa_path = 'lexer/dfa.txt'
            lexer = Lexer(code_file, get_dfa_from_file(dfa_path), get_symbol_table())
            parser = Parser(grammar, parse_table, start_symbol, lexer)
            root = parser.parse_AST() if ast else parser.parse_tree()
            if output:
                out_tree(root,out_file)
        return root


    def translate(self,in_file=None,out_file=None, readable=False):
        '''
        Translate input codes to Flink SQL or Flink Java.
        :param in_file: Input code file path. If None, read stdin.
        :param out_file: Output file path. If None, write to stdout.
        :return:
        '''
        try:
            root=self.__parse(in_file, ast=True,out_file=None,output=False)
        except SyntaxError as e:
            print(e)
            return
        except LexicalError as e:
            print(e)
            return
        except:
            print("Unexpected error.")
            raise

        visitor = ASTVisitor()
        policies = visitor.visit(root)
        policy_num = len(policies)
        logging.info(f"Generated {policy_num} {'policies' if policy_num > 1 else 'policy'}.")

        file=bool(out_file)
        out_file=open(out_file,'w') if out_file else sys.stdout
        for p in policies:
            if readable:
                out_file.write(str(p))
            else:
                out_file.writelines(s+'\n' for s in p)
        if file: out_file.close()

if __name__ == '__main__':
    logging.info("FFML translator started.")
    fire.Fire(Main)
