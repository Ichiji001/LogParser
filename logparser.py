import os
import sys
import threading
from PyQt4 import QtGui
from PyQt4 import QtCore

class LogParser_ApplyFilterThread(QtCore.QThread):
	def __init__(self, parent):
		QtCore.QThread.__init__(self, parent)
		self.parent = parent
		self._lock = threading.Lock()
		self.signal = QtCore.SIGNAL('Update text')
		self.running = False

	def fileDisplayUI_ApplyFilters(self):
		self.parent.maxMatches = 200
		numMatches = 0
		display = ''
		currentLineInFile = -1

		while numMatches < self.parent.maxMatches:
			if self.running == False:
				break

			currentLineInFile = currentLineInFile + 1
			filterOmitTrigger = False
			filterIncludeTrigger = False
			includeFilterExists = False

			for group in self.parent.filterGroups:
				if group[0].foreground().color().green() == 255
					includeFilterExists = True

			if len(self.parent.fileData) > currentLineInFile:

				if self.parent.newLineMode == False:
					if self.parent.fileData[currentLineInFile] == '':
						continue

				for group in self.parent.filterGroups:
					if str(group[0].text()) in self.parent.fileData[currentLineInFile]:
						if group[0].foreground().color().green() == 255:
							filterIncludeTrigger = True
							continue
						else:
							filterOmitTrigger = True
							break

				if filterOmitTrigger == True
					continue

				if filterIncludeTrigger == False and includeFilterExists == True:
					continue

				for group in self.parent.filterGroups:

					filterIncludeTrigger = False
					filterOmitTrigger = False
					includeFilterExists = False

					for item in group:
						if group[0] != item:
							if item.foreground().color().green() == 255:
								includeFilterExists = True

					for item in group:
						if group[0] != item:
							childText = str(item.text())[3:]
							if childText in self.parent.fileData[currentLineInFile]:
								if item.foreground.color().green() == 255:
									filterIncludeTrigger = True
									continue
								else:
									filterOmitTrigger = True
									break

					if filterOmiterTrigger == True:
						break

					if filterIncludeTrigger == False and includeFilterExists == True:
						break

				if filterOmitTrigger == True:
					continue

				if filterIncludeTrigger == False and includeFilterExists == True:
					continue

				display = display + self.parent.fileData[currentLineInFile] + '\n'
				numMatches = numMatches + 1

				self.emit(self.signal, display)

			else:
				break

		if display == '':
			display = 'No Results!'
			self.emit(self.signal, display)

		self.running = False

	def run(self):
		with self._lock:
			self.running = True
			self.fileDisplayUI_ApplyFilters()





class LogParser(QtGui.QMainWindow):

	def __init__(self, fname=None):
		super(LogParser, self).__init__()

		self.initProgramVariables()
		self.initCentralWidgetUI()
		self.initGUIStructureUI()
		self.initComponentsUI()

		p = self.palette()
		p.setColor(QtGui.QPalette.Window, QtGui.QColor(65, 75, 65))
		p.setColor(QtGui.QPalette.Button, QtGui.QColor(220, 220, 220))
		p.setColor(QtGui.QPalette.ButtonText, QtGui.QColor(0, 0, 0))
		self.setPalette(p)

		self.setGeometry(300, 300, 1300, 500)
		self.setWindowTitle('Log Parser')
		self.show()

		if fname is not None:
			with open(fname, 'r') as f:
				self.fileData = f.read()
			self.fileData = self.fileData.split('\n')
			self.fileDisplayUI_ApplyFilters()

	def eventFilter(self, source, event):
		if event.type() == QtCore.QEvent.DragEnter and source is self.fileDisplayUI:
			event.accept()
			return True

		elif event.type() == QtCore.QEvent.Drop and source is self.filterDisplayUI:
			if event.mimeData().hasUrls:
				droppath = str(event.mimeData().urls().pop().toLocalFile())
				with open(droppath, 'r') as f:
					self.fileData = f.read()
				self.fileData = self.fileData.split('\n')
				self.fileDisplayUI_ApplyFilters()
			return True

		elif event.type() == QtCore.QEvent.KeyPress and event.key() == QtCore.Qt.key_Tab:
			if self.filterDisplayUI.hasFocus() == False:
				self.filterInputUI.setFocus()
			return True

		else:
			return super(LogParser, self).eventFilter(source, event)


	def fileDisplayUI_BufferScroll(self):

		maximumValue = float(self.fileDisplayUI.verticalScrollBar().maximum())
		currentValue = self.fileDisplayUI.verticalScrollBar().value()
		percentScrolled = 0.0

		if maximumValue > 0:
			percentScrolled = currentValue / maximumValue

		print currentValue

		if percentScrolled > .75:
			if self.pageNumber * self.maxMatches < len(self.fileData):
				print 'add'
				self.pageNumber = self.pageNumber + 1
				self.fileDisplayUI_ApplyFilters()
		elif percentScrolled < .01 and False:
			if self.pageNumber > 0:
				print 'sub'
				self.pageNumber = self.pageNumber - 1
				self.fileDisplayUI_ApplyFilters()

	def filterDisplayUI_addNewFilter(self):
		filterInput = self.filterInputUI.text()
		self.filterInputUI.setText('')
		if str(filterInput).strip() == '':
			return
		items = []
		for index in xrange(self.filterDisplayUI.count()):
			items.append(self.filterDisplayUI.item(index))
		labels = [i.text() for i in items]

		if filterInput in labels:
			return

		items = []
		group = []

		filterInputItem = QtGui.QListWidgetItem()
		filterInputItem.setForeground(QtGui.QColor(255, 0, 0))
		filterInputItem.setText(filterInput)

		for selectedItem in self.filterDisplayUI.selectedItems():
			items.append(selectedItem)

		if len(items) > 0:
			selectedItem = items[0]
			for group in self.filterGroups:
				if selectedItem in group:
					filterInputItem.setText('   ' + filterInput)
					group.append(filterInputItem)
		else:
			group.append(filterInputItem)
			self.filterGroups.append(group)

		filterGroupsCopy = []
		for group in self.filterGroups:
			groupCopy = []
			for item in group:
				groupCopy.append(item.clone())
				filterGroupsCopy.append(groupCopy)

		self.filterDisplayUI.clear()
		self.filterGroups = filterGroupsCopy

		for group in self.filterGroups:
			for item in group:
				self.filterDisplayUI.addItem(item)

		self.fileDisplayUI_ApplyFilters()


	def filterDisplayUI_toggleFilterMode(self):
		for selectedItem in self.filterDisplayUI.selectedItems():
			if selectedItem.foreground().color().red() == 255:
				selectedItem.setForeground(QtGui.QColor(0, 255, 0))
			else:
				selectedItem.setForeground(QtGui.QColor(255, 0, 0))

			self.filterDisplayUI.setItemSelected(selectedItem, False)
			self.fileDisplayUI_ApplyFilters()

	def filterDisplayUI_mousePressedEvent(self, event):
		self.filterDisplayUI.clearSelection()
		super(QtGui.QListWidget, self.filterDisplayUI).mousePressEvent(event)

	def filterDisplayUI_mouseDoubleClickEvent(self, event):
		self.filterDisplayUI_toggleFilterMode()
		self.filterInputUI.setFocus()

	def filterDisplayUI_keyPressEvent(self, event):
		if event.matches(QtGui.QKeySequence.Delete):
			itemsToDelete = []
			groupToDelete = None
			for selectedItem in self.filterDisplayUI.selectedItems():
				for group in self.filterGroups:
					if selectedItem in group:
						if group[0] == selectedItem:
							for item in group:
								itemsToDelete.append(item)
							groupToDelete = group
						else:
							itemsToDelete.append(selectedItem)
			for item in itemsToDelete:
				itemToRemove = self.filterDisplayUI.takeItem(self.filterDisplayUI.row(item))
				for group in self.filterGroups:
					if itemToRemove in group:
						group.remove(itemToRemove)

			if groupToDelete != None:
				self.filterGroups.remove(groupToDelete)

			self.filterDisplayUI.setItemSelected(selectedItem, False)
			self.fileDisplayUI_ApplyFilters()

		if event.key() == QtCore.Qt.Key_Space:
			self.filterDisplayUI_toggleFilterMode()

	def initComponentsUI(self):
		self.fileDisplayUI = QtGui.QTextEdit('Drop a file here or use the command line')
		self.fileDisplayUI.setReadOnly(True)
		self.fileDisplayUI.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
		self.fileDisplayUI.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
		p = self.fileDisplayUI.palette()
		p.setColor(QtGui.QPalette.Base, QtGui.QColor(39, 40, 34))
		p.setColor(QtGui.QPalette.Text, QtGui.QColor(255, 255, 255))
		self.fileDisplayUI.setPalette(p)
		self.fileDisplayUI.installEventFilter(self)
		self.upperSplitter.addWidget(self.fileDisplayUI)

		self.filterInputUI = QtGui.QLineEdit()
		self.filterInputUI.setFixedHeight(25)
		self.filterInputUI.setPlaceholderText('Enter filters here')
		p = self.filterInputUI.palette()
		p.setColor(QtGui.QPalette.Base, QtGui.QColor(200, 200, 200))
		p.setColor(QtGui.QPalette.Text, QtGui.QColor(0, 0, 0))
		self.filterInputUI.setPalette(p)
		self.filterInputUI.returnPressed.connect(self.filterDisplayUI_addNewFilter)
		self.lowerSplitter.addWidget(self.filterInputUI)

		self.filterDisplayUI = QtGui.QListWidget()
		self.filterDispalyUI.mousePressEvent = self.filterDisplayUI_mousePressedEvent
		self.filterDisplayUI.mouseDoubleClickEvent = self.filterDisplayUI_mouseDoubleClickEvent
		self.filterDisplayUI.keyPressEvent = self.filterDisplayUI_keyPressEvent
		#self.filterDisplayUI.setFocusPolicy(QtCore.Qt.NoFocus)
		p = self.filterDisplayUI.palette()
		p.setColor(QtGui.QPalette.Base, QtGui.QColor(39, 40, 34))
		p.setColor(QtGui.QPalette.Text, QtGui.QColor(255, 255, 255))
		p.setColor(QtGui.QPalette.Highlight, QtGui.QColor(49, 50, 46))
		self.filterDisplayUI.setPalette(p)
		self.filterDisplayUI.installEventFilter(self)
		self.upperSplitter.addWidget(self.filterDisplayUI)

		self.upperSplitter.setSizes([1000, 100])

	def initGUIStructureUI(self):
		componentContainer = QtGui.QWidget()
		componentLayout = QtGui.QVBoxLayout()
		componentSplitter = QtGui.QSplitter()
		componentSplitter.setOrientation(QtCore.Qt.Vertical)
		componentContainer.setLayout(componentLayout)
		componentLayout.addWidget(componentSplitter)

		upperContainer = Qtgui.QWidget
		upperLayout = QtGui.QVBoxLayout()
		self.upperSplitter = QtGui.QSplitter()
		upperContainer.setLayout(upperLayout)
		upperLayout.addWidget(self.upperSplitter)

		lowerContainer = QtGui.QWidget()
		lowerLayout = QtGui.QVBoxLayout()
		self.lowerSplitter = QtGui.QSplitter()
		lowerContainer.setLayout(lowerLayout)
		lowerLayout.addWidget(self.lowerSplitter)

		componentSplitter.addWidget(upperContainer)
		componentSplitter.addWidget(lowerContainer)
		componentSplitter.setSizes([1000, 100])

		self.centralVBox.addWidget(componentContainer)

	def toggleNewLineMode(self):
		self.newLineMode = not self.newLineMode
		self.fileDisplayUI_ApplyFilters()

	def initCentralWidgetUI(self):
		self.statusBar().showMessage('Ready')
		self.statusBar().setStyleSheet("color: rgb(180, 180, 180);")

		exitAction = QtGui.QAction(QtGui.QIcon('exit.png'), '&Exit', self)
		exitAction.setShortcut('Ctrl+Q')
		exitAction.setStatusTip('Exit application')
		exitAction.triggered.connect(QtGui.qApp.quit)

		newLineAction = QtGui.QAction(QtGui.QIcon('filter.png'), '&Toggle New Lines', self)
		newLineAction.setShortcut('Ctrl+Shift+N')
		newLineAction.setStatusTip('Toggle filtering new lines')
		newLineAction.triggered.connect(self.toggleNewLineMode)

		menubar = self.menuBar()
		fileMenu = menubar.addMenu('&File')
		fileMenu.addAction(exitAction)

		toolbar = self.addToolBar('Exit')
		toolbar.addAction(exitAction)
		toolbar.addAction(newLineAction)

		self.centralVBox = QtGui.QVBoxLayout()

		centralWidget = QtGui.QWidget()
		centralWidget.setLayout(self.centralVBox)
		self.setCentralWidget(centralWidget)

	def fileDisplayUI_UpdateDisplay(self, displayText):
		self.fileDisplayUI.setText(displayText)

	def fileDisplayUI_ApplyFilters(self):
		while self.applyFiltersThread.isRunning() == True:
			self.applyFiltersThread.running = False

		self.fileDisplayUI.setText('Filtering/Loading file...')
		self.applyFiltersThread.start()

	def initProgramVariables(self):
		self.newLineMode = True
		self.fileData = []
		self.pageNumber = 0
		self.filterGroups = []
		self.applyFiltersThread = LogParser_ApplyFilterThread(self)
		self.connect(self.applyFiltersThread, self.applyFiltersThread.signal, self.fileDisplayUI_UpdateDisplay)

def main():
	filename = None
	if len(sys.argv) > 1:
		fname = sys.argv[1]

		if os.path.isfile(fname):
			filename = fname
		else:
			print("ERROR: {} does not exist or is not a regular file!".format(fname))
			sys.exit(1)
	app = QtGui.QApplication(sys.argv)
	log_parser = LogParser(filename)
	sys.exit(app.exec_())

if __name__ == '__main__':
	main()
