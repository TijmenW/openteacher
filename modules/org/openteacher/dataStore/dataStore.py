#! /usr/bin/env python
# -*- coding: utf-8 -*-

#	Copyright 2011, Marten de Vries
#	Copyright 2011-2012, Milan Boers
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
#	GNU Generatypel Public License for more details.
#
#	You should have received a copy of the GNU General Public License
#	along with OpenTeacher.  If not, see <http://www.gnu.org/licenses/>.

import json
import os
import atexit

class JSONShelve(dict):
	def __init__(self, filepath, *args, **kwargs):
		super(JSONShelve, self).__init__(*args, **kwargs)
		
		self.filepath = filepath
		
		if os.path.exists(self.filepath):
			fp = open(self.filepath, 'r')
			d = json.load(fp)
			# Copy dict to self
			for key, value in d.iteritems():
				self[key] = value
			fp.close()
		else:
			pass
	
	def write(self):
		fp = open(self.filepath, 'w+')
		json.dump(self, fp)
		fp.close()

class DataStoreModule(object):
	def __init__(self, moduleManager, *args, **kwargs):
		super(DataStoreModule, self).__init__(*args, **kwargs)
		self._mm = moduleManager

		self.type = "dataStore"

		self._folderPath = self._getFolderPath()
		# Create folder path if not exists
		if not os.path.exists(self._folderPath):
			os.makedirs(self._folderPath)

		self.store = JSONShelve(os.path.join(self._folderPath, "store.json"))
		atexit.register(self.store.write)

	def _getFolderPath(self):
		if os.name == "nt":
			return os.path.join(os.getenv("appdata"), "OpenTeacher")
		else:
			return os.path.join(os.path.expanduser("~"), ".openteacher")

def init(moduleManager):
	return DataStoreModule(moduleManager)
