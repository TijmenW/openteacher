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

import datetime
try:
	from elementTree import ElementTree
except ImportError:
	from xml.etree import ElementTree

class WordList(list): pass

class Word(object):
	def __init__(self):
		self.questions = []
		self.answers = []

class WrtsFileModule(object):
	def __init__(self, moduleManager):
		self._mm = moduleManager

		self.supports = ("load", "save", "initializing")
		self.requires = (1, 0)
		self.active = False

	def initialize(self):
		for module in self._mm.activeMods.supporting("settings"):
			module.registerModule("WRTS file type", self)

	def enable(self):
		self._pyratemp = self._mm.import_(__file__, "pyratemp")
		self.loads = {"wrts": ["words"]}
		self.saves = {"words": ["wrts"]}

		self.active = True

	def disable(self):
		self.active = False

		del self._pyratemp
		del self.loads
		del self.saves

	def getFileTypeOf(self, path):
		if path.endswith(".wrts"):
			return "words"

	def load(self, path):
		root = ElementTree.parse(open(path)).getroot()
		#dutch: lijst = list
		listTree = root.find("lijst")

		wordList = WordList()

		#dutch: titel = title
		wordList.title = listTree.findtext("titel")
		#dutch: taal = language
		wordList.questionSubject = listTree.findtext("taal/a")
		wordList.answerSubject = listTree.findtext("taal/b")

		#dutch: woord = word
		for wordTree in listTree.findall("woord"):
			word = Word()

			word.questions = wordTree.findtext("a").split(", ")
			word.answers = wordTree.findtext("b").split(", ")
			
			wordList.append(word)
		
		return wordList

	def save(self, type, list, path):
		templatePath = self._mm.resourcePath(__file__, "template.txt")
		t = self._pyratemp.Template(open(templatePath).read())
		data = {
			"list": list,
			"date": datetime.datetime.now().strftime("%a, %d %b %Y %H:%M:%S %z")
		}
		content = t(**data)
		open(path, "w").write(content.encode("UTF-8"))

def init(moduleManager):
	return WrtsFileModule(moduleManager)