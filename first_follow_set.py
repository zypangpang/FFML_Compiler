from constants import EMPTY, ELE_TYPE, ENDMARK
from grammar_related import Element


class FirstFollowSet:
    def __init__(self, grammar, ss):
        self.__has_first=False
        self.__has_follow=False
        self.__first_set = {}
        self.__follow_set = {}
        self.__grammar = grammar
        self.__addto_follow = {}
        self.__start_symbol = ss

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
        productions = self.__grammar[left]['right']
        fset = set()
        for line in productions:
            fset.update(self.elements_first_set(line))
        return fset

    def combination_first_set(self, element):
        fset = self.elements_first_set(element.symbols)
        if element.op == '?' or element.op == '*':
            fset.add(EMPTY)
        return fset

    # def string_first_set(str):
    #    if str[0] in f'"<{EMPTY}':
    #        return {str}
    #    else:
    #        return nonterminal_first_set(str)

    def element_first_set(self, element):
        if element.type == ELE_TYPE.TERM:
            return {element.symbols[0]}
        elif element.type == ELE_TYPE.NONTERM:
            str = element.symbols[0]
            if str not in self.__first_set:
                self.__first_set[str] = self.nonterminal_first_set(str)
            return self.__first_set[str]
        elif element.type == ELE_TYPE.COMBI:
            return self.combination_first_set(element)
        else:
            raise Exception("invalid element type")


    def init_follow_set(self):
        for nt in self.__grammar:
            self.__addto_follow[nt] = set()
            self.__follow_set[nt] = set()
        self.__follow_set[self.__start_symbol].add(ENDMARK)

    def followset_rule_1(self, elements, follow_elements=[]):
        for i in range(0, len(elements)):
            ele = elements[i]
            if ele.type == ELE_TYPE.NONTERM:
                self.__follow_set[ele.symbols[0]].update(
                    self.elements_first_set(elements[i + 1:] + follow_elements) - {EMPTY})
            elif ele.type == ELE_TYPE.COMBI:
                self.combi_get_follow_rule1(ele, elements[i + 1:] + follow_elements)

    def followset_rule_2(self, A: str, elements: list, follow_elements=[]):
        n = len(elements)
        for i in range(0, n):
            B: Element = elements[i]
            if B.type == ELE_TYPE.NONTERM:
                if EMPTY in self.elements_first_set(elements[i + 1:] + follow_elements):
                    self.__addto_follow[A].add(B.symbols[0])
            elif B.type == ELE_TYPE.COMBI:
                # debug
                # if B.symbols[0].symbols[0]=="ConditionStatement":
                #    print(elements[i + 1:]+follow_elements)
                #    print(elements_first_set(elements[i + 1:]+follow_elements))
                # -----
                self.combi_get_follow_rule2(A, B, elements[i + 1:] + follow_elements)

    def combi_get_follow_rule1(self, combi_ele, follow_elements):
        elements = combi_ele.symbols
        self.followset_rule_1(elements, follow_elements)
        if combi_ele.op == '+' or combi_ele.op == '*':
            if len(elements) > 1:
                self.followset_rule_1([elements[-1]], elements + follow_elements)

    def combi_get_follow_rule2(self, A, combi_ele, follow_elements):
        elements = combi_ele.symbols
        self.followset_rule_2(A, elements, follow_elements)
        if combi_ele.op == '+' or combi_ele.op == '*':
            if len(elements) > 1:
                self.followset_rule_2(A, [elements[-1]], elements + follow_elements)

    def get_rule1_followset(self):
        productions = self.__grammar.values()
        for prod in productions:
            for line in prod['right']:
                self.followset_rule_1(line)

    def get_addto_followset(self):
        productions = self.__grammar.values()
        for prod in productions:
            A = prod['left']
            for line in prod['right']:
                self.followset_rule_2(A, line)

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

        self.__has_follow=True
        return self.__follow_set

    def first_set(self):
        if self.__has_first:
            return self.__first_set

        for nt in self.__grammar:
            if nt not in self.__first_set:
                self.__first_set[nt] = self.nonterminal_first_set(nt)
        self.__has_first=True

        return self.__first_set

    def get_grammar(self):
        return self.__grammar