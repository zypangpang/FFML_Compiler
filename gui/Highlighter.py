from PyQt5.QtCore import QRegularExpression,Qt
from PyQt5.QtGui import QSyntaxHighlighter, QTextCharFormat, QFont


class Highlighter(QSyntaxHighlighter):
    class HighlightingRule:
        def __init__(self,pattern:QRegularExpression,format:QTextCharFormat):
            self.pattern=pattern
            self.format=format


    def __init__(self,parent):
        super().__init__(parent)
        self.highlighting_rules=[]


        self.functionFormat = QTextCharFormat()
        self.functionFormat.setFontItalic(True)
        self.functionFormat.setForeground(Qt.blue)
        self.highlighting_rules.append(
            Highlighter.HighlightingRule(QRegularExpression(r"\b[A-Za-z0-9_]+(?=\()"), self.functionFormat))

        self.quotationFormat = QTextCharFormat()
        self.quotationFormat.setForeground(Qt.darkGreen)
        self.highlighting_rules.append(
            Highlighter.HighlightingRule(QRegularExpression(r"'.*'"), self.quotationFormat))

        self.digitFormat = QTextCharFormat()
        self.digitFormat.setForeground(Qt.darkRed)
        self.highlighting_rules.append(
            Highlighter.HighlightingRule(QRegularExpression(r"\b\d+\.?\d*\b"), self.digitFormat))

        self.keyword_format = QTextCharFormat()
        self.keyword_format.setForeground(Qt.darkBlue)
        self.keyword_format.setFontWeight(QFont.Bold)
        keywordPatterns = [
            r"\bPOLICYID\b", r"\bON\b", r"\bIF\b", r"\bTHEN\b", r"\bAND\b", r"\bOR\b", r"\bHISTORY\b", r"\bQUERY\b",
            r"\bSEQ\b",r"\bTRUE\b",r"\bFALSE\b"
        ]
        self.highlighting_rules += [Highlighter.HighlightingRule(QRegularExpression(pattern), self.keyword_format)
                                   for pattern in keywordPatterns]

        self.singleLineCommentFormat = QTextCharFormat()
        self.singleLineCommentFormat.setForeground(Qt.gray)
        self.highlighting_rules.append(
            Highlighter.HighlightingRule(QRegularExpression("//[^\n]*"), self.singleLineCommentFormat))

    def highlightBlock(self, text: str) -> None:
        for rule in self.highlighting_rules:
            matchIterator = rule.pattern.globalMatch(text)
            while matchIterator.hasNext():
                match = matchIterator.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), rule.format)
