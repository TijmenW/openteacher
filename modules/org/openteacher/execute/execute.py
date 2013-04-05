#! /usr/bin/env python
# -*- coding: utf-8 -*-

#	Copyright 2011-2013, Marten de Vries
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

import argparse
import sys

class ExecuteModule(object):
	"""When OpenTeacher is run, this module sets a profile, controls
	   enabling of all modules in the current profile, sends an event
	   (``startRunning``) when that's done so other modules can take
	   over control at the right time, and handles exiting gracefully
	   after that by sending the ``aboutToExit`` event.

	   In other words, this module controls the complete execution of
	   OpenTeacher from the moment on the moduleManager is initialized.

	"""
	def __init__(self, moduleManager, *args, **kwargs):
		super(ExecuteModule, self).__init__(*args, **kwargs)
		self._mm = moduleManager

		self.type = "execute"
		self.requires = (
			self._mm.mods(type="event"),
		)
		self.uses = (
			self._mm.mods(type="settings"),
			self._mm.mods(type="translator"),
		)
		self.filesWithTranslations = ("execute.py",)
		self.active = True

	def _getMod(self, *args, **kwargs):
		mods = set(self._mm.mods(*args, **kwargs))
		if len(mods) != 1:
			raise ValueError("There has to be exactly one module installed with signature %s." % ((args, kwargs),))
		return mods.pop()

	def execute(self):
		#enable printing a stacktrace in the case of a segfault if
		#supported.
		try:
			import faulthandler
		except ImportError:
			pass
		else:
			faulthandler.enable()
		#load the settings module's dependencies (currently one)
		try:
			dataStore = self._getMod(type="dataStore")
			settings = self._getMod(type="settings")
		except ValueError:
			self._profileSetting = {"value": "all"}
		else:
			settings.initialize()
			self._profileSetting = settings.registerSetting(**{
				"internal_name": "org.openteacher.execute.startup_profile",
				"type": "profile",
				"defaultValue": "all",
				"callback": {
					"args": (),
					"kwargs": {"type": "execute"},
					"method": "_settingChanged",
				}
			})

		parser = argparse.ArgumentParser()
		parser.add_argument("-p", "--profile", **{
			"nargs": "?",
			"default": self._profileSetting["value"],
			"type": unicode,
			"help": "Start OpenTeacher with the PROFILE profile. Don't know which profiles are included? I'll give away one: 'help' ;).",
		})
		args, otherArgs = parser.parse_known_args(sys.argv)
		#remove the args we parsed from sys.argv
		del sys.argv[0:]
		sys.argv.extend(otherArgs)

		self._modules = self._getMod(type="modules")
		self._modules.profile = args.profile

		event = self._modules.default(type="event")

		self.startRunning = event.createEvent()
		self.aboutToExit = event.createEvent()

		self._modules.updateToProfile()

		#setup translation
		try:
			translator = self._modules.default("active", type="translator")
		except IndexError:
			pass
		else:
			translator.languageChanged.handle(self._retranslate)
		self._retranslate()

		self.startRunning.send()
		self.aboutToExit.send()

	def _retranslate(self):
		try:
			translator = self._modules.default("active", type="translator")
		except IndexError:
			_, ngettext = unicode, lambda a, b, n: a if n == 1 else b
		else:
			_, ngettext = translator.gettextFunctions(
				self._mm.resourcePath("translations")
			)

		self._profileSetting.update({
			"name": _("Profile"),
			"category": _("General"),
			"subcategory": _("Profile"),
		})

	def _settingChanged(self):
		try:
			dialogShower = self._modules.default("active", type="dialogShower")
			settingsDialog = self._modules.default("active", type="settingsDialog")
		except IndexError:
			pass #no guarantees can be made for these modules...
		dialogShower.showMessage.send(settingsDialog.tab, "Restart OpenTeacher for this setting to take effect.")

def init(moduleManager):
	return ExecuteModule(moduleManager)
