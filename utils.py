from constants import TERM_BEGIN_CHARS, ELE_TYPE,LOG_LEVEL
import re

class SyntaxError(Exception):
    def __init__(self,type,desc):
        self.type=type
        self.desc=desc
    def __str__(self):
        return f"Syntax error:\ntype: {self.type}\n{self.desc}"
class LexicalError(Exception):
    def __init__(self,type,desc):
        self.type=type
        self.desc=desc
    def __str__(self):
        return f"Lexical error:\ntype: {self.type}\n{self.desc}"

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

def log_print(content,level=LOG_LEVEL.INFO):
    #level_str={
    #    LOG_LEVEL.INFO:"info",
    #    LOG_LEVEL.WARN: "Warning",
    #    LOG_LEVEL.ERROR: "ERROR",
    #}
    #level_s=level_str[level]
    print(f">>> {level.name.upper()}: {content}")


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

def print_tree(root,depth,last=False):
    if last:
        print("┆ "*depth+"┖┄"+root.type)
    else:
        print("┆ " * depth  + "┠┄" + root.type)
    for c in root.children[:-1]:
        print_tree(c,depth+1)
    if root.children:
        print_tree(root.children[-1],depth+1,True)

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

    def get_code(self):
        code:str=self.meta_str
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

if __name__ == '__main__':
    test_str = "abc$NAME$ ext$TABLE$ 'd12'"
    tp=MyTemplate(test_str)
    tp.set_value("NAME","test")
    tp.set_value("TABLE","abc")
    print(tp.get_code())





