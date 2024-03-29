from constants import TERM_BEGIN_CHARS, ELE_TYPE,LOG_LEVEL,DEBUG,GUI,translator_configs
import re,sys,logging
from gui.utils import add_log


class SyntaxError(Exception):
    def __init__(self,type,line_number,desc):
        self.type=type
        self.desc=desc
        self.line_number=line_number
    def __str__(self):
        return f"Syntax error {self.type}\n{self.desc}"

class LexicalError(Exception):
    def __init__(self,type,line_number,desc):
        self.type=type
        self.desc=desc
        self.line_number=line_number
    def __str__(self):
        return f"Lexical error {self.type}\n{self.desc}"

def nonterm_name_generator(begin_chars):
    now = 'A'
    while True:
        yield begin_chars + now
        # add 1
        new = []
        carry = 1
        for c in reversed(now):
            i = ord(c) - ord('A')
            remain = (i + carry) % 26
            carry = (i + carry) // 26
            # print(remain,carry)
            new.append(chr(ord('A') + remain))
            # print(new)
        if carry > 0:
            new.append(chr(ord('A') - 1 + carry))
        now = ''.join(reversed(new))


def int_id_generator(begin=0):
    while True:
        yield begin
        begin = begin + 1


def format_print(func, title, table=False):
    dash_number = 70

    def inner_func(*args, **kwargs):
        print('=' * dash_number)
        if table:
            print(f"SYMBOL\t\t{title.upper()}")
        else:
            print(title.upper())
        print('-' * dash_number)
        func(*args, **kwargs)
        print('_' * dash_number)

    return inner_func

'''
def log_print(content,level=LOG_LEVEL.INFO):
    #level_str={
    #    LOG_LEVEL.INFO:"info",
    #    LOG_LEVEL.WARN: "Warning",
    #    LOG_LEVEL.ERROR: "ERROR",
    #}
    #level_s=level_str[level]
    if DEBUG:
        print(f">>> {level.name.upper()}: {content}")
    else:
        with open

    if not DEBUG:
        if level == LOG_LEVEL.INFO:
            return

    print(f">>> {level.name.upper()}: {content}")
'''

def log_collect(content,level='warning'):
    if GUI[0]:
        add_log(content,level)
    getattr(logging,level)(content)


def print_dict(my_dict, key_order=None):
    if key_order:
        nts = key_order
    else:
        # nts=sorted([x for x in my_dict])
        nts = [x for x in my_dict]
    for x in nts:
        if x[0] not in TERM_BEGIN_CHARS:
            # print(f"{x} \t {sorted([i for i in global_set[x]])}")
            print(f"{x} \t {my_dict[x]}")


def output_formatted_grammar(start_symbol, grammar, deduce_symbol, begin_alter, endmark):
    print(start_symbol)
    indent = "    "
    for x in grammar:
        print(f"{x} {deduce_symbol}")
        first = True
        for line in grammar[x]:
            line = line.right_elements
            if first:
                output = indent + "  "
                first = False
            else:
                output = indent + begin_alter + " "
            output = output + " ".join([f'"{e.content}"' if e.type==ELE_TYPE.TERM else e.content for e in line])
            print(output)
        print(indent + endmark)


def output_formatted_grammar_online(start_symbol, grammar, deduce_symbol, begin_alter, endmark):
    print(start_symbol)
    indent = "    "
    for x in grammar:
        print(f"{x} {deduce_symbol}")
        first = True
        for line in grammar[x]['right']:
            if first:
                output = indent + " "
                first = False
            else:
                output = indent + begin_alter + " "
            for ele in line:
                content = ele.content.strip('"').lower() if ele.type == ELE_TYPE.TERM else ele.content
                output = output + f" {content}"
            print(output)
        print(indent + endmark)


def prod_to_str(left, right):
    right_str = " ".join([ele.content for ele in right])
    return f"{left}->{right_str}"

def out_tree(root,out_file=None):
    file = bool(out_file)
    out_file=open(out_file,"w") if out_file else sys.stdout
    str_list=get_tree_str_list(root)
    for s in str_list:
        out_file.write(s)
        out_file.write('\n')
    if file: out_file.close()


def get_tree_str_list(root,depth=0,last=False):
    out_list=[]
    if last:
        out_list.append("┆ "*depth+"┖┄"+root.type)
    else:
        out_list.append("┆ " * depth  + "┠┄" + root.type)
    if root.children:
        for c in root.children[:-1]:
            out_list += get_tree_str_list(c,depth+1)
        out_list+=get_tree_str_list(root.children[-1],depth+1,True)
    return out_list

class MyTemplate:
    def __init__(self,meta_str):
        self.meta_str=meta_str
        self.__emtpy_dict={}
        self.__process_meta()

    def __process_meta(self):
        p=re.compile("\\$(\\w+)\\$")
        m=p.findall(self.meta_str)
        for x in m:
            self.__emtpy_dict[x]=None

    def set_value(self,empty,val):
        if empty not in self.__emtpy_dict:
            raise Exception(f"{empty} template param not exist")
        self.__emtpy_dict[empty]=val
        return self

    def get_key_dict(self):
        return self.__emtpy_dict

    def get_key_value(self):
        return self.__emtpy_dict.values()

    def get_code(self):
        code: str=self.meta_str
        for empty,val in self.__emtpy_dict.items():
            if val is None:
                raise Exception(f"{empty} not set")
            code=code.replace(f"${empty}$",val)
        return code
    def __str__(self):
        return self.get_code()

class ListTemplate:
    def __init__(self,conj):
        self.conj=conj
        self.l=None

    def set_list(self, l):
        self.l = [f"( {item} )" for item in l]
        return self

    def get_code(self):
        return f" {self.conj} ".join(self.l)

    def __str__(self):
        return self.get_code()


def bt(s):
    if isinstance(s,list):
        return [f"`{item}`" for item in s]
    else:
        return f"`{s}`"

def log_info(func):
    def inner(*args,**kwargs):
        log_print(f"call {func.__name__}")
        return func(*args,**kwargs)
    return inner

def get_template_from_file(path: str):
    with open(path) as f:
        template=MyTemplate(f.read())
    return template

def output_to_file(path,content):
    with open(path) as f:
        f.write(str(content))


if __name__ == '__main__':
    test_str = "abc$NAME$ ext$TABLE$ 'd12'"
    tp=MyTemplate(test_str)
    tp.set_value("NAME","test")
    tp.set_value("TABLE","abc")
    print(tp.get_code())





