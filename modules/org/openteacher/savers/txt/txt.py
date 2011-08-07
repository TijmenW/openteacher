#! /usr/bin/env python
# -*- coding: utf-8 -*-

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

class TxtSaverModule(object):
	def __init__(self, moduleManager, *args, **kwargs):
		super(TxtSaverModule, self).__init__(*args, **kwargs)
		self._mm = moduleManager

		self.type = "save"

	def enable(self):
		self._modules = set(self._mm.mods("active", type="modules")).pop()
		self._modules.registerModule("Plain text (.txt) saver", self)
		self.saves = {"words": ["txt"]}

		self.active = True

	def disable(self):
		self.active = False

		del self._modules
		del self.saves

	def save(self, type, list, path, resources):		
		composers = set(self._mm.mods("active", type="wordsStringComposer"))
		compose = self._modules.chooseItem(composers).compose

		text = u""

		if "title" in list:
			text += list["title"] + "\n\n"
		if "questionLanguage" in list and "answerLanguage" in list:
			text += list["questionLanguage"] + " - " + list["answerLanguage"] + "\n\n"

		if len(list["items"]) != 0:
			#FIXME: questions -> not guaranteed to be there
			lengths = map(lambda word: len(compose(word["questions"])), list["items"])
			maxLen = max(lengths) +1
			#FIXME: should 8 be an advanced setting?
			if maxLen < 8:
				maxLen = 8

			for word in list["items"]:
				try:
					questions = compose(word["questions"])
				except KeyError:
					questions = u""
				text += u"".join([
					questions,
					(maxLen - len(questions)) * " ",
					#FIXME: answers -> not guaranteed to be there
					compose(word["answers"]),
					u"\n"
				])

		open(path, "w").write(text.encode("UTF-8"))

def init(moduleManager):
	return TxtSaverModule(moduleManager)
