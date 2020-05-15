from constants import TERM_BEGIN_CHARS

def nonterm_name_generator():
    now='A'
    while True:
        yield '_'+now
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

def print_set(global_set):
    for x in global_set:
        if x[0] not in TERM_BEGIN_CHARS:
            print(f"{x} \t {global_set[x]}")


