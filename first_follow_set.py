from constants import EMPTY, ELE_TYPE, ENDMARK
from grammar_related import Element, get_all_productions
from collections import defaultdict


class FirstFollowSet:
    def __init__(self, grammar, ss):
        self.__has_first = False
        self.__has_follow = False
        self.__first_set = {}
        self.__follow_set = {}
        self.__grammar = grammar
        self.__addto_follow = {}
        self.__start_symbol = ss
        # self.__production_map={}
        # for x in grammar:
        #    for prod in grammar[x]:
        #        self.__production_map[prod.id] = prod

    def elements_first_set(self, elements):
        fset = set()
        all_empty = True
        for ele in elements:
            ele_first_set = self.element_first_set(ele)
            fset.update(ele_first_set - {EMPTY})
            if EMPTY not in ele_first_set:
                all_empty = False
                break
        if all_empty:
            fset.add(EMPTY)
        return fset

    def nonterminal_first_set(self, left):
        productions = self.__grammar[left]
        fset = set()
        for prod in productions:
            fset.update(self.elements_first_set(prod.right_elements))
        return fset

    '''
    def combination_first_set(self, element):
        fset = self.elements_first_set(element.content)
        if element.op == '?' or element.op == '*':
            fset.add(EMPTY)
        return fset
    '''

    # def string_first_set(str):
    #    if str[0] in f'"<{EMPTY}':
    #        return {str}
    #    else:
    #        return nonterminal_first_set(str)

    def element_first_set(self, element):
        # print(element)
        if element.type == ELE_TYPE.TERM:
            return {element.content}
        elif element.type == ELE_TYPE.NONTERM:
            str = element.content
            if str not in self.__first_set:
                self.__first_set[str] = self.nonterminal_first_set(str)
            return self.__first_set[str]
        # elif element.type == ELE_TYPE.COMBI:
        #    return self.combination_first_set(element)
        else:
            raise Exception("invalid element type")

    def init_follow_set(self):
        for nt in self.__grammar:
            self.__addto_follow[nt] = set()
            self.__follow_set[nt] = set()
        self.__follow_set[self.__start_symbol].add(ENDMARK)

    def followset_rule_1(self, elements):
        for i in range(0, len(elements)):
            ele = elements[i]
            if ele.type == ELE_TYPE.NONTERM:
                self.__follow_set[ele.content].update(
                    self.elements_first_set(elements[i + 1:]) - {EMPTY})
            # elif ele.type == ELE_TYPE.COMBI:
            #    self.combi_get_follow_rule1(ele, elements[i + 1:] + follow_elements)

    def followset_rule_2(self, A: str, elements: list):
        n = len(elements)
        for i in range(0, n):
            B: Element = elements[i]
            if B.type == ELE_TYPE.NONTERM:
                if EMPTY in self.elements_first_set(elements[i + 1:]):
                    self.__addto_follow[A].add(B.content)
            # elif B.type == ELE_TYPE.COMBI:
            # debug
            # if B.symbols[0].symbols[0]=="ConditionStatement":
            #    print(elements[i + 1:]+follow_elements)
            #    print(elements_first_set(elements[i + 1:]+follow_elements))
            # -----
            #    self.combi_get_follow_rule2(A, B, elements[i + 1:] + follow_elements)

    '''
    def combi_get_follow_rule1(self, combi_ele, follow_elements):
        elements = combi_ele.content
        self.followset_rule_1(elements, follow_elements)
        if combi_ele.op == '+' or combi_ele.op == '*':
            if len(elements) > 1:
                self.followset_rule_1([elements[-1]], elements + follow_elements)

    def combi_get_follow_rule2(self, A, combi_ele, follow_elements):
        elements = combi_ele.content
        self.followset_rule_2(A, elements, follow_elements)
        if combi_ele.op == '+' or combi_ele.op == '*':
            if len(elements) > 1:
                self.followset_rule_2(A, [elements[-1]], elements + follow_elements)
    '''

    def get_rule1_followset(self):
        # productions = self.__grammar.values()
        all_prods = get_all_productions(self.__grammar)
        for prod in all_prods:
            self.followset_rule_1(prod.right_elements)

    def get_addto_followset(self):
        all_prods = get_all_productions(self.__grammar)
        for prod in all_prods:
            self.followset_rule_2(prod.left, prod.right_elements)

    def followset_add(self, A, B, addto_dict):
        len1 = len(self.__follow_set[B])
        self.__follow_set[B].update(self.__follow_set[A])
        if (len1 < len(self.__follow_set[B])):
            self.follow_rule2_update_nonterm(B, addto_dict)

    def follow_rule2_update_nonterm(self, A: str, addto_dict):
        for B in addto_dict[A]:
            self.followset_add(A, B, addto_dict)

    def update_followset_rule2(self, addto_dict):
        for A, right in addto_dict.items():
            for B in right:
                self.followset_add(A, B, addto_dict)

    #### public methods
    def follow_set(self):
        if self.__has_follow:
            return self.__follow_set

        self.init_follow_set()
        self.get_rule1_followset()
        self.get_addto_followset()
        self.update_followset_rule2(self.__addto_follow)

        self.__has_follow = True
        return self.__follow_set

    def first_set(self):
        if self.__has_first:
            return self.__first_set

        for nt in self.__grammar:
            if nt not in self.__first_set:
                self.__first_set[nt] = self.nonterminal_first_set(nt)
        self.__has_first = True

        return self.__first_set

    def get_grammar(self):
        return self.__grammar

    def get_parse_table(self, isLL1):
        def set_item(A, a, id):
            if isLL1:
                parse_table[A][a] = id
            else:
                if a not in parse_table[A]:
                    parse_table[A][a] = set()
                parse_table[A][a].add(id)

        parse_table = defaultdict(dict)
        if not self.__has_first:
            self.first_set()
        if not self.__has_follow:
            self.follow_set()
        all_prods = get_all_productions(self.__grammar)
        for prod in all_prods:
            A = prod.left
            first_alpha = self.elements_first_set(prod.right_elements)
            follow_A = self.__follow_set[A]
            for a in first_alpha - {EMPTY}:
                set_item(A, a, prod.id)
            if EMPTY in first_alpha:
                for b in follow_A:
                    set_item(A, b, prod.id)
            if EMPTY in first_alpha and ENDMARK in follow_A:
                set_item(A, ENDMARK, prod.id)
        return parse_table

    def check_LL1(self):
        grammar = self.__grammar
        # first_set=ff.first_set()
        follow_set = self.follow_set()
        LL1 = True
        for A in grammar:
            prods = grammar[A]
            # rights=prod['right']
            n = len(prods)
            for i in range(n - 1):
                for j in range(i + 1, n):
                    alpha = prods[i].right_elements
                    beta = prods[j].right_elements
                    first_alpha = self.elements_first_set(alpha)
                    first_beta = self.elements_first_set(beta)
                    if first_alpha & first_beta:
                        print(f"first alpha x first beta: {A}")
                        LL1 = False

                    if EMPTY in first_alpha and first_beta & follow_set[A]:
                        print(f"first beta x follow A: {A}")
                        LL1 = False

                    if EMPTY in first_beta and first_alpha & follow_set[A]:
                        print(f"first alpha x follow A: {A}")
                        LL1 = False
        return LL1
