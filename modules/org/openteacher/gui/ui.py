#! /usr/bin/env python
# -*- coding: utf-8 -*-

#	Copyright 2011-2013, Marten de Vries
#	Copyright 2009 Nokia Corporation and/or its subsidiary(-ies)
#
#	This file is part of OpenTeacher.
#
#	OpenTeacher is free software: you can redistribute it and/or modify
#	it under the terms of the GNU General Public License as published by
#	the Free Software Foundation, either version 3 of the License, or
#	(at your option) any later version.
#
#	OpenTeacher is distributed in the hope that it will be useful,
#	but WITHOUT ANY WARRANTY; without even the implied warranty of
#	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#	GNU General Public License for more details.
#
#	You should have received a copy of the GNU General Public License
#	along with OpenTeacher.  If not, see <http://www.gnu.org/licenses/>.

from PyQt4 import QtCore, QtGui

#INFO: ICON_PATH is set by gui.py . Set it yourself when re-using this
#code in another context.

class CloseButton(QtGui.QAbstractButton):
	def __init__(self, *args, **kwargs):
		super(CloseButton, self).__init__(*args, **kwargs)
		
		self.setFocusPolicy(QtCore.Qt.NoFocus)
		self.setCursor(QtCore.Qt.ArrowCursor)
		self.setToolTip(_("Close Tab"))
		self.resize(self.sizeHint())

	def sizeHint(self):
		self.ensurePolished()
		width = self.style().pixelMetric(QtGui.QStyle.PM_TabCloseIndicatorWidth, None, self)
		height = self.style().pixelMetric(QtGui.QStyle.PM_TabCloseIndicatorHeight, None, self)
		return QtCore.QSize(width, height)

	def enterEvent(self, *args, **kwargs):
		if self.isEnabled():
			self.update()
		super(CloseButton, self).enterEvent(*args, **kwargs)

	def leaveEvent(self, *args, **kwargs):
		if self.isEnabled():
			self.update()
		super(CloseButton, self).leaveEvent(*args, **kwargs)

	def paintEvent(self, event):
		p = QtGui.QPainter(self)
		opt = QtGui.QStyleOption()
		opt.initFrom(self)
		opt.state = opt.state | QtGui.QStyle.State_AutoRaise
		if self.isEnabled() and self.underMouse() and not self.isChecked() and not self.isDown():
			opt.state = opt.state | QtGui.QStyle.State_Raised
		if self.isChecked():
			opt.state = opt.state | QtGui.QStyle.State_On
		if self.isDown():
			opt.state = opt.state | QtGui.QStyle.State_Sunken

		tb = self.parent()

		if tb.__class__ == QtGui.QTabBar:
			index = tb.currentIndex()
			position = self.style().styleHint(QtGui.QStyle.SH_TabBar_CloseButtonPosition, None, tb)

			if tb.tabButton(index, position) == self:
				opt.state = opt.state | QtGui.QStyle.State_Selected

		self.style().drawPrimitive(QtGui.QStyle.PE_IndicatorTabClose, opt, p, self)

class LessonTabWidget(QtGui.QTabWidget):
	def __init__(self, enterWidget, teachWidget, resultsWidget, *args, **kwargs):
		super(LessonTabWidget, self).__init__(*args, **kwargs)

		self.enterWidget = enterWidget
		self.teachWidget = teachWidget
		self.resultsWidget = resultsWidget

		if enterWidget:
			self.addTab(self.enterWidget, "")
		if teachWidget:
			self.addTab(self.teachWidget, "")
		if resultsWidget:
			self.addTab(self.resultsWidget, "")

		self.setTabPosition(QtGui.QTabWidget.South)
		self.setDocumentMode(True)

		self.retranslate()

	def retranslate(self):
		self.setTabText(self.indexOf(self.enterWidget), _("Enter list"))
		self.setTabText(self.indexOf(self.teachWidget), _("Teach me!"))
		self.setTabText(self.indexOf(self.resultsWidget), _("Show results"))

class FilesTabWidget(QtGui.QTabWidget):
	def __init__(self, startWidget, *args, **kwargs):
		super(FilesTabWidget, self).__init__(*args, **kwargs)

		self.startWidget = startWidget
		self._wrapWidget(startWidget)

		#super because our method does add a close button, which we
		#don't want.
		super(FilesTabWidget, self).addTab(
			self.startWidget,
			QtGui.QIcon.fromTheme("add",
				QtGui.QIcon(ICON_PATH + "add.png"),
			),
			""
		)

		self.setDocumentMode(True)

		#stored, otherwise they're removed too fast.
		self._closeButtons = set()

	def _wrapWidget(self, w):
		# We wrap the layout in a QVBoxLayout widget, so messages can be added on top of the tab.
		wrapperWidget = QtGui.QWidget()
		wrapperLayout = QtGui.QVBoxLayout()
		#no borders
		wrapperLayout.setContentsMargins(0, 0, 0, 0)

		wrapperLayout.addWidget(w)
		wrapperWidget.setLayout(wrapperLayout)
		w.wrapperWidget = wrapperWidget

		return wrapperWidget

	def addTab(self, w, *args, **kwargs):
		w.setAutoFillBackground(True)
		return self.insertTab(self.count() -1, w, *args, **kwargs) #-1 because of +-tab

	def insertTab(self, i, w, *args, **kwargs):
		wrappedWidget = self._wrapWidget(w)

		#create tab
		i = super(FilesTabWidget, self).insertTab(i, wrappedWidget, *args, **kwargs)

		#add close button
		closeButton = CloseButton()
		self._closeButtons.add(closeButton)
		self.tabBar().setTabButton(i, QtGui.QTabBar.RightSide, closeButton)

		#set new tab to current
		self.setCurrentIndex(i)

		return i

class OpenTeacherWidget(QtGui.QMainWindow):
	activityChanged = QtCore.pyqtSignal([object])

	def __init__(self, startWidget=None, requestClose=lambda: None, aeroSetting=False, *args, **kwargs):
		super(OpenTeacherWidget, self).__init__(*args, **kwargs)

		self.resize(640, 520)

		#used to ask for permission before closing the window.
		self._requestClose = requestClose

		#tabWidget
		self.tabWidget = FilesTabWidget(startWidget, self)

		self.setCentralWidget(self.tabWidget)

		#File menu
		self.fileMenu = QtGui.QMenu(self)
		self.menuBar().addMenu(self.fileMenu)

		newIcon = QtGui.QIcon.fromTheme("document-new",
			QtGui.QIcon(ICON_PATH + "new.png"),
		)
		self.newAction = QtGui.QAction(newIcon, "", self)
		self.newAction.setShortcut(QtGui.QKeySequence.New)
		self.fileMenu.addAction(self.newAction)

		openIcon = QtGui.QIcon.fromTheme("document-open",
			QtGui.QIcon(ICON_PATH + "open.png")
		)
		self.openAction = QtGui.QAction(openIcon, "", self)
		self.openAction.setShortcut(QtGui.QKeySequence.Open)
		self.fileMenu.addAction(self.openAction)

		self.openIntoAction = QtGui.QAction(self)
		self.fileMenu.addAction(self.openIntoAction)

		self.fileMenu.addSeparator()

		saveIcon = QtGui.QIcon.fromTheme("document-save",
			QtGui.QIcon(ICON_PATH + "save.png")
		)
		self.saveAction = QtGui.QAction(saveIcon, "", self)
		self.saveAction.setShortcut(QtGui.QKeySequence.Save)
		self.fileMenu.addAction(self.saveAction)

		saveAsIcon = QtGui.QIcon.fromTheme("document-save-as",
			QtGui.QIcon(ICON_PATH + "save_as.png"),
		)
		self.saveAsAction = QtGui.QAction(saveAsIcon, "", self)
		self.saveAsAction.setShortcut(QtGui.QKeySequence.SaveAs)
		self.fileMenu.addAction(self.saveAsAction)

		self.fileMenu.addSeparator()

		printIcon = QtGui.QIcon.fromTheme("document-print",
			QtGui.QIcon(ICON_PATH + "print.png")
		)
		self.printAction = QtGui.QAction(printIcon, "", self)
		self.printAction.setShortcut(QtGui.QKeySequence.Print)
		self.fileMenu.addAction(self.printAction)

		self.fileMenu.addSeparator()

		quitIcon = QtGui.QIcon.fromTheme("application-exit",
			QtGui.QIcon(ICON_PATH + "quit.png")
		)
		self.quitAction = QtGui.QAction(quitIcon,	"", self)
		self.quitAction.setShortcut(QtGui.QKeySequence.Quit)
		self.fileMenu.addAction(self.quitAction)

		#Edit
		self.editMenu = QtGui.QMenu(self)
		self.menuBar().addMenu(self.editMenu)

		self.reverseAction = QtGui.QAction(self)
		self.editMenu.addAction(self.reverseAction)

		settingsIcon = QtGui.QIcon.fromTheme("preferences-system",
			QtGui.QIcon(ICON_PATH + "settings.png")
		)
		self.settingsAction = QtGui.QAction(settingsIcon,	"", self)
		self.editMenu.addAction(self.settingsAction)

		#View
		self.viewMenu = QtGui.QMenu(self)
		self.menuBar().addMenu(self.viewMenu)

		fullscreenIcon = QtGui.QIcon.fromTheme("view-fullscreen",
			QtGui.QIcon(ICON_PATH + "fullscreen.png")
		)
		self.fullscreenAction = QtGui.QAction(fullscreenIcon, "", self)
		self.fullscreenAction.setCheckable(True)
		self.viewMenu.addAction(self.fullscreenAction)

		#Help
		self.helpMenu = QtGui.QMenu(self)
		self.menuBar().addMenu(self.helpMenu)

		docsIcon = QtGui.QIcon.fromTheme("help",
			QtGui.QIcon(ICON_PATH + "help.png")
		)
		self.docsAction = QtGui.QAction(docsIcon, "", self)
		self.helpMenu.addAction(self.docsAction)

		aboutIcon = QtGui.QIcon.fromTheme("help-about",
			QtGui.QIcon(ICON_PATH + "about.png")
		)
		self.aboutAction = QtGui.QAction(aboutIcon, "", self)
		self.helpMenu.addAction(self.aboutAction)

		#Toolbar
		self.toolBar = self.addToolBar("")
		self.toolBar.addAction(self.newAction)
		self.toolBar.addAction(self.openAction)
		self.toolBar.addSeparator()
		self.toolBar.addAction(self.saveAction)
		self.toolBar.addAction(self.saveAsAction)
		self.toolBar.addSeparator()
		self.toolBar.addAction(self.printAction)
		self.toolBar.addSeparator()
		self.toolBar.addAction(self.quitAction)

		self.toolBar.setToolButtonStyle(QtCore.Qt.ToolButtonFollowStyle)

		# Aero glass
		if aeroSetting:
			self.setAttribute(QtCore.Qt.WA_TranslucentBackground, True)
			pal = self.palette()
			bg = pal.window().color()
			bg.setAlpha(230)
			pal.setColor(QtGui.QPalette.Window, bg)
			self.setPalette(pal)
			from ctypes import windll, c_int, byref
			windll.dwmapi.DwmExtendFrameIntoClientArea(c_int(self.winId()), byref(c_int(-1)))
			# Refill status bar
			self.statusBar().setAutoFillBackground(True)
			# Remove borders from toolbar
			self.toolBar.setStyleSheet("border: 0;")
			# Make menu bar transparent
			self.menuBar().setStyleSheet("QMenuBar { background-color:transparent; } QMenuBar::item { background-color: transparent; }")

	def closeEvent(self, event):
		if self._requestClose():
			event.accept()
		else:
			event.ignore()

	def retranslate(self):
		self.fileMenu.setTitle(_("&File"))
		self.newAction.setText(_("&New"))
		self.openAction.setText(_("&Open"))
		self.openIntoAction.setText(_("Open &into current list"))
		self.saveAction.setText(_("&Save"))
		self.saveAsAction.setText(_("Save &As"))
		self.printAction.setText(_("&Print"))
		self.quitAction.setText(_("&Quit"))

		self.editMenu.setTitle(_("&Edit"))
		self.reverseAction.setText(_("&Reverse list"))
		self.settingsAction.setText(_("&Settings"))

		self.viewMenu.setTitle(_("&View"))
		self.fullscreenAction.setText(_("Fullscreen"))

		self.helpMenu.setTitle(_("&Help"))
		self.docsAction.setText(_("&Documentation"))
		self.aboutAction.setText(_("&About"))

		self.toolBar.setWindowTitle(_("Toolbar"))

	def changeEvent(self, event):
		if event.type() == QtCore.QEvent.ActivationChange:
			self.activityChanged.emit(self.isActiveWindow())
