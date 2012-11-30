#! /usr/bin/env python
# -*- coding: utf-8 -*-

#	Copyright 2012, Marten de Vries
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

class TestCase(unittest.TestCase):
	def testCodeValidity(self):
		for mod in self._mm.mods("active", "javaScriptImplementation"):
			engine = QtScript.QScriptEngine()
			engine.evaluate(mod.code)
			self.assertFalse(
				engine.hasUncaughtException(),
				"Error in JS mod '%s': %s" % (mod.__class__.__file__, engine.uncaughtException().toString())
			)

class TestModule(object):
	def __init__(self, moduleManager, *args, **kwargs):
		super(TestModule, self).__init__(*args, **kwargs)
		self._mm = moduleManager

		self.type = "test"
		self.requires = (
			self._mm.mods(type="ui"),
		)
		self.uses = (
			self._mm.mods("javaScriptImplementation"),
		)

	def enable(self):
		global QtScript
		try:
			from PyQt4 import QtScript
		except ImportError:
			return
		self.TestCase = TestCase
		self.TestCase._mm = self._mm
		self.active = True

	def disable(self):
		self.active = False
		del self.TestCase

def init(moduleManager):
	return TestModule(moduleManager)
