import string
from global_var import global_symbol_table
from constants import  ENDMARK,BUFFER_SIZE

def get_dfa(dfa_file):
    def add_edge(_pstate,_chars,_nstate):
        for _c in _chars:
            T[_pstate][_c]=_nstate
    state_num,edge_num,start_state=(int(x) for x in dfa_file.readline().strip().split())
    T=[{}]*state_num
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
        for i,d in enumerate(self.__M):
            ans+=f"{i}: {d}\n"
        return ans



class Lexer:
    def __init__(self,file,dfa:DFA):
        self.__buffer=[[]] *2

        self.__lexeme_begin=0
        self.__lexeme_buffer=0

        self.__forward = 0
        self.__forward_buffer=0

        self.code_file = file
        self.dfa=dfa

        self.eof=False

        self.__load_buffer()

    def __load_buffer(self):
        self.__forward_buffer = self.__forward_buffer ^ 1
        self.__buffer[self.__forward_buffer]=list(self.code_file.read(BUFFER_SIZE))
        self.__buffer[self.__forward_buffer].append(ENDMARK)


    def __next_char(self):
        if self.eof:
            raise Exception("No more characters")
        buffer=self.__buffer[self.__forward_buffer]
        ans=buffer[self.__forward]
        if ans == ENDMARK:
            self.eof=True
            return ans
        next=self.__forward+1
        if buffer[next]==ENDMARK and next == len(buffer)-1:
            self.__load_buffer()
            next=0
        self.__forward=next
        return ans

    def __retract(self):
        self.__forward=self.__forward-1
        if self.__forward < 0:
            self.__forward_buffer^=1
            self.__forward=BUFFER_SIZE-1

    def __get_lexeme_str(self):
        if self.__lexeme_buffer == self.__forward_buffer:
            return self.__buffer[self.__lexeme_buffer][self.__lexeme_begin:self.__forward]
        else:
            return self.__buffer[self.__lexeme_buffer][self.__lexeme_begin:-1]\
                   + self.__buffer[self.__forward_buffer][0:self.__forward]

    def get_next_token(self):
        if self.eof:
            raise Exception("Reach EOF")

        s=self.dfa.get_start_state()
        while s is not None:
            c=self.__next_char()
            s = self.dfa.move(s, c)
        self.__retract()
        token_name=self.dfa.accept(s)
        if token_name:
            token = Token(token_name,{'str':self.__get_lexeme_str()})
            self.__lexeme_begin=self.__forward
            self.__lexeme_begin = self.__forward_buffer
            return token
        else:
            raise Exception("Lexical Error")


if __name__ == '__main__':
    dfa_path='lexer/dfa.txt'
    code_path='test_code.txt'
    with open(dfa_path,'r') as f:
        dfa=get_dfa(f)
    print(dfa)
    code_file=open(code_path,'r')
    lexer=Lexer(code_file,dfa)
    try:
        while True:
            print(lexer.get_next_token())
    except Exception as e:
        print(e)
    code_file.close()

