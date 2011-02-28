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

import pyratemp
try:
	from elementTree import ElementTree
except ImportError:
	from xml.etree import ElementTree

class List(list): pass

class Item(object):
	def __init__(self):
		self.questions = []
		self.answers = []

#FIXME: also support other types than words
class Importer(object):
	def __init__(self, manager):
		self.manager = manager
		self.imports = {"t2k": ["words"]}

	def getFileTypeOf(self, path):
		if path.endswith(".t2k"):
			return "words"

	def __call__(self, path):
		root = ElementTree.parse(open(path)).getroot()

		list = List()

		list.title = u""
		list.questionSubject = u""
		list.answerSubject = u""
		
		for item in root.findall("message_data/items/item"):
			listItem = Item()
			for question in item.findall("questions/question"):
				listItem.questions.append(question.text)

			for answer in item.findall("answers/answer"):
				listItem.answers.append(answer.text)

			list.append(listItem)
		return list

class Exporter(object):
	def __init__(self, manager):
		self.manager = manager
		self.exports = {"words": ["t2k"]}

	def __call__(self, type, list, path):
		templatePath = self.manager.resourcePath(__file__, "template.txt")
		t = pyratemp.Template(open(templatePath).read())
		data = {
			"list": list
		}
		content = t(**data)
		open(path, "w").write(content.encode("UTF-8"))

class Teach2000FileModule(object):
	def __init__(self, manager):
		self.manager = manager
		self.supports = ("state", "import", "export")

	def enable(self):
		self.importer = Importer(self.manager)
		self.exporter = Exporter(self.manager)

	def disable(self):
		del self.importer
		del self.exporter

def init(manager):
	return Teach2000FileModule(manager)
