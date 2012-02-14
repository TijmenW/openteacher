#! /usr/bin/env python
# -*- coding: utf-8 -*-

#	Copyright 2011, Marten de Vries
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

import gettext
import locale
import os

class TranslatorModule(object):
	def __init__(self, moduleManager, *args, **kwargs):
		super(TranslatorModule, self).__init__(*args, **kwargs)
		self._mm = moduleManager

		self.type = "translator"
		self.requires = (
			self._mm.mods(type="event"),
			self._mm.mods(type="settings"),
		)

	def enable(self):
		self.active = True

		self._modules = set(self._mm.mods(type="modules")).pop()
		self.languageChanged = self._modules.default(
			type="event"
		).createEvent()

		self._languageSetting = self._modules.default(
			type="settings"
		).registerSetting(**{
			"internal_name": "org.openteacher.translator.language",
			"type": "language",
			"name": "Language", #FIXME: translate
			"defaultValue": None,
			"callback": {
				"args": ("active",),
				"kwargs": {"type": "translator"},
				"method": "sendLanguageChanged",
			}
		})

	def sendLanguageChanged(self):
		"""A wrapper method called by the setting callback, which can't
		   call the send() method directly

		"""
		self.languageChanged.send()

	@property
	def language(self):
		lang = self._languageSetting["value"]
		if not lang:
			return locale.getdefaultlocale()[0]
		return lang

	def gettextFunctions(self, localeDir, language=None):
		if not language:
			# Try to fill it
			language = self.language
		# If it is filled...
		if language:
			path = os.path.join(localeDir, language + ".mo")
			if not os.path.isfile(path):
				path = os.path.join(localeDir, language.split("_")[0] + ".mo")
			if os.path.isfile(path):
				t = gettext.GNUTranslations(open(path, "rb"))
				return t.ugettext, t.ungettext
		# Otherwise, default
		return unicode, lambda x, y, n: x if n == 1 else y

	def disable(self):
		self.active = False

		del self._modules
		del self.languageChanged

def init(moduleManager):
	return TranslatorModule(moduleManager)
