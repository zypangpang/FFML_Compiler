from constants import COMMENT_SYM
import sys


class Preprocessor:
    def __init__(self, file_path=None):
        self.file_path = file_path
        self.new_file_path = f".{self.file_path}.tmp"

    @staticmethod
    def remove_blank(line):
        return line.strip()

    @staticmethod
    def remove_comment(line):
        comm_begin = line.find(COMMENT_SYM)
        return line[:comm_begin] if comm_begin != -1 else line

    def process(self):
        rf = open(self.file_path, 'r') if self.file_path else sys.stdin
        with open(self.new_file_path, 'w') as wf:
            for line in rf:
                line = self.remove_blank(line)
                line = self.remove_comment(line)
                wf.write(line + '\n')
        rf.close()
        return self.new_file_path
