#! /usr/bin/env python
# -*- coding: utf-8 -*-

#	Copyright 2011, Marten de Vries
#	Copyright 2011, Cas Widdershoven
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

class NormalLessonType(object):
	def __init__(self, manager, list, *args, **kwargs):
		super(NormalLessonType, self).__init__(*args, **kwargs)

		self.list = list[:] #copy

		self.name = "Normal lesson" #FIXME: translate
		self.supports = ("lessonType",)
		self.manager = manager

		self.newItem = self.manager.createEvent()
		self.lessonDone = self.manager.createEvent()

	def start(self):
		self.newItem.emit(self.list.pop())

	def setResult(self, result):
		#FIXME: store results!
		self.newItem.emit(self.list.pop())

class NormalLessonTypeModule(object):
	def __init__(self, manager, *args, **kwargs):
		super(NormalLessonTypeModule, self).__init__(*args, **kwargs)

		self.manager = manager
		self.supports = ("lessonType",)

	def getLessonType(self, list):
		return NormalLessonType(self.manager, list)

def init(manager):
	return NormalLessonTypeModule(manager)
