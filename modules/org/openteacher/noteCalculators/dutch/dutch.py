#! /usr/bin/env python
# -*- coding: utf-8 -*-

#	Copyright 2009-2011, Marten de Vries
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

class DutchNoteCalculatorModule(object):
	def __init__(self, moduleManager, *args, **kwargs):
		super(DutchNoteCalculatorModule, self).__init__(*args, **kwargs)
		self._mm = moduleManager

		self.type = "noteCalculator"
		self.uses = (
			self._mm.mods(type="translator"),
		)

	def _formatNote(self, note):
		if note == 10:
			return u"10" #makes sure '10.0' isn't returned
		return (u"%0.1f" % note).replace(".", ",")

	def _calculateFloat(self, test):
		results = map(lambda x: 1 if x["result"] == "right" else 0, test["results"])
		total = len(results)
		amountRight = sum(results)

		return float(amountRight) / float(total) * 9 + 1

	def calculateNote(self, test):
		return self._formatNote(self._calculateFloat(test))

	def calculateAverageNote(self, tests):
		note = 0
		for test in tests:
			note += self._calculateFloat(test)
		note /= len(tests)
		return self._formatNote(note)

	def enable(self):
		self.name = _("Dutch") #FIXME: own translator
		self.active = True

	def disable(self):
		self.active = False
		del self.name

def init(moduleManager):
	return DutchNoteCalculatorModule(moduleManager)
