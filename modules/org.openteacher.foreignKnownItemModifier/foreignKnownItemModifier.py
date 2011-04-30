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

class ForeignKnownModule(object):
	def __init__(self, moduleManager, *args, **kwargs):
		super(ForeignKnownModule, self).__init__(*args, **kwargs)
		self._mm = moduleManager

		self.supports = ("itemModifier",)
		self.requires = (1, 0)
		self.active = False

	def modifyItem(self, item):
		#modify in place, because the caller is responsable for passing
		#a copy of item.
		item.questions, item.answers = item.answers, item.questions
		return item

	def enable(self):
		self.type = "words"
		self.name = "Foreign - Known"
		self.active = True

	def disable(self):
		self.active = False
		del self.type
		del self.name

def init(moduleManager):
	return ForeignKnownModule(moduleManager)
