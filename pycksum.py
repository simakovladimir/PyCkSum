#! /usr/bin/env python

# PyQt-based GUI tool for checksum calculation of a single file
# Typical usage:
#   pycksum.py <commands> <file>
# where:
#   <commands> is a comma-separated list of hash computing tools
#     available in the system
#   <file> is a file to be processed
# Example:
#   pycksum.py crc32,md5sum,sha1sum ./foo.bar
# License: MIT
# Dedicated to my friends

import re
import sys
import operator
import subprocess
import os.path
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

class CkSumHashContainer(QObject):
  modified = pyqtSignal(int)
  def __init__(self, argv):
    QObject.__init__(self)
    if len(argv) != 3 or not os.path.exists(argv[2]):
      raise RuntimeError("Invalid command line")
    self.HashSource = argv[0]
    self.HashTitles = argv[1].split(",")
    self.HashValues = ["computing"] * len(self.HashTitles)
    self.HashTarget = argv[2]
  def hashSource(self):
    return self.HashSource
  def hashTitles(self):
    return self.HashTitles
  def hashValues(self):
    return self.HashValues
  def hashTarget(self):
    return self.HashTarget
  def displayItem(self, index):
    return self.HashTitles[index] + ": " + self.HashValues[index]
  @pyqtSlot(int, str)
  def modify(self, index, newValue):
    if index in range(len(self.HashValues)):
      self.HashValues[index] = newValue
      self.modified.emit(index)

class CkSumHashProcessor(QObject):
  finished = pyqtSignal()
  stopped = pyqtSignal()
  updated = pyqtSignal(int, str)
  def __init__(self, hashContainer):
    QObject.__init__(self)
    self.HashContainer = hashContainer
    self.OughtClose = False
  @pyqtSlot()
  def process(self):
    for i in range(len(self.HashContainer.hashTitles())):
      try:
        self.updated.emit(
          i,
          re.sub(
            r"^(\w+).*", r"\1",
            subprocess.check_output([
              self.HashContainer.hashTitles()[i],
              self.HashContainer.hashTarget()]),
            flags = re.DOTALL))
      except:
        self.updated.emit(i, "failed")
      if self.OughtClose:
        self.stopped.emit()
        return
    self.finished.emit()
  @pyqtSlot()
  def stop(self):
    self.OughtClose = True

class CkSumDialog(QDialog):
  forceStop = pyqtSignal()
  def __init__(self, hashContainer):
    QDialog.__init__(self)
    self.HashContainer = hashContainer
    self.MightClose = False
    self.setMinimumSize(400, 300)
    self.setGeometry(
      QStyle.alignedRect(
        Qt.LeftToRight,
        Qt.AlignCenter,
        self.minimumSize(),
        QApplication.desktop().availableGeometry()))
    self.setWindowTitle(
      "Checksum - " + os.path.basename(self.HashContainer.hashTarget()))
    self.verticalLayout = QVBoxLayout()
    self.labelList = QLabel()
    self.labelList.setText("Checksum list")
    self.verticalLayout.addWidget(self.labelList)
    self.listWidget = QListWidget()
    self.listWidget.addItems(
      map(
        self.HashContainer.displayItem,
        range(len(self.HashContainer.hashTitles()))))
    self.listWidget.setContextMenuPolicy(Qt.CustomContextMenu)
    self.listWidget.customContextMenuRequested.connect(self.openMenu)
    self.listWidget.currentRowChanged.connect(self.rowSwitched)
    self.listWidget.setEnabled(False)
    self.verticalLayout.addWidget(self.listWidget)
    self.labelEdit = QLabel()
    self.labelEdit.setText("Quick match")
    self.verticalLayout.addWidget(self.labelEdit)
    self.lineEdit = QLineEdit()
    self.lineEdit.textChanged.connect(self.inputUpdated)
    self.lineEdit.setEnabled(False)
    self.verticalLayout.addWidget(self.lineEdit)
    self.buttonBox = QDialogButtonBox()
    self.buttonBox.setStandardButtons(QDialogButtonBox.Ok)
    self.buttonBox.accepted.connect(self.accept)
    self.verticalLayout.addWidget(self.buttonBox)
    self.setLayout(self.verticalLayout)
  def closeEvent(self, event):
    if self.MightClose:
      event.accept()
    else:
      self.forceStop.emit()
      event.ignore()
  def accept(self):
    self.close()
  def reject(self):
    self.close()
  def done(self):
    self.close()
  @pyqtSlot(int)
  def update(self, index):
    self.listWidget.item(index).setText(self.HashContainer.displayItem(index))
  @pyqtSlot()
  def calcOver(self):
    self.MightClose = True
    self.listWidget.setEnabled(True)
    self.lineEdit.setEnabled(True)
  @pyqtSlot()
  def stop(self):
    self.MightClose = True
    self.close()
  @pyqtSlot(QPoint)
  def openMenu(self, position):
    menu = QMenu()
    copyAction = QAction(
      operator.add(
        "Copy to clipboard ",
        self.HashContainer.hashTitles()[self.listWidget.currentRow()]),
      self)
    copyAction.triggered.connect(self.copyValue)
    menu.addAction(copyAction)
    menu.exec_(self.listWidget.viewport().mapToGlobal(position))
  @pyqtSlot(int)
  def rowSwitched(self, row):
    QApplication.clipboard().setText(
      self.HashContainer.hashValues()[row],
      QClipboard.Selection)
  @pyqtSlot(str)
  def inputUpdated(self, newText):
    if newText in self.HashContainer.hashValues():
      self.listWidget.setCurrentRow(
        self.HashContainer.hashValues().index(newText))
    else:
      self.listWidget.clearSelection()
  @pyqtSlot()
  def copyValue(self):
    QApplication.clipboard().setText(
      self.HashContainer.hashValues()[self.listWidget.currentRow()],
      QClipboard.Clipboard)

if __name__ == "__main__":
  try:
    app = QApplication(sys.argv)
    QApplication.setWindowIcon(QIcon.fromTheme("kde"))
    container = CkSumHashContainer(sys.argv)
    processor = CkSumHashProcessor(container)
    dialog = CkSumDialog(container)
    thread = QThread()
    processor.moveToThread(thread)
    container.modified.connect(dialog.update)
    processor.finished.connect(thread.quit)
    processor.finished.connect(dialog.calcOver)
    processor.stopped.connect(thread.quit)
    processor.stopped.connect(dialog.stop)
    processor.updated.connect(container.modify)
    dialog.forceStop.connect(processor.stop, Qt.DirectConnection)
    thread.started.connect(processor.process)
    dialog.show()
    thread.start()
  except:
    QMessageBox.critical(
      None, "Checksum error", "Check command line and try again")
    sys.exit(1)
  sys.exit(app.exec_())
