from constants import EBNF_OP_SYMBOL


class Element:
    """The element of grammar production right part"""

    def __init__(self, symbols, op=''):
        self.symbols = symbols
        self.op = op

    def __str__(self):
        return f"Element({self.symbols} {self.op})"

    def __repr__(self):
        return f"({self.symbols} {self.op})"


def read_EBNF(file_path):
    grammar = []
    with open(file_path, "r") as f:
        line = f.readline()
        while line:
            production = {'left': line.split()[0], 'right': []}
            right = f.readline().split()
            while right[0] != ';':
                production['right'].append(right)
                right = f.readline().split()

            grammar.append(production)
            line = f.readline()
    return grammar


def process_right(grammar):
    for production in grammar:
        new_right = []
        for line in production['right']:
            right_elements = []
            line = iter(line)
            item = next(line, '#')
            while item != '#':
                if item[0] == '(':
                    item = item[1:]
                    symbols = []
                    while item != '#':
                        if item[-1] in EBNF_OP_SYMBOL:
                            symbols.append(item[:-2])
                            break
                        else:
                            symbols.append(item)
                        item = next(line, '#')
                    right_elements.append(Element(symbols, item[-1]))
                else:
                    right_elements.append(Element([item]))
                item = next(line, '#')
            new_right.append(right_elements)
        production['right'] = new_right


if __name__ == '__main__':
    EBNF_path = "grammar.txt"
    grammar = read_EBNF(EBNF_path)
    process_right(grammar)
    for x in grammar:
        print(x)
