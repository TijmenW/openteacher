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

import datetime
import exceptions
import collections
import itertools
import traceback
import sys
import json
import contextlib

PYTHON_EXCEPTIONS = dict(
	(name, exc) for name, exc in vars(exceptions).iteritems()
	if type(exc) == type(Exception)
)

PYTHON_ERROR_DEFINITION = """
var JSEvaluatorPythonError = function(name, message) {
	this.name = name;
	this.message = message;
	this.lineNumber = -1;
}
JSEvaluatorPythonError.prototype = new Error();
"""

def installQtClasses():
	global ObjectProxyClass, DictProxyClass, SequenceProxyClass

	class BaseProxyClass(QtScript.QScriptClass):
		def __init__(self, obj, toJS, toPython, *args):
			super(BaseProxyClass, self).__init__(*args)

			self._obj = obj
			self._toJS = toJS
			self._toPython = toPython

		def _pyName(self, scriptName):
			return unicode(scriptName.toString())

		def queryProperty(self, object, name, flags):
			return flags, -1

		def toPythonValue(self):
			return self._obj

	class ObjectProxyClass(BaseProxyClass):
		def _toString(self, *args, **kwargs):
			return "<%s %s>" % (self.__class__.__name__, dir(self._obj))

		def property(self, object, name, id):
			name = self._pyName(name)
			if name == "toString":
				return self._toJS(self._toString)
			try:
				return self._toJS(getattr(self._obj, name))
			except AttributeError:
				return self.engine().undefinedValue()

		def setProperty(self, object, name, id, value):
			name = self._pyName(name)
			setattr(self._obj, name, self._toPython(value))

	class DictProxyClass(BaseProxyClass):
		def _toString(self, *args, **kwargs):
			return "<%s %s>" % (self.__class__.__name__, dict(self._obj))

		def property(self, object, name, id):
			name = self._pyName(name)
			if name == "toString":
				return self._toJS(self._toString)
			try:
				return self._toJS(self._obj[name])
			except KeyError:
				return self.engine().undefinedValue()

		def setProperty(self, object, name, id, value):
			self._obj[self._pyName(name)] = self._toPython(value)

	class SequenceProxyClass(BaseProxyClass):
		def property(self, object, name, id):
			name = self._pyName(name)
			if name == "length":
				return self._toJS(len(self._obj))
			with contextlib.ignored(KeyError):
				return self._toJS({
					"join": self._join,
					"indexOf": self._indexOf,
					"filter": self._filter,
					"toString": self._toString,
					"slice": self._slice,
					"splice": self._splice,
					"push": self._push,
				}[name])
			try:
				return self._toJS(self._obj[int(name)])
			except (IndexError, ValueError):
				return self.engine().undefinedValue()

		def _join(self, sep):
			return sep.join(self._obj)

		def _filter(self, func):
			return [item for item in self._obj if func(item)]

		def _toString(self, *args, **kwargs):
			return "<%s %s>" % (
				self.__class__.__name__,
				json.dumps(list(self._obj)),
			)

		def _indexOf(self, data):
			try:
				return self._obj.index(data)
			except ValueError:
				return -1

		def _slice(self):
			"""Non-complete implementation?"""
			return [item for item in self._obj]

		def _splice(self, index, amount):
			"""Not-complete implementation?"""
			while amount:
				amount -= 1
				del self._obj[index]

		def _push(self, item):
			"""Non-complete implementation?"""
			self._obj.append(item)

		def setProperty(self, object, name, id, value):
			self._obj[int(self._pyName(name))] = self._toPython(value)

class JSObject(collections.MutableMapping):
	def __init__(self, qtScriptObj, toPython, toJS, *args, **kwargs):
		super(JSObject, self).__init__(*args, **kwargs)

		self.__dict__["_obj"] = qtScriptObj
		self.__dict__["_toPython"] = toPython
		self.__dict__["_toJs"] = toJS

	def _getPropertyOrError(self, key):
		prop = self._obj.property(key)
		if not prop.isValid() or prop.isUndefined():
			raise KeyError("No such key: %s" % key)
		return prop

	def __getitem__(self, key):
		return self._toPython(self._getPropertyOrError(key), self._obj)

	def __setitem__(self, key, value):
		self._obj.setProperty(key, self._toJs(value))

	def __delitem__(self, key):
		#raises KeyError for us if necessary
		self._getPropertyOrError(key)
		self._obj.setProperty(key, QtScript.QScriptValue())

	def __getattr__(self, attr):
		try:
			return self[attr]
		except KeyError, e:
			raise AttributeError(e)

	def __setattr__(self, attr, value):
		self[attr] = value

	def __delattr__(self, attr):
		try:
			del self[attr]
		except KeyError, e:
			raise AttributeError(e)

	def __iter__(self):
		iterator = QtScript.QScriptValueIterator(self._obj)
		while iterator.hasNext():
			iterator.next()
			yield unicode(iterator.name())

	def __len__(self):
		return sum(1 for _ in self)

	def toJSObject(self):
		return self._obj

	def __repr__(self):
		return "<%s %s>" % (self.__class__.__name__, dict(self))

	def __eq__(self, other):
		return dict(self) == dict(other)

class JSError(Exception):
	def __init__(self, name, message, lineNumber, *args, **kwargs):
		super(JSError, self).__init__(*args, **kwargs)

		self.name = name
		self.message = message
		self.lineNumber = lineNumber

	def __str__(self):
		return "%s: %s (line %s)" % (self.name, self.message, self.lineNumber)

class JSArray(collections.MutableSequence):
	def __init__(self, toJSValue, toPythonValue, value, *args, **kwargs):
		super(JSArray, self).__init__(*args, **kwargs)

		self._toJSValue = toJSValue
		self._toPythonValue = toPythonValue

		self._value = value

	def _checkBounds(self, key):
		if not 0 <= key < len(self):
			raise IndexError("Index out of bounds (%s)" % key)

	def __getitem__(self, key):
		self._checkBounds(key)
		return self._toPythonValue(self._value.property(key))

	def __delitem__(self, key):
		self._checkBounds(key)
		sef._value.setProperty(key, QtScript.QScriptValue())

	def __setitem__(self, key, value):
		self._value.setProperty(key, self._toJSValue(value))

	def __len__(self):
		return self._value.property("length").toInteger()

	def __eq__(self, other):
		return list(self) == list(other)

	def __repr__(self):
		return "<%s %s>" % (self.__class__.__name__, list(self))

	def insert(self, index, value):
		self._value.property("splice").call(self._value, [
			self._toJSValue(a)
			for a in [index, 0, value]
		])

	def toJSObject(self):
		return self._value

class JSEvaluator(object):
	JSError = JSError

	def __init__(self, *args, **kwargs):
		super(JSEvaluator, self).__init__(*args, **kwargs)

		self._engine = QtScript.QScriptEngine()
		self._functionCache = {}
		self._objectCache = {}
		self._proxyReferences = set()
		self._counter = itertools.count()

		self.eval(PYTHON_ERROR_DEFINITION)

	def _newId(self):
		return next(self._counter)

	def eval(self, js):
		result = self._engine.evaluate(js)
		self._checkForErrors()
		return self._toPythonValue(result)

	def _pythonExceptionFor(self, jsExc):
		name = unicode(jsExc.property("name").toString())
		message = unicode(jsExc.property("message").toString())
		lineNumber = int(jsExc.property("lineNumber").toString())

		try:
			msg = message + " (line %s)" % lineNumber
			return PYTHON_EXCEPTIONS[name](msg)
		except KeyError:
			return JSError(name, message, lineNumber)

	def _checkForErrors(self):
		if self._engine.hasUncaughtException():
			exc = self._engine.uncaughtException()
			self._engine.clearExceptions()
			raise self._pythonExceptionFor(exc)

	def __getitem__(self, key):
		return self._toPythonValue(self._engine.globalObject().property(key))

	def __setitem__(self, key, value):
		self._engine.globalObject().setProperty(key, self._toJSValue(value))

	def __delitem__(self, key):
		self._engine.globalObject().setProperty(key, self._engine.undefinedValue())

	def _newProxy(self, ProxyClass, value):
		proxy = ProxyClass(value, self._toJSValue, self._toPythonValue, self._engine)
		self._proxyReferences.add(proxy)
		id = self._newId()
		self._objectCache[id] = value
		return self._engine.newObject(proxy, QtScript.QScriptValue(id))

	def _toJSValue(self, value):
		#immutable values first
		try:
			return QtScript.QScriptValue(value)
		except TypeError:
			pass
		#including null (None)
		if value is None:
			return self._engine.nullValue()

		#mutable values
		#function
		if callable(value):
			return self._wrapPythonFunction(value)
		#date
		try:
			datetime = QtCore.QDateTime(value)
		except TypeError:
			pass
		else:
			if datetime.isValid():
				return self._engine.newDate(value)
		#object (JSObject)
		try:
			jsObj = value.toJSObject()
		except AttributeError:
			pass
		else:
			#reuse the current script value only when it was constructed
			#by the current engine. Otherwise Qt could throw an error.
			if jsObj.engine() == self._engine:
				return jsObj
		#object (dict-like)
		if isinstance(value, collections.Mapping):
			return self._newProxy(DictProxyClass, value)
		#sequence (list-like)
		if isinstance(value, collections.Sequence):
			return self._newProxy(SequenceProxyClass, value)
		#object (object-like)
		return self._newProxy(ObjectProxyClass, value)

	def _wrapPythonFunction(self, value):
		if not value in self._functionCache:
			def wrapper(context, engine):
				args = []
				for i in range(context.argumentCount()):
					args.append(self._toPythonValue(context.argument(i)))
				try:
					#if the last arg is a dict, use keyword arguments.
					#kinda makes up for the fact JS doesn't support
					#them...
					try:
						result = value(*args[:-1], **dict(args[-1].iteritems()))
					except (IndexError, TypeError, AttributeError):
						result = value(*args)
				except BaseException, exc:
					print >> sys.stderr, ""
					print >> sys.stderr, "Catched exception in Python code. Passing to JavaScript (this might just be fine):"
					traceback.print_exc()
					print >> sys.stderr, "---"
					#convert exceptions to JS exceptions
					args = (exc.__class__.__name__, str(exc))
					exc = self["JSEvaluatorPythonError"].new(*args)
					context.throwValue(self._toJSValue(exc))
					return
				return QtScript.QScriptValue(self._toJSValue(result))
			self._functionCache[value] = self._engine.newFunction(wrapper)
		return self._functionCache[value]

	def _toPythonValue(self, value, scope=None):
		if not scope:
			scope = self._engine.globalObject()

		getProperty = lambda key: self._toPythonValue(value.property(key))
		#immutable
		if not value.isValid():
			return None
		elif value.isBool():
			return value.toBool()
		elif value.isNumber():
			number = value.toNumber()
			if round(number) == number:
				return int(number)
			else:
				return number
		elif value.isNull():
			return None
		elif value.isString():
			return unicode(value.toString())
		elif value.isUndefined():
			return None
		#mutable
		elif value.scriptClass():
			return self._objectCache[int(value.data().toInteger())]
		elif value.isArray():
			a = JSArray(self._toJSValue, self._toPythonValue, value)
			return a
		elif value.isDate():
			return value.toDateTime().toPyDateTime()
		elif value.isFunction() or value.isError():
			def _getJsArgs(args, kwargs):
				if kwargs:
					args = list(args) + [kwargs]
				return [self._toJSValue(arg) for arg in args]
			def wrapper(*args, **kwargs):
				jsArgs = _getJsArgs(args, kwargs)
				result = value.call(scope, jsArgs)
				self._checkForErrors()
				return self._toPythonValue(result)
			def new(*args, **kwargs):
				jsArgs = _getJsArgs(args, kwargs)
				result = value.construct(jsArgs)
				self._checkForErrors()
				return self._toPythonValue(result)
			wrapper.new = new
			return wrapper
		elif value.isObject():
			return JSObject(value, self._toPythonValue, self._toJSValue)
		else:# pragma : no cover
			#can't imagine a situation in which this would happen, but
			#if it ever does, an exception is better than going on
			#silently.
			raise NotImplementedError("Can't convert such a value to Python")

class JSEvaluatorModule(object):
	def __init__(self, moduleManager, *args, **kwargs):
		super(JSEvaluatorModule, self).__init__(*args, **kwargs)
		self._mm = moduleManager

		self.type = "javaScriptEvaluator"
		self.requires = (
			self._mm.mods(type="qtApp"),
		)

	def createEvaluator(self):
		"""Returns an object that helps you interacting with JS code
		   from Python. It can be used dict-like to modify the JS global
		   scope, and evaluate JavaScript code via its ``eval`` method.

		   You can also call JS functions by accessing them in the dict-
		   like way, e.g.:

		   ``evaluator["JSON"]["stringify"]({"test": True})``

		   Or use the .new() on a value to make an instance as with the
		   JS new keyword:

		   ``evaluator["Date"].new()``

		"""
		return JSEvaluator()

	def enable(self):
		global QtCore, QtScript
		try:
			from PyQt4 import QtCore, QtScript
		except ImportError:# pragma: no cover
			return
		installQtClasses()
		self.active = True

	def disable(self):
		self.active = False

def init(moduleManager):
	return JSEvaluatorModule(moduleManager)
