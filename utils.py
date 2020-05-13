from constants import TERM_BEGIN_CHARS

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

