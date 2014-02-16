#! /usr/bin/env python
# -*- coding: utf-8 -*-

#	Copyright 2011, Milan Boers
#	Copyright 2011-2014, Marten de Vries
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

import os
import shutil

class HtmlSaverModule(object):
	def __init__(self, moduleManager, *args, **kwargs):
		super(HtmlSaverModule, self).__init__(*args, **kwargs)
		self._mm = moduleManager

		self.type = "save"
		self.priorities = {
			"default": 616,
		}

		self.requires = (
			self._mm.mods(type="htmlGenerator", dataType="topo"),
		)
		self.uses = (
			self._mm.mods(type="translator"),
		)
		self.filesWithTranslations = ("topoHtml.py",)

	def enable(self):
		self._modules = set(self._mm.mods(type="modules")).pop()

		try:
			translator = self._modules.default("active", type="translator")
		except IndexError:
			pass
		else:
			translator.languageChanged.handle(self._retranslate)
		self._retranslate()

		self.active = True

	def _retranslate(self):
		try:
			translator = self._modules.default("active", type="translator")
		except IndexError:
			_, ngettext = unicode, lambda a, b, n: a if n == 1 else b
		else:
			_, ngettext = translator.gettextFunctions(
				self._mm.resourcePath("translations")
			)
		self.saves = {"topo": {
			#TRANSLATORS: This is the name of an internet standard. Please
			#TRANSLATORS: just use the English name of it, unless the
			#TRANSLATORS: standard is known under another name in your
			#TRANSLATORS: language (or you have a very good reason yourself
			#TRANSLATORS: for translating it). For more information about
			#TRANSLATORS: HTML: http://en.wikipedia.org/wiki/HTML
			"html": _("Hyper Text Markup Language")
		}}

	def disable(self):
		self.active = False

		del self._modules
		del self.saves

	def save(self, type, lesson, path):
		name = os.path.splitext(os.path.basename(path))[0]
		html = self._modules.default(
			"active",
			type="htmlGenerator",
			dataType="topo"
		).generate(lesson, name=name)

		resourceDir = path + ".resources"
		os.mkdir(resourceDir)
		targetPath = os.path.join(resourceDir, "map.image")
		shutil.copy(lesson.resources["mapPath"], targetPath)

		relativeTargetPath = os.path.join(os.path.basename(resourceDir), "map.image")
		html = html.replace(lesson.resources["mapPath"], relativeTargetPath)

		with open(path, 'w') as htmlfile:
			htmlfile.write(html.encode("UTF-8"))

		lesson.path = None

def init(moduleManager):
	return HtmlSaverModule(moduleManager)
