#! /usr/bin/env python
# -*- coding: utf-8 -*-

#	Copyright 2013, Marten de Vries
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

import unittest

class DummyLesson(object):
	def __init__(self, *args, **kwargs):
		super(DummyLesson, self).__init__(*args, **kwargs)

		self.list = {}
		self.resources = {}

class TestCase(unittest.TestCase):
	def testGeneratingMinimalLesson(self):
		for mod in self._mm.mods("active", type="htmlGenerator"):
			html = mod.generate(DummyLesson())
			try:
				self.assertIn("<html>", html)
			except:
				print mod
				raise

	def testAllActive(self):
		self.assertEqual(
			set(self._mm.mods(type="htmlGenerator")),
			set(self._mm.mods("active", type="htmlGenerator")),
		)

class TestModule(object):
	def __init__(self, moduleManager, *args, **kwargs):
		super(TestModule, self).__init__(*args, **kwargs)
		self._mm = moduleManager

		self.type = "test"
		self.requires = (
			self._mm.mods(type="htmlGenerator"),
		)

	def enable(self):
		self.TestCase = TestCase
		self.TestCase._mm = self._mm
		self.active = True

	def disable(self):
		self.active = False
		del self.TestCase

def init(moduleManager):
	return TestModule(moduleManager)
