#! /usr/bin/env python
# -*- coding: utf-8 -*-

#	Copyright 2011-2012, Marten de Vries
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

#abstracts the json importing process. Hackish so this file can be
#named json.py, but it works! :D

import sys as sys

path = sys.path.pop(0)
#keep a reference so this module isn't garbage collected
this = sys.modules["json"]
del sys.modules["json"]

try:
	sys.modules["json"] = __import__("simplejson")
except ImportError:
	sys.modules["json"] = __import__("json")

sys.path.insert(0, path)
