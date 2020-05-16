from constants import TERM_BEGIN_CHARS,ELE_TYPE

def nonterm_name_generator():
    now='A'
    while True:
        yield 'I_'+now
        # add 1
        new=[]
        carry = 1
        for c in reversed(now):
            i=ord(c)-ord('A')
            remain=(i+carry)%26
            carry=(i+carry)//26
            #print(remain,carry)
            new.append(chr(ord('A')+remain))
            #print(new)
        if carry > 0:
            new.append(chr(ord('A')-1+carry))
        now=''.join(reversed(new))

def format_print(func, title, table=False):
    dash_number=70
    def inner_func(*args,**kwargs):
        print('=' * dash_number)
        if table:
            print(f"SYMBOL\t\t{title.upper()}")
        else:
            print(title.upper())
        print('-' * dash_number)
        func(*args, **kwargs)
        print('_' * dash_number)
    return inner_func

def print_set(global_set,key_order=None):
    if key_order:
        nts=key_order
    else:
        nts=sorted([x for x in global_set])
    for x in nts:
        if x[0] not in TERM_BEGIN_CHARS:
            #print(f"{x} \t {sorted([i for i in global_set[x]])}")
            print(f"{x} \t {global_set[x]}")

def output_formatted_grammar(start_symbol, grammar, deduce_symbol, begin_alter, endmark):
    print(start_symbol)
    indent="    "
    for x in grammar:
        print(f"{x} {deduce_symbol}")
        first=True
        for line in grammar[x]['right']:
            if first:
                output=indent+"  "
                first=False
            else:
                output=indent+begin_alter+" "
            output = output + " ".join([e.content for e in line])
            print(output)
        print(indent+endmark)

def output_formatted_grammar_online(start_symbol, grammar, deduce_symbol, begin_alter, endmark):
    print(start_symbol)
    indent="    "
    for x in grammar:
        print(f"{x} {deduce_symbol}")
        first=True
        for line in grammar[x]['right']:
            if first:
                output=indent+" "
                first=False
            else:
                output=indent+begin_alter+" "
            for ele in line:
                content=ele.content.strip('"').lower() if ele.type==ELE_TYPE.TERM else ele.content
                output=output + f" {content}"
            print(output)
        print(indent+endmark)

