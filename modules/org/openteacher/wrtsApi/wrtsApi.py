#! /usr/bin/env python
# -*- coding: utf-8 -*-

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

class WrtsApiModule(object):
	def __init__(self, moduleManager):
		super(WrtsApiModule, self).__init__()
		self._mm = moduleManager

		self.uses = (
			self._mm.mods(type="translator"),
		)
		self.requires = (
			self._mm.mods(type="ui"),
			self._mm.mods(type="loader"),
		)

	def enable(self):
		self._modules = set(self._mm.mods("active", type="modules")).pop()
		#load translator
		try:
			translator = self._modules.default("active", type="translator")
		except IndexError:
			_, ngettext = unicode, lambda a, b, n: a if n == 1 else b
		else:
			_, ngettext = translator.gettextFunctions(
				self._mm.resourcePath("translations")
			)

		self.name = _("Wrts API connection")

		self._ui = self._mm.import_("ui")
		self._ui._, self._ui.ngettext = _, ngettext
		self._api = self._mm.import_("api")
		self._references = set()

		self._wrtsConnection = self._api.WrtsConnection(self._mm)

		event = self._uiModule.addLessonLoadButton(_("Import from WRTS"))
		event.handle(self.importFromWrts)
		self._references.add(event)
		self.active = True

	@property
	def _uiModule(self):
		return self._modules.default("active", type="ui")

	def disable(self):
		self.active = False

		del self._modules
		del self.name
		del self._ui
		del self._api
		del self._references
		del self._wrtsConnection

	def importFromWrts(self):
		ld = self._ui.LoginDialog(self._uiModule.qtParent)

		tab = self._uiModule.addCustomTab(ld.windowTitle(), ld)
		tab.closeRequested.handle(tab.close)
		ld.rejected.connect(tab.close)
		ld.accepted.connect(tab.close)

		ld.exec_()
		if not ld.result():
			return

		self._wrtsConnection.logIn(ld.email, ld.password)

		listsParser = self._wrtsConnection.listsParser

		ldc = self._ui.ListChoiceDialog(listsParser.lists, self._uiModule.qtParent)

		tab = self._uiModule.addCustomTab(ldc.windowTitle(), ldc)
		tab.closeRequested.handle(tab.close)
		ldc.rejected.connect(tab.close)
		ldc.accepted.connect(tab.close)

		ldc.exec_()
		if not ldc.result():
			return

		listUrl = listsParser.getWordListUrl(ldc.selectedRowIndex)
		list = self._wrtsConnection.importWordList(listUrl)

		self._modules.default(
			"active",
			type="loader"
		).loadFromList("words", list)

def init(moduleManager):
	return WrtsApiModule(moduleManager)
