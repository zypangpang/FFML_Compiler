import string
from collections import defaultdict
#from global_var import global_symbol_table
from constants import  ENDMARK,BUFFER_SIZE,KEYWORDS
def get_symbol_table():
    '''
    Get original symbol table.
    Put all keywords in advance.
    :return: symbol table including all keyword entries
    '''
    symbol_table={}
    for x in KEYWORDS:
        symbol_table[x]={'name':'<KEYWORD>','str':x}
    return symbol_table

def get_dfa(dfa_file):
    '''
    Get dfa from file
    :param dfa_file:
    :return:
    '''
    def add_edge(_pstate,_chars,_nstate):
        for _c in _chars:
            T[_pstate][_c]=_nstate
    state_num,edge_num,start_state=(int(x) for x in dfa_file.readline().strip().split())
    T=defaultdict(dict)
    digit = string.digits
    letters_ = string.ascii_letters + '_'
    ws='\t\n '
    for i in range(edge_num):
        pstate,chars,nstate=dfa_file.readline().strip().split()
        pstate = int(pstate)
        nstate = int(nstate)
        if chars == 'digit':
            add_edge(pstate,digit,nstate)
        elif chars=='letters_':
            add_edge(pstate,letters_,nstate)
        elif chars == 'ws':
            add_edge(pstate,ws,nstate)
        else:
            add_edge(pstate,chars,nstate)
    final_state_num=int(dfa_file.readline().strip())
    final_states={}
    for i in range(final_state_num):
        state, name=dfa_file.readline().strip().split()
        state = int(state)
        final_states[state]=name
    return DFA(T,final_states,start_state)


class Token:
    def __init__(self,name,attr: dict):
        self.name=name
        self.attr=attr
    def __str__(self):
        return f"({self.name}; {self.attr})"


class DFA:
    def __init__(self,table,accept_states: dict, start_state: int =0):
        self.__M=table
        self.__accept_states=accept_states
        self.__start_state=start_state

    def get_start_state(self):
        return self.__start_state

    def accept(self,state):
        if state in self.__accept_states:
            return self.__accept_states[state]
        return None

    def move(self,s,c):
        '''
        State transition function
        :param s: current state
        :param c: input char
        :return: next state
        '''
        if c in self.__M[s]:
            return self.__M[s][c]
        return None
    def __str__(self):
        ans=""
        for i,d in self.__M.items():
            ans+=f"{i}: {d}\n"
        return ans


class Lexer:
    '''
    FFML Lexer
    '''
    def __init__(self,file,dfa:DFA,symbol_table):
        '''
        Constructor
        :param file: Code file
        :param dfa: DFA object
        :param symbol_table: symbol table
        '''
        self.__buffer=[[]] *2 # Reading buffer

        self.__lexeme_begin=0
        self.__lexeme_buffer=0

        self.__forward = 0
        self.__forward_buffer=0

        self.__cur_line_num=1

        self.code_file = file
        self.dfa=dfa
        self.symbol_table=symbol_table

        self.eof=False
        self.__cur_token=None
        #self.__retract_token=False

        self.__loaded=False # This bool var is used for forward pointer retraction to avoid loading buffer wrongly
        self.__load_buffer()

    def retract_token(self):
        self.__retract_token=True

    def __load_buffer(self):
        '''
        load buffer from code file
        :return:
        '''
        self.__forward_buffer = self.__forward_buffer ^ 1
        if self.__loaded:
            self.__loaded=False
            return
        self.__buffer[self.__forward_buffer]=list(self.code_file.read(BUFFER_SIZE))
        self.__buffer[self.__forward_buffer].append(ENDMARK)


    def __next_char(self):
        '''
        Get next character from code file
        :return:
        '''
        if self.eof:
            raise Exception("No more characters")
        buffer=self.__buffer[self.__forward_buffer]
        ans=buffer[self.__forward]
        next=self.__forward+1
        if ans == ENDMARK:
            self.eof=True
        elif buffer[next]==ENDMARK and next == BUFFER_SIZE:
            self.__load_buffer()
            next=0
        self.__forward=next
        return ans

    def __retract(self):
        '''
        Retract forward pointer
        :return:
        '''
        self.__forward=self.__forward-1
        if self.__forward < 0:
            self.__forward_buffer^=1
            self.__forward=BUFFER_SIZE-1
            self.__loaded=True

    def __get_lexeme_str(self):
        '''
        Get current lexeme, i.e., chars between lexeme_begin and forward
        :return:
        '''
        if self.__lexeme_buffer == self.__forward_buffer:
            return self.__buffer[self.__lexeme_buffer][self.__lexeme_begin:self.__forward]
        else:
            a=self.__buffer[self.__lexeme_buffer][self.__lexeme_begin:-1]\
                   + self.__buffer[self.__forward_buffer][0:self.__forward]
            #print(''.join(a))
            return a

    def __install_id(self,id):
        '''
        Install and return symbol table entry
        :param id:
        :return:
        '''
        if id not in self.symbol_table:
            self.symbol_table[id]={'name':'<ID>','str':id}
        return self.symbol_table[id]

    def get_error_context(self):
        left = self.__lexeme_begin-10
        right = self.__lexeme_begin+10
        if left < 0:
            left = 0
        #if right >= BUFFER_SIZE:
        #    right = BUFFER_SIZE
        return ''.join(self.__buffer[self.__lexeme_buffer][left:self.__lexeme_begin-1]),\
               ''.join(self.__buffer[self.__lexeme_buffer][self.__lexeme_begin-1:right]) #.replace('\n','\\n')\

    def get_cur_line_num(self):
        return self.__cur_line_num

    def get_next_token(self):
        '''
        Take away current token
        :return:
        '''
        if self.__cur_token is None:
            self.__fetch_next_token()
        res = self.__cur_token
        self.__cur_token=None
        return res

    def lookahead(self):
        if self.__cur_token is None:
            self.__fetch_next_token()
        return self.__cur_token

    def __fetch_next_token(self):
        '''
        Get current token. If no, then get next token from code file and put it as the current token
        :return: current token
        '''
        if self.__cur_token:
            raise Exception("Fetch when cur_token is not None")
        if self.eof:
            self.__cur_token= Token(ENDMARK,{'str':ENDMARK})
            return

        s=self.dfa.get_start_state()
        ps=s
        cur_str=""
        while s is not None:
            ps = s
            c=self.__next_char()
            s = self.dfa.move(s, c)
            cur_str+=c
        self.__retract()
        token_name=self.dfa.accept(ps)
        if token_name:
            lexeme=''.join(self.__get_lexeme_str())
            if token_name == '<ID>':
                st_obj=self.__install_id(lexeme)
                token = Token(token_name,{'entry':st_obj})
            else:
                token = Token(token_name,{'str':lexeme})
            self.__lexeme_begin=self.__forward
            self.__lexeme_buffer = self.__forward_buffer
            if token_name == "<BLANK>":
                self.__cur_line_num+=lexeme.count('\n')
                token=self.get_next_token()

            self.__cur_token=token
        else:
            #print(self.__next_char())
            print(f"Unrecognized string: '{cur_str}'")
            raise Exception("Lexical Error: "+cur_str)

def get_dfa_from_file(path):
    '''
    Get DFA from file
    :param path:
    :return:
    '''
    with open(path,'r') as f:
        dfa=get_dfa(f)
    return dfa

if __name__ == '__main__':
    dfa_path='lexer/dfa.txt'
    code_path='test_code.txt'
    with open(dfa_path,'r') as f:
        dfa=get_dfa(f)
    code_file=open(code_path,'r')
    lexer=Lexer(code_file,dfa,get_symbol_table())
    try:
        while True:
            print(lexer.get_next_token())
    except Exception as e:
        print(e)
    code_file.close()

