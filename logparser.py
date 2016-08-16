#!/usr/bin/env python
""" logparser.py - PyQt graphical log parser

This is an easy-to-use tool which combines the advantages of *less* and *grep* in a fashion which doesn't require the
 user to understand regular expressions.

Useage:
    python logparser.py [filename.txt]

    To load a file either pass the name in as an argument on the command line or drag and drop any file within the
    bounds of the file output display.

    Below the file output display there is a spot to type strings to filter for.  The enter key will apply the filter.
    All existing filters are displayed to the far right.

Filters:
    Green filters include all lines that contain the filter string.  Multiple green filters are treated as ORs.  Both
    filters do not need to exist on the same line.

    Red filters take priority over green filters.  Red filters wil lexclude any line that contains the filter string.

    Toggle filters from red to green or vice versa by double-clicing with the mouse or by selecting with mouse and
    pressing <Space>.

    Delete filters by selecting with mouse and pressing <Delete>.

    To create an AND filter, click on an existing filter and then type in a new filter.  The ANDed filter shoudl appear
    indented under the filter that was clicked on.

Incomplete features:
    There are currently two "invisible" buttons that don't have an icon, but do have mouse-over tooltips.  They are both
    located just below the "File" menu.
        - Left button exits the application
        - Right button toggles filtering out empty lines (e.g. lines with just a newline)
"""
import os
import sys
import threading
from PyQt4 import QtGui
from PyQt4 import QtCore


class LogParser_ApplyFilterThread(QtCore.QThread):
    def __init__(self, parent):
        """
        As filters are applied, update the text as results are required.
        This is basically a worker thread to help make the GUI appear more responsive.

        :param parent: LogParer -  the LogParser instance (i.e. the GUI application)
        """
        QtCore.QThread.__init__(self, parent)
        self.parent = parent
        # Create Lock
        self._lock = threading.Lock()
        # Custom signal / slot for updating the results text as it's found
        self.signal = QtCore.SIGNAL('Update text')
        # Flag used to end the current filter search
        self.running = False

    def fileDisplayUI_ApplyFilters(self):
        # Maximum number of lines to display on the file display widget
        self.parent.maxMatches = 200

        # Current number of lines found to display
        numMatches = 0

        # String output that will be written to the file display widget
        display = ''

        # Current line in the fileData that we are comparing with our filter
        # currentLineInFile = ( self.pageNumber * self.maxMatches ) - 1
        currentLineInFile = -1

        # While the output buffer still has space
        while numMatches < self.parent.maxMatches:
            # If this filter job is being interrupted, then break out
            if not self.running:
                break

            # Always increment the current line of the file
            currentLineInFile += 1

            # Flag used to continue the while loop if any exclusion filter matches
            filterOmitTrigger = False

            # Flag used to continue the while loop if no inclusion filter matches
            filterIncludeTrigger = False

            # Flag to determine the existence of an include filter
            includeFilterExists = False

            # For each parent filter, see if the text color is green, if so, an include filter exists
            for group in self.parent.filterGroups:
                if group[0].foreground().color().green() == 255:
                    includeFilterExists = True

            # If our current line index for the fileData doesn't exceed the length of the file
            if len(self.parent.fileData) > currentLineInFile:

                # If the user wants to filter new lines
                if not self.parent.newLineMode:
                    if self.parent.fileData[currentLineInFile] == '':
                        continue

                # For each parent filter
                for group in self.parent.filterGroups:
                    # If the parent is in the current line
                    if str(group[0].text()) in self.parent.fileData[currentLineInFile]:
                        # If the parent is a green inclusion filter
                        if group[0].foreground().color().green() == 255:
                            filterIncludeTrigger = True
                            continue
                        else:
                            filterOmitTrigger = True
                            break
                # If the line matches an exclusion filter, omit that line
                if filterOmitTrigger:
                    continue

                # If the line doesn't contain our inclusion criteria
                # Ensure that an include filter exists, otherwise everything gets filtered out
                if includeFilterExists and not filterIncludeTrigger:
                    continue

                # For each child filter
                for group in self.parent.filterGroups:
                    # Re-initialize the flags
                    filterIncludeTrigger = False
                    filterOmitTrigger = False
                    includeFilterExists = False

                    # Determine if an include filter exists within this group
                    for item in group:
                        if group[0] != item:
                            if item.foreground().color().green() == 255:
                                includeFilterExists = True

                    # Apply filters for each child
                    for item in group:
                        if group[0] != item:
                            childText = str(item.text())[3:]
                            if childText in self.parent.fileData[currentLineInFile]:
                                # If the parent is a green inclusion filter
                                if item.foreground().color().green() == 255:
                                    filterIncludeTrigger = True
                                    continue
                                else:
                                    filterOmitTrigger = True
                                    break

                    if filterOmitTrigger:
                        break

                    if includeFilterExists and not filterIncludeTrigger:
                        break

                if filterOmitTrigger:
                    continue

                # If the line doesn't contain our inclusion criteria
                # Ensure that an include filter exists, otherwise everything gets filtered out
                if includeFilterExists and not filterIncludeTrigger:
                    continue

                # Add the current line of the fileData to our buffer
                display = display + self.parent.fileData[currentLineInFile] + '\n'
                numMatches += 1

                # Display our filtered output
                self.emit(self.signal, display)

            # If the currentLineInFile exceeds the file's length, break
            else:
                break

        # If there is no output to display, display 'No Results' to avoid user confusion
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
        """
        Main LogParser class.

        :param fname: str - filename to open at startup (optional)
        """
        super(LogParser, self).__init__()

        # Init all UI components
        self.initProgramVariables()
        self.initCentralWidgetUI()
        self.initGUIStructureUI()
        self.initComponentsUI()

        # Main window colors
        p = self.palette()
        p.setColor(QtGui.QPalette.Window, QtGui.QColor(65, 75, 65))
        p.setColor(QtGui.QPalette.Button, QtGui.QColor(220, 220, 220))
        p.setColor(QtGui.QPalette.ButtonText, QtGui.QColor(0, 0, 0))
        self.setPalette(p)

        # Main window attributes
        self.setGeometry(300, 300, 1300, 500)
        self.setWindowTitle('Log Parser')
        self.show()

        # If a filename was passed in
        if fname is not None:
            with open(fname, 'r') as f:
                self.fileData = f.read()
            self.fileData = self.fileData.split('\n')
            self.fileDisplayUI_ApplyFilters()

    def eventFilter(self, source, event):
        # Drag event for the file display UI
        if event.type() == QtCore.QEvent.DragEnter and source is self.fileDisplayUI:
            event.accept()
            return True
        # Drop event for file display UI
        elif event.type() == QtCore.QEvent.Drop and source is self.fileDisplayUI:
            if event.mimeData().hasUrls:
                droppath = str(event.mimeData().urls().pop().toLocalFile())
                with open(droppath, 'r') as f:
                    self.fileData = f.read()
                self.fileData = self.fileData.split('\n')
                self.fileDisplayUI_ApplyFilters()
            return True

        elif event.type() == QtCore.QEvent.KeyPress and event.key() == QtCore.Qt.Key_Tab:
            if not self.filterDisplayUI.hasFocus():
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

        #print(percentScrolled)
        print(currentValue)

        # If the user has scrolled above 75% of the available text
        if percentScrolled > .75:
            # If the pageNumber would go out of bounds, don't change it
            if self.pageNumber * self.maxMatches < len(self.fileData):
                print('add')
                self.pageNumber += 1
                self.fileDisplayUI_ApplyFilters()
                #self.fileDisplayUI.verticalScrollBar().setValue( (self.maxMatches / 2) * 15 )
        # If the user has scrolled below 25% of the available text
        elif percentScrolled < .01 and False:
            # If the pageNumber would go out of bounds, don't change it
            if self.pageNumber > 0:
                print('sub')
                self.pageNumber -= 1
                self.fileDisplayUI_ApplyFilters()

    def filterDisplayUI_addNewFilter(self):

        # Obtain the filter that was just typed from the UI
        filterInput = self.filterInputUI.text()

        # Set the filter input UI text back to being empty
        self.filterInputUI.setText('')

        # Disallow empty filters
        if str(filterInput).strip() == '':
            return

        # Get all currently enabled filters from the UI
        items = []
        for index in range(self.filterDisplayUI.count()):
            items.append(self.filterDisplayUI.item(index))
        labels = [i.text() for i in items]

        # Disallow repeated filters
        if filterInput in labels:
            return

        # Insert filters into sorted groups
        items = []
        group = []

        # Convert the filter string to a QListWidgetItem, and customize it
        filterInputItem = QtGui.QListWidgetItem()
        filterInputItem.setForeground(QtGui.QColor(255, 0, 0))
        filterInputItem.setText(filterInput)

        # Check if a filter is selected within the filter output display
        for selectedItem in self.filterDisplayUI.selectedItems():
            items.append(selectedItem)

        # If a filter is selected, append the new filter as a child of the selection
        if len(items) > 0:
            selectedItem = items[0]
            for group in self.filterGroups:
                if selectedItem in group:
                    filterInputItem.setText('   ' + filterInput)
                    group.append(filterInputItem)
        # If none were selected, the new filter will become a group parent
        else:
            group.append(filterInputItem)
            self.filterGroups.append(group)

        # Since QListWidget.clear() deletes all points of it's items, we make a copy
        filterGroupsCopy = []
        for group in self.filterGroups:
            groupCopy = []
            for item in group:
                groupCopy.append(item.clone())
            filterGroupsCopy.append(groupCopy)

        # Erase all items from display to ensure order of parent and children
        self.filterDisplayUI.clear()

        # Set the filter groups equal to the copy since the original was deleted
        self.filterGroups = filterGroupsCopy

        # Add all filters to the QListWidget
        for group in self.filterGroups:
            for item in group:
                self.filterDisplayUI.addItem(item)

        # Apply the new set of filters to the input file
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
        """
        Allow clicking to clear the filter selection
        """
        self.filterDisplayUI.clearSelection()
        super(QtGui.QListWidget, self.filterDisplayUI).mousePressEvent(event)

    def filterDisplayUI_mouseDoubleClickEvent(self, event):
        """
        Allow toggling of filters by double-clicking
        """
        self.filterDisplayUI_toggleFilterMode()
        self.filterInputUI.setFocus()

    def filterDisplayUI_keyPressEvent(self, event):
        # Delete key
        if event.matches(QtGui.QKeySequence.Delete):
            # List to avoid concurrent modification
            itemsToDelete = []

            # If we're deleting a parent of a group, keep track of it
            groupToDelete = None
            selectedItem = None

            # For each selected item, remove it from the UI
            for selectedItem in self.filterDisplayUI.selectedItems():
                # For each group in our list of groups
                for group in self.filterGroups:
                    # If the item to delete is among this group
                    if selectedItem in group:
                        # Check if it's a parent
                        if group[0] == selectedItem:
                            # Remove all children of the parent
                            for item in group:
                                itemsToDelete.append(item)
                            # Delete the group
                            groupToDelete = group
                        # If the item to delete is a child
                        else:
                            itemsToDelete.append(selectedItem)

            # For each item that we have flagged to delete
            for item in itemsToDelete:
                # Delete it from the GUI
                itemToRemove = self.filterDisplayUI.takeItem(self.filterDisplayUI.row(item))
                # Delete it from our list
                for group in self.filterGroups:
                    if itemToRemove in group:
                        group.remove(itemToRemove)

            # If we are deleting a parent group, remove the group
            if groupToDelete is not None:
                self.filterGroups.remove(groupToDelete)

            if selectedItem is not None:
                # De-select the selected item
                self.filterDisplayUI.setItemSelected(selectedItem, False)

                # Update the file display with the new filter options
                self.fileDisplayUI_ApplyFilters()

        # Space key
        if event.key() == QtCore.Qt.Key_Space:
            self.filterDisplayUI_toggleFilterMode()

        self.filterInputUI.setFocus()

    def initComponentsUI(self):
        # Wrapping options:
        #QtGui.QTextEdit.NoWrap, WidgetWidth, FixedPixelWidth, FixedColumnWidth

        # UI widget that will display the output of the input file
        self.fileDisplayUI = QtGui.QTextEdit('Drop a file here or use the command line')
        self.fileDisplayUI.setReadOnly(True)
        self.fileDisplayUI.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.fileDisplayUI.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        p = self.fileDisplayUI.palette()
        p.setColor(QtGui.QPalette.Base, QtGui.QColor(39, 40, 34))
        p.setColor(QtGui.QPalette.Text, QtGui.QColor(255, 255, 255))
        self.fileDisplayUI.setPalette(p)
        #self.fileDisplayUI.verticalScrollBar().valueChanged.connect(self.fileDisplayUI_BufferScroll)
        self.fileDisplayUI.installEventFilter(self)
        self.upperSplitter.addWidget(self.fileDisplayUI)

        # UI Widget that the user types filters into, the enter key adds the filter
        self.filterInputUI = QtGui.QLineEdit()
        self.filterInputUI.setFixedHeight(25)
        self.filterInputUI.setPlaceholderText('Enter filters here')
        p = self.filterInputUI.palette()
        p.setColor(QtGui.QPalette.Base, QtGui.QColor(200, 200, 200))
        p.setColor(QtGui.QPalette.Text, QtGui.QColor(0, 0, 0))
        self.filterInputUI.setPalette(p)
        self.filterInputUI.returnPressed.connect(self.filterDisplayUI_addNewFilter)
        self.lowerSplitter.addWidget(self.filterInputUI)

        # UI Widget that displays currently enabled filters
        self.filterDisplayUI = QtGui.QListWidget()
        self.filterDisplayUI.mousePressEvent = self.filterDisplayUI_mousePressedEvent
        self.filterDisplayUI.mouseDoubleClickEvent = self.filterDisplayUI_mouseDoubleClickEvent
        self.filterDisplayUI.keyPressEvent = self.filterDisplayUI_keyPressEvent
        # self.filterDisplayUI.setFocusPolicy(QtCore.Qt.NoFocus)
        p = self.filterDisplayUI.palette()
        p.setColor(QtGui.QPalette.Base, QtGui.QColor(39, 40, 34))
        p.setColor(QtGui.QPalette.Text, QtGui.QColor(255, 255, 255))
        p.setColor(QtGui.QPalette.Highlight, QtGui.QColor(49, 50, 46))
        self.filterDisplayUI.setPalette(p)
        self.filterDisplayUI.installEventFilter(self)
        self.upperSplitter.addWidget(self.filterDisplayUI)

        self.upperSplitter.setSizes([1000, 100])

    def initGUIStructureUI(self):
        """
        Generally, to add widgets to the GUI, use the splitter.addWidget() function.
        This can differ depending on the desired effect from the GUI.

        |-----------------------------------------------|
        |componentContainer
        |  |-----------------------------------------|  |
        |  |componentLayout                          |  |
        |  |  |-----------------------------------|  |  |
        |  |  |upperContainer                     |  |  |
        |  |  |  |-----------------------------|  |  |  |
        |  |  |  |upperLayout                  |  |  |  |
        |  |  |  |             |               |  |  |  |
        |  |  |  |             |               |  |  |  |
        |  |  |  |             |               |  |  |  |
        |  |  |  |             |               |  |  |  |
        |  |  |  |             |               |  |  |  |
        |  |  |  |             |upperSplitter  |  |  |  |
        |  |  |  |                             |  |  |  |
        |  |  |  |-----------------------------|  |  |  |
        |  |  |                                   |  |  |
        |  |  |-----------------------------------|  |  |
        |  |                                         |  |
        |  |         ---componentSplitter---         |  |
        |  |                                         |  |
        |  |  |-----------------------------------|  |  |
        |  |  |lowerContainer                     |  |  |
        |  |  |  |-----------------------------|  |  |  |
        |  |  |  |lowerLayout                  |  |  |  |
        |  |  |  |             |               |  |  |  |
        |  |  |  |             |               |  |  |  |
        |  |  |  |             |               |  |  |  |
        |  |  |  |             |               |  |  |  |
        |  |  |  |             |               |  |  |  |
        |  |  |  |             |lowerSplitter  |  |  |  |
        |  |  |  |                             |  |  |  |
        |  |  |  |-----------------------------|  |  |  |
        |  |  |                                   |  |  |
        |  |  |-----------------------------------|  |  |
        |  |                                         |  |
        |  |-----------------------------------------|  |
        |                                               |
        |-----------------------------------------------|
        """
        componentContainer = QtGui.QWidget()
        componentLayout = QtGui.QVBoxLayout()
        componentSplitter = QtGui.QSplitter()
        componentSplitter.setOrientation(QtCore.Qt.Vertical)
        componentContainer.setLayout(componentLayout)
        componentLayout.addWidget(componentSplitter)

        upperContainer = QtGui.QWidget()
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
        # Status bar that appears on the bottom of the window
        self.statusBar().showMessage('Ready')
        self.statusBar().setStyleSheet("color: rgb(180, 180, 180);")

        # This action describes exiting the application
        exitAction = QtGui.QAction(QtGui.QIcon('exit.png'), '&Exit', self)
        exitAction.setShortcut('Ctrl+Q')
        exitAction.setStatusTip('Exit application')
        exitAction.triggered.connect(QtGui.qApp.quit)

        # This action causes newlines to be ommitted from the filter output
        newLineAction = QtGui.QAction(QtGui.QIcon('filter.png'), '&Toggle New Lines', self)
        newLineAction.setShortcut('Ctrl+Shift+N')
        newLineAction.setStatusTip('Toggle filtering new lines')
        newLineAction.triggered.connect(self.toggleNewLineMode)

        # Adds a File dropdown menu
        menubar = self.menuBar()
        fileMenu = menubar.addMenu('&File')
        fileMenu.addAction(exitAction)

        # A bar that is always in view with buttons
        toolbar = self.addToolBar('Exit')
        toolbar.addAction(exitAction)
        toolbar.addAction(newLineAction)

        # Vertical box layout
        self.centralVBox = QtGui.QVBoxLayout()

        # Main container for all widgets
        centralWidget = QtGui.QWidget()
        centralWidget.setLayout(self.centralVBox)
        self.setCentralWidget(centralWidget)

    def fileDisplayUI_UpdateDisplay(self, displayText):
        """
        Custom event handler for updating the GUI's display as filter results
        are found from the thread that filters the file.

        The filter thread emits the signal every time a new matching line is found.
        """
        self.fileDisplayUI.setText(displayText)

    def fileDisplayUI_ApplyFilters(self):
        """
        This functoin can be called multiple times because when the thread reaches
        the end of it's run method, the isRunning flag becomes false automatically.
        """
        while self.applyFiltersThread.isRunning():
            self.applyFiltersThread.running = False

        self.fileDisplayUI.setText('Filtering/Loading file...')
        self.applyFiltersThread.start()

    def initProgramVariables(self):
        # Don't filter new lines by default
        self.newLineMode = True
        # Contains every line of the file we wish to filter
        self.fileData = []
        # TODO: Will be used later for smooth scrolling of the entire file
        self.pageNumber = 0
        # Used for grouping filters, necessary for ANDing filters
        self.filterGroups = []
        # Thread used to apply filters, prevents the GUI from locking up with large files
        self.applyFiltersThread = LogParser_ApplyFilterThread(self)
        # Custom event handler for the filtering thread to update the GUI text as resutls are found
        self.connect(self.applyFiltersThread, self.applyFiltersThread.signal, self.fileDisplayUI_UpdateDisplay)


def main():
    # If a valid filename is passed in as an argument, then open that
    filename = None
    if len(sys.argv) > 1:
        fname = sys.argv[1]
        # Make sure the file exists and is a regular file
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
