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

import tempfile
import os
import atexit
import shutil

class SourceSaverModule(object):
	def __init__(self, moduleManager, *args, **kwargs):
		super(SourceSaverModule, self).__init__(*args, **kwargs)
		self._mm = moduleManager

		self.type = "sourceSaver"

		atexit.register(self._cleanup)
		self._dirs = set()

	def enable(self):
		self.active = True

	def _cleanup(self):
		for dir in self._dirs:
			shutil.rmtree(dir)

	def saveSource(self):
		#e.g. /tmp/uuid-here
		copyBase = tempfile.mkdtemp()
		self._dirs.add(copyBase)

		#e.g. /programming_dir/openteacher
		moduleBase = os.path.dirname(__file__)
		while not moduleBase.endswith("modules"):
			moduleBase = os.path.normpath(os.path.join(moduleBase, ".."))
		originalBase = os.path.normpath(os.path.join(moduleBase, ".."))

		#make /tmp/uuid-here/modules
		os.mkdir(os.path.join(copyBase, "modules"))
		#copy python files from the original base dir to /tmp/uuid-here
		for f in os.listdir(originalBase):
			if not os.path.isfile(os.path.join(originalBase, f)) or not f.endswith(".py"):
				continue
			shutil.copy(
				os.path.join(originalBase, f),
				os.path.join(copyBase, f)
			)
		#copy all modules available in self._mm.mods
		for mod in self._mm.mods:
			dir = os.path.dirname(mod.__class__.__file__)
			commonLen = len(os.path.commonprefix([moduleBase, dir]))
			dest = os.path.join(
				copyBase,
				"modules",
				dir[commonLen:].strip(os.sep)
			)
			shutil.copytree(dir, dest, ignore=shutil.ignore_patterns("*.pyc", "*~"))
		return copyBase

	def disable(self):
		self.active = False

def init(moduleManager):
	return SourceSaverModule(moduleManager)