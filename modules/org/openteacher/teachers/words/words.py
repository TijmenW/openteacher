#! /usr/bin/env python
# -*- coding: utf-8 -*-

#	Copyright 2011-2013, Marten de Vries
#	Copyright 2011-2012, Cas Widdershoven
#	Copyright 2012, Milan Boers
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

import datetime
import copy
import weakref

def getTeachSettingsWidget():
	class TeachSettingsWidget(QtGui.QWidget):
		def __init__(self, settings, widgets, *args, **kwargs):
			super(TeachSettingsWidget, self).__init__(*args, **kwargs)

			self._settings = settings

			self.startLessonButton = QtGui.QPushButton()
			self.formLayout = QtGui.QFormLayout()

			self._settingsKeys = ["lessonType", "listModifiers", "itemModifiers"]#, "dontShowAgain"]
			for key in self._settingsKeys:
				setting = settings[key]
				try:
					widget = widgets[setting["type"]](setting)
				except KeyError:
					#shouldn't happen, just in case...
					widget = QtGui.QLabel()
				self.formLayout.addRow("placeholder", widget)
			self.formLayout.addRow(self.startLessonButton)

			self.gb = QtGui.QGroupBox()
			self.gb.setLayout(self.formLayout)

			mainLayout = QtGui.QVBoxLayout()
			mainLayout.addWidget(self.gb)
			self.setLayout(mainLayout)

			self.retranslate()

		def retranslate(self):
			self.startLessonButton.setText(
				_("I'm ready, start the lesson!")
			)
			self.gb.setTitle(_("Lesson settings"))
			i = 0
			for key in self._settingsKeys:
				setting = self._settings[key]
				w = self.formLayout.itemAt(i, QtGui.QFormLayout.LabelRole).widget()
				w.setText(setting["name"])

				i += 1
	return TeachSettingsWidget

def getTeachLessonWidget():
	class TeachLessonWidget(QtGui.QSplitter):
		def __init__(self, keyboardWidget, *args, **kwargs):
			super(TeachLessonWidget, self).__init__(*args, **kwargs)

			self.changeSettingsButton = QtGui.QPushButton()
			self.wordLabel = QtGui.QLabel()
			self.questionLabel = QtGui.QLabel()
			font = QtGui.QFont()
			font.setPointSize(24)
			self.questionLabel.setFont(font)
			self.questionLabel.setWordWrap(True)
			self.commentLabel = QtGui.QLabel()
			self.commentLabel.setWordWrap(True)
			if keyboardWidget is not None:
				self.keyboardWidget = keyboardWidget
			self.teachTabWidget = QtGui.QTabWidget()
			self.progressBar = QtGui.QProgressBar()

			self.sideWidget = QtGui.QSplitter(QtCore.Qt.Vertical)
		
			leftLayout = QtGui.QVBoxLayout()
			leftLayout.addWidget(self.wordLabel)
			leftLayout.addWidget(self.questionLabel)
			leftLayout.addWidget(self.commentLabel)
			leftLayout.addStretch()
			leftLayout.addWidget(self.teachTabWidget)
			leftLayout.addWidget(self.progressBar)

			leftWidget = QtGui.QWidget()
			leftWidget.setLayout(leftLayout)
			
			rightLayout = QtGui.QVBoxLayout()
			try:
				rightLayout.addWidget(self.keyboardWidget)
			except AttributeError:
				pass
			rightLayout.addWidget(self.changeSettingsButton)

			rightWidget = QtGui.QWidget()
			rightWidget.setLayout(rightLayout)

			self.addWidget(self.sideWidget)
			self.addWidget(leftWidget)
			self.addWidget(rightWidget)

			#set stretch factor for widget indexes
			self.setStretchFactor(0, 1)
			self.setStretchFactor(1, 255)
			self.setStretchFactor(2, 1)

		def retranslate(self):
			self.changeSettingsButton.setText(_("Change lesson settings"))
			self.wordLabel.setText(_("Word:"))

		def addSideWidget(self, widget):
			self.sideWidget.insertWidget(0, widget)

		def removeSideWidget(self, widget):
			widget.setParent(None)
	return TeachLessonWidget

def getTeachWidget():
	class TeachWidget(QtGui.QStackedWidget):
		tabChanged = QtCore.pyqtSignal([object])
		lessonDone = QtCore.pyqtSignal()
		listChanged = QtCore.pyqtSignal([object])

		def __init__(self, moduleManager, modules, settings, widgets, keyboardWidget, applicationActivityChanged, *args, **kwargs):
			super(TeachWidget, self).__init__(*args, **kwargs)

			#FIXME > 3.0: get rid of the module manager in this widget, move
			#that logic to the module class and pass to the constructor
			#instead.
			self._mm = moduleManager
			self._modules = modules
			self._settings = settings
			self._applicationActivityChanged = applicationActivityChanged
			self._keyboardWidget = keyboardWidget

			self._buildUi(keyboardWidget, widgets)
			self._connectSignals()

			try:
				letterChosen = self._keyboardWidget.letterChosen
			except AttributeError:
				#replacement that does nothing
				letterChosen = self._modules.default(type="event").createEvent()

			#setup teachTypes
			self._teachTypeWidgets = []
			for module in self._modules.sort("active", type="teachType"): 
				if module.dataType in ("all", "words"):
					widget = module.createWidget(self.tabChanged, letterChosen, self._lessonWidget.addSideWidget, self._lessonWidget.removeSideWidget)
					self._teachTypeWidgets.append(widget)
					self._lessonWidget.teachTabWidget.addTab(widget, module.name)
			
			self.inLesson = False

		def updateLesson(self, lesson):
			self.lesson = lesson

		def _showSettings(self):
			self.setCurrentWidget(self._settingsWidget)

		def _modForPath(self, path):
			for mod in self._mm.mods:
				if mod.__class__.__file__ == path:
					return mod
			raise IndexError()

		def _startLesson(self):
			self.setCurrentWidget(self._lessonWidget)
			self._applicationActivityChanged.handle(self._activityChanged)

			path = self._settings["lessonType"]["value"]
			try:
				lessonTypeModule = self._modForPath(path)
			except IndexError:
				lessonTypeModule = self._modules.default("active", type="lessonType")

			indexes = range(len(self.lesson.list["items"]))
			for path in self._settings["listModifiers"]["value"]:
				try:
					listModifier = self._modForPath(path)
				except IndexError:
					continue
				indexes = listModifier.modifyList(indexes, self.lesson.list)

			itemModifiers = []
			for path in self._settings["itemModifiers"]["value"]:
				try:
					itemModifiers.append(self._modForPath(path).modifyItem)
				except IndexError:
					pass

			#FIXME > 3.0: maybe the item modifiers should also be applied
			#in the results dialog?
			def modifyItem(item):
				#function that applies all item modifiers on an item and
				#returns the result at the end of the chain. Before that is
				#done, it makes a copy of the item since the item modifiers
				#may modify the item in place.
				result = item.copy()
				for modify in itemModifiers:
					result = modify(result)
				return result

			self._lessonType = lessonTypeModule.createLessonType(self.lesson.list, indexes, modifyItem)

			self._lessonType.newItem.handle(self._newItem)
			self._lessonType.lessonDone.handle(self.stopLesson)

			for widget in self._teachTypeWidgets:
				widget.updateLessonType(self._lessonType)

			self._lessonType.start()

			self.inLesson = True

		def _activityChanged(self, activity):
			if activity == "inactive":
				self._pauseStart = datetime.datetime.now()
			elif activity == "active":
				self._lessonType.addPause({
					"start": self._pauseStart,
					"end": datetime.datetime.now()
				})

		def _tellListAndLessonChange(self):
			"""Updates the GUI after some modifications have been made."""

			self.listChanged.emit(self.lesson.list)
			self.lesson.changed = True

		def _newItem(self, item):
			#update GUI to changes made since the last time _newItem was
			#called.
			self._tellListAndLessonChange()

			compose = self._modules.default("active", type="wordsStringComposer").compose
			self._lessonWidget.questionLabel.setText(compose(item["questions"]))
			try:
				self._lessonWidget.commentLabel.setText(item["comment"])
			except KeyError:
				self._lessonWidget.commentLabel.clear()
			self._updateProgress()

		def _updateProgress(self):
			self._lessonWidget.progressBar.setMaximum(self._lessonType.totalItems)
			self._lessonWidget.progressBar.setValue(self._lessonType.askedItems)

		def stopLesson(self, showResults=True):
			#first update the GUI since modifications have been made.
			self._tellListAndLessonChange()

			self._applicationActivityChanged.unhandle(self._activityChanged)
			self._updateProgress()

			self._showSettings()

			if showResults:
				try:
					module = self._modules.default("active", type="resultsDialog")
					module.showResults(self.lesson.list, "words", self.lesson.list["tests"][-1])
				except IndexError:
					pass

			self.inLesson = False
			
			self.lessonDone.emit()

		def _buildUi(self, keyboardWidget, widgets):
			self._settingsWidget = TeachSettingsWidget(self._settings, widgets)
			self._lessonWidget = TeachLessonWidget(keyboardWidget)

			self.addWidget(self._settingsWidget)
			self.addWidget(self._lessonWidget)

		def retranslate(self):
			self._settingsWidget.retranslate()
			self._lessonWidget.retranslate()

		def _connectSignals(self):
			#tab changed
			self._lessonWidget.teachTabWidget.currentChanged.connect(lambda i: self.tabChanged.emit(self._lessonWidget.teachTabWidget.currentWidget()))

			#start lesson button
			self._settingsWidget.startLessonButton.clicked.connect(self._startLesson)

			#change lesson settings button
			self._lessonWidget.changeSettingsButton.clicked.connect(self._showSettings)
	return TeachWidget

class WordsTeacherModule(object):
	def __init__(self, moduleManager, *args, **kwargs):
		super(WordsTeacherModule, self).__init__(*args, **kwargs)
		self._mm = moduleManager

		self.type = "wordsTeacher"
		self.priorities = {
			"default": 506,
		}

		self.uses = (
			self._mm.mods(type="translator"),
			self._mm.mods(type="itemModifier"),
			self._mm.mods(type="listModifier"),
			self._mm.mods(type="resultsDialog"),
			self._mm.mods(type="settings"),
		)
		self.requires = (
			self._mm.mods(type="ui"),
			self._mm.mods(type="wordsStringComposer"),
			self._mm.mods(type="lessonType"),
			self._mm.mods(type="teachType"),
			self._mm.mods(type="settingsWidgets"),
		)
		self.filesWithTranslations = ("words.py",)

	def createWordsTeacher(self):
		tw = TeachWidget(self._mm, self._modules, self._settings, self._widgets, self._charsKeyboard, self._applicationActivityChanged)
		self._activeWidgets.add(weakref.ref(tw))
		self._retranslate()

		return tw

	@property
	def _widgets(self):
		return self._modules.default("active", type="settingsWidgets").widgets

	@property
	def _charsKeyboard(self):
		try:
			return self._modules.default(
				"active",
				type="charsKeyboard"
			).createWidget()
		except IndexError:
			return

	@property
	def _applicationActivityChanged(self):
		uiModule = set(self._mm.mods("active", type="ui")).pop()
		return uiModule.applicationActivityChanged

	def enable(self):
		global QtCore, QtGui
		try:
			from PyQt4 import QtCore, QtGui
		except ImportError:
			return
		global TeachLessonWidget, TeachSettingsWidget, TeachWidget
		TeachLessonWidget = getTeachLessonWidget()
		TeachSettingsWidget = getTeachSettingsWidget()
		TeachWidget = getTeachWidget()

		self._modules = set(self._mm.mods(type="modules")).pop()
		self._activeWidgets = set()

		try:
			registerSetting = self._modules.default(type="settings").registerSetting
		except IndexError:
			def registerSetting(name, **kwargs):
				kwargs["value"] = kwargs.pop("defaultValue")
				return kwargs

		modToOption = lambda mod: (mod.name, mod.__class__.__file__)
		lessonTypeOptions = map(modToOption, self._modules.sort("active", type="lessonType"))
		listModifierOptions = map(modToOption, self._modules.sort("active", type="listModifier"))
		itemModifierOptions = map(modToOption, self._modules.sort("active", type="itemModifier"))
		self._settings = {
			"lessonType": registerSetting(**{
				"internal_name": "org.openteacher.teachers.words.lessonType",
				"type": "option",
				"options": lessonTypeOptions,
				"defaultValue": lessonTypeOptions[0][1] if len(lessonTypeOptions) > 0 else None,
			}),
			"listModifiers": registerSetting(**{
				"internal_name": "org.openteacher.teachers.words.listModifiers",
				"type": "multiOption",
				"options": listModifierOptions,
				"defaultValue": listModifierOptions[0][1] if len(listModifierOptions) > 0 else None,
			}),
			"itemModifiers": registerSetting(**{
				"internal_name": "org.openteacher.teachers.words.itemModifiers",
				"type": "multiOption",
				"options": itemModifierOptions,
				"defaultValue": itemModifierOptions[0][1] if len(itemModifierOptions) > 0 else None,
			}),
#FIXME: make this actually work... :S
#			"dontShowAgain": registerSetting(**{
#				"internal_name": "org.openteacher.teachers.words.dontShowAgain",
#				"type": "boolean",
#				"defaultValue": False,
#			}),
		}

		try:
			translator = self._modules.default("active", type="translator")
		except IndexError:
			pass
		else:
			translator.languageChanged.handle(self._retranslate)
		self._retranslate()

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

		self._settings["lessonType"]["name"] = _("Lesson type")
		self._settings["listModifiers"]["name"] = _("Word list order and filters")
		self._settings["itemModifiers"]["name"] = _("Word modifications")
#		self._settings["dontShowAgain"]["name"] = _("Don't show this screen again when I start a lesson.")

		for setting in self._settings.values():
			setting.update({
				"category": _("Words lesson"),
				"subcategory": _("Lesson settings")
			})

		for widget in self._activeWidgets:
			r = widget()
			if r is not None:
				r.retranslate()

	def disable(self):
		self.active = False

		del self._modules
		del self._activeWidgets
		del self._settings

def init(moduleManager):
	return WordsTeacherModule(moduleManager)
