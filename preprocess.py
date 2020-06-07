from constants import COMMENT_SYM

class Preprocessor:
    def __init__(self,file_path):
        self.file_path=file_path
        self.new_file_path=f".{self.file_path}.tmp"

    def remove_blank(self,line):
        return line.strip()
    def remove_comment(self,line):
        comm_begin=line.find(COMMENT_SYM)
        return line[:comm_begin] if comm_begin != -1 else line
    def process(self):
        with open(self.file_path,'r') as rf:
            with open(self.new_file_path,'w') as wf:
                for line in rf:
                    line=self.remove_blank(line)
                    line=self.remove_comment(line)
                    wf.write(line+'\n')
        return self.new_file_path
