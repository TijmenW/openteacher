#! /usr/bin/env python
# -*- coding: utf-8 -*-

#	Copyright 2011, Cas Widdershoven
#	Copyright 2011, Marten de Vries
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

from PyQt4 import QtGui, QtCore

class TypingTeachWidget(QtGui.QWidget):
	def __init__(self, *args, **kwargs):
		super(TypingTeachWidget, self).__init__(*args, **kwargs)

		self.inputLineEdit = QtGui.QLineEdit()

		self.checkButton = QtGui.QPushButton(u"Check!")
		self.checkButton.setShortcut(QtCore.Qt.Key_Return) #FIXME: translatable?
		self.correctButton = QtGui.QPushButton(u"Correct anyway")

		mainLayout = QtGui.QGridLayout()
		mainLayout.addWidget(self.inputLineEdit, 0, 0)
		mainLayout.addWidget(self.checkButton, 0, 1)
		mainLayout.addWidget(self.correctButton, 1, 1)
		self.setLayout(mainLayout)

	def updateLessonType(self, lessonType):
		self.lessonType = lessonType

		self.lessonType.newItem.handle(self.newItem)

		self.checkButton.clicked.connect(self.checkAnswer)
		self.correctButton.clicked.connect(self.lessonType.correctLastAnswer)

	def newItem(self, item):
		self.item = item
		self.inputLineEdit.clear()
		self.inputLineEdit.setFocus()

	def checkAnswer(self):
		if self.inputLineEdit.text() in self.item.answers:
			self.lessonType.setResult("right")
		else:
			self.lessonType.setResult("wrong")

class TypingTeachTypeModule(object):
	def __init__(self, moduleManager, *args, **kwargs):
		super(TypingTeachTypeModule, self).__init__(*args, **kwargs)
		self.supports = ("teachType",)
		self.requires = (1, 0)
		self._mm = moduleManager

	def enable(self):
		self.type = "words"
		self.name = "Type Answer"
		self.active = True

	def disable(self):
		self.active = False
		del self.type
		del self.name

	def createWidget(self):
		return TypingTeachWidget()

def init(moduleManager):
	return TypingTeachTypeModule(moduleManager)