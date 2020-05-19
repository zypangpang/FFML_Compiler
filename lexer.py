from global_var import global_symbol_table
from constants import  ENDMARK,BUFFER_SIZE
class Token:
    def __init__(self,name,attr: dict):
        self.name=name
        self.attr=attr

class Lexer:
    def __init__(self,file):
        self.__buffer=[[]] *2

        self.__lexeme_begin=0
        self.__lexeme_buffer=0

        self.__forward = 0
        self.__forward_buffer=0

        self.code_file = file

    def __load_buffer(self):
        self.__forward_buffer = self.__forward_buffer ^ 1
        self.__buffer[self.__forward_buffer]=self.code_file.read(BUFFER_SIZE)
        self.__buffer[self.__forward_buffer].append(ENDMARK)


    def __next_char(self):
        buffer=self.__buffer[self.__forward_buffer]
        self.__forward=self.__forward+1
        if buffer[self.__forward] != ENDMARK:
            return buffer[self.__forward]
        else:
            if self.__forward == len(buffer)-1:
                self.__load_buffer()
                self.__forward=0
                return self.__next_char()
            else:
                return ENDMARK

    def __retract(self):
        self.__forward=self.__forward-1
        if self.__forward < 0:
            self.__forward_buffer^=1
            self.__forward=BUFFER_SIZE-1

    def get_next_token(self):
        pass