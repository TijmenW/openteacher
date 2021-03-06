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

class TestCase(unittest.TestCase):
	def testSize(self):
		if not self.mode in ("all", "gui"):
			self.skipTest("Too heavy for this test mode.")
		for mod in self._mm.mods("active", type="ui"):
			mod.qtParent.show()
			QtGui.QApplication.instance().processEvents()
			mod.qtParent.hide()

			xExpected = 660
			xResult = mod.qtParent.width()
			self.assertTrue(xResult <= xExpected, msg="Window width should be %spx at most, but was %spx." % (xExpected, xResult))

			yExpected = 520
			yResult = mod.qtParent.height()
			self.assertTrue(yResult <= yExpected, msg="Window height should be %spx at most, but was %spx." % (yExpected, yResult))

class TestModule(object):
	def __init__(self, moduleManager, *args, **kwargs):
		super(TestModule, self).__init__(*args, **kwargs)
		self._mm = moduleManager

		self.type = "test"
		self.requires = (
			self._mm.mods(type="ui"),
		)

	def enable(self):
		global QtGui
		try:
			from PyQt4 import QtGui
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
