#! /usr/bin/env python
# -*- coding: utf-8 -*-

#	Copyright 2011, Cas Widdershoven
#	Copyright 2011, Marten de Vries
#	Copyright 2011, Milan Boers
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
import weakref

#FIXME: should parent be replaced with signals & slots? Nicer style.

class RepeatScreenWidget(QtGui.QWidget):
	def __init__(self, repeatAnswerTeachWidget, modules, *args, **kwargs):
		super(RepeatScreenWidget, self).__init__(*args, **kwargs)

		self._repeatAnswerTeachWidget = repeatAnswerTeachWidget
		self._modules = modules

		self.showAnswerScreen = QtGui.QVBoxLayout()
		self.answerLabel = QtGui.QLabel()
		self.showAnswerScreen.addWidget(self.answerLabel)
		self.setLayout(self.showAnswerScreen)

	def fade(self):
		compose = self._modules.default("active", type="wordsStringComposer").compose
		self.answerLabel.setText(compose(self._repeatAnswerTeachWidget.word["answers"]))
		timer = QtCore.QTimeLine(2000, self)
		timer.setFrameRange(0, 255)
		timer.frameChanged.connect(self.fadeAction)
		timer.finished.connect(self.finish)
		timer.start()

	def fadeAction(self, frame):
		palette = QtGui.QPalette()
		color = palette.windowText().color()
		color.setAlpha(255 - frame)
		palette.setColor(QtGui.QPalette.WindowText, color)

		self.answerLabel.setPalette(palette)

	def finish(self):
		self._repeatAnswerTeachWidget.setCurrentWidget(self._repeatAnswerTeachWidget.inputWidget)

class StartScreenWidget(QtGui.QWidget):
	def __init__(self, parent, *args, **kwargs):
		super(StartScreenWidget, self).__init__(*args, **kwargs)

		self.parent = parent

		self.label = QtGui.QLabel()
		self.startButton = QtGui.QPushButton()

		self.startScreen = QtGui.QVBoxLayout()
		self.startScreen.addWidget(self.label)
		self.startScreen.addWidget(self.startButton)
		self.setLayout(self.startScreen)

		self.startButton.clicked.connect(self.parent.startRepeat)

	def retranslate(self):
		self.label.setText(_("Click the button to start"))
		self.startButton.setText(_("Start!"))

class RepeatAnswerTeachWidget(QtGui.QStackedWidget):
	def __init__(self, modules, tabChanged, *args, **kwargs):
		super(RepeatAnswerTeachWidget, self).__init__(*args, **kwargs)

		self._modules = modules

		#make start screen
		self.startScreen = StartScreenWidget(self)
		self.addWidget(self.startScreen)

		#make "show answer" screen
		self.repeatScreen = RepeatScreenWidget(self, modules)
		self.addWidget(self.repeatScreen)

		#make input screen
		typingInput = self._modules.default("active", type="typingInput")
		self.inputWidget = typingInput.createWidget()
		self.addWidget(self.inputWidget)

		tabChanged.connect(lambda: self.setCurrentWidget(self.startScreen))

	def retranslate(self):
		self.startScreen.retranslate()

	def startRepeat(self):
		self.setCurrentWidget(self.repeatScreen)
		self.repeatScreen.fade()

	def updateLessonType(self, lessonType, *args, **kwargs):
		self.inputWidget.updateLessonType(lessonType, *args, **kwargs)
		lessonType.newItem.handle(self.newWord)

	def newWord(self, word):
		self.word = word
		self.startRepeat()

class RepeatAnswerTeachTypeModule(object):
	def __init__(self, moduleManager, *args, **kwargs):
		super(RepeatAnswerTeachTypeModule, self).__init__(*args, **kwargs)
		self._mm = moduleManager

		self.type = "teachType"
		self.priorities = {
			"student@home": 651,
			"student@school": 651,
			"teacher": 651,
			"wordsonly": 651,
			"selfstudy": 651,
			"testsuite": 651,
			"codedocumentation": 651,
			"all": 651,
		}
		self.requires = (
			self._mm.mods(type="ui"),
			self._mm.mods(type="typingInput"),
			self._mm.mods(type="wordsStringComposer"),
		)
		self.uses = (
			self._mm.mods(type="translator"),
		)

	def enable(self):
		self._modules = set(self._mm.mods(type="modules")).pop()
		
		self._activeWidgets = set()

		try:
			translator = self._modules.default("active", type="translator")
		except IndexError:
			pass
		else:
			translator.languageChanged.handle(self._retranslate)
		self._retranslate()

		self.dataType = "words"
		self.active = True

	def _retranslate(self):
		#Translations
		global _
		global ngettext

		try:
			translator = self._modules.default("active", type="translator")
		except IndexError:
			_, ngettext = unicode, lambda a, b, n: a if n == 1 else b
		else:
			_, ngettext = translator.gettextFunctions(
				self._mm.resourcePath("translations")
			)
		self.name = _("Repeat answer")

		for widget in self._activeWidgets:
			r = widget()
			if r is not None:
				r.retranslate()

	def disable(self):
		self.active = False

		del self._modules
		del self._activeWidgets
		del self.dataType
		del self.name

	def createWidget(self, tabChanged):
		ratw = RepeatAnswerTeachWidget(self._modules, tabChanged)
		self._activeWidgets.add(weakref.ref(ratw))
		return ratw

def init(moduleManager):
	return RepeatAnswerTeachTypeModule(moduleManager)
