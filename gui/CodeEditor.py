from PyQt5.QtCore import QSize, QRect, Qt, qRound
from PyQt5.QtGui import QColor, QTextFormat, QPainter
from PyQt5.QtWidgets import QWidget, QPlainTextEdit, QTextEdit


class LineNumberArea(QWidget):
    def __init__(self,editor):
        super().__init__(editor)
        self.codeEditor=editor

    def sizeHint(self):
        return QSize(self.codeEditor.lineNumberAreaWidth(),0)

    def paintEvent(self, event) -> None:
        self.codeEditor.lineNumberAreaPaintEvent(event)
    
class CodeEditor(QPlainTextEdit):
    def __init__(self,parent):
        super().__init__(parent)
        self.lineNumberArea=LineNumberArea(self)
        self.blockCountChanged.connect(self.updateLineNumberAreaWidth)
        self.updateRequest.connect(self.updateLineNumberArea)
        self.cursorPositionChanged.connect(self.highlightCurrentLine)

        self.updateLineNumberAreaWidth(0)
        self.highlightCurrentLine()

    def lineNumberAreaWidth(self):
        digits=1
        maxD=max(1,self.blockCount())
        while maxD>=10:
            maxD //= 10
            digits+=1

        space = 3 + self.fontMetrics().horizontalAdvance('9') * digits
        return space

    def updateLineNumberAreaWidth(self,newBlockCount):
        self.setViewportMargins(self.lineNumberAreaWidth(), 0, 0, 0)
    
    def updateLineNumberArea(self,rect, dy):
        if dy:
            self.lineNumberArea.scroll(0, dy)
        else:
            self.lineNumberArea.update(0, rect.y(), self.lineNumberArea.width(), rect.height())

        if rect.contains(self.viewport().rect()):
            self.updateLineNumberAreaWidth(0)

    def resizeEvent(self, e) -> None:
        super().resizeEvent(e)

        cr = self.contentsRect()
        self.lineNumberArea.setGeometry(QRect(cr.left(), cr.top(), self.lineNumberAreaWidth(), cr.height()))

    def highlightCurrentLine(self):
        extraSelections=[]

        if not self.isReadOnly():
            selection=QTextEdit.ExtraSelection()

            lineColor = QColor(Qt.yellow).lighter(160)

            selection.format.setBackground(lineColor)
            selection.format.setProperty(QTextFormat.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extraSelections.append(selection)

        self.setExtraSelections(extraSelections)

    def lineNumberAreaPaintEvent(self,event):
        painter=QPainter(self.lineNumberArea)
        painter.fillRect(event.rect(),Qt.lightGray)
        block = self.firstVisibleBlock()
        blockNumber = block.blockNumber()
        top = qRound(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + qRound(self.blockBoundingRect(block).height())
        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(blockNumber + 1)
                painter.setPen(Qt.black)
                painter.drawText(0, top, self.lineNumberArea.width(), self.fontMetrics().height(),
                                                         Qt.AlignRight, number)

            block = block.next()
            top = bottom
            bottom = top + qRound(self.blockBoundingRect(block).height())
            blockNumber+=1

