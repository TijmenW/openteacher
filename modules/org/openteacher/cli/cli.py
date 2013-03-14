#! /usr/bin/env python
# -*- coding: utf-8 -*-

#	Copyright 2012-2013, Marten de Vries
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

import argparse
import sys
import glob
import os

class DummyLesson(object):
	def __init__(self, lessonDict, *args, **kwargs):
		super(DummyLesson, self).__init__(*args, **kwargs)

		self.list = lessonDict["list"]
		self.resources = lessonDict["resources"]

def getEnterEdit(Event):
	class EnterEdit(urwid.Edit):
		def __init__(self, *args, **kwargs):
			super(EnterEdit, self).__init__(*args, **kwargs)

			self.enterPressed = Event()

		def keypress(self, size, key):
			if key == "enter":
				self.enterPressed.send()
			else:
				return super(EnterEdit, self).keypress(size, key)

	return EnterEdit

class PractisingInterface(object):
	def __init__(self, createController, lessonType, *args, **kwargs):
		super(PractisingInterface, self).__init__(*args, **kwargs)

		self._controller = createController()
		self._controller.lessonType = lessonType
		self._connectToEvents()
		self._setupUi()

	def _connectToEvents(self):
		self._controller.clearInput.handle(self._clearInput)
		self._controller.showCorrection.handle(self._showCorrection)
		self._controller.hideCorrection.handle(self._hideCorrection)

	def _setupUi(self):
		#setup main UI
		self._txt = urwid.Text(u"")
		self._edit = EnterEdit("ANSWER: ")
		self._edit.enterPressed.handle(self._onCheck)
		urwid.connect_signal(self._edit, "change", lambda x, y: self._controller.userIsTyping)

		checkButton = urwid.Button("Check", lambda button: self._onCheck())
		skipButton = urwid.Button("Skip", lambda button: self._controller.skipTriggered())

		divider = urwid.Divider()
		quitButton = urwid.Button("Quit", lambda button: self.quit())

		widgets = [self._txt, self._edit, divider, checkButton, skipButton, divider, quitButton]
		listBox = urwid.ListBox(widgets)
		adapter = urwid.BoxAdapter(listBox, len(widgets))
		self._mainFiller = urwid.Filler(adapter, "middle")

		#setup correction dialog
		self._correctionTxt = urwid.Text(u"")
		self._correctionFiller = urwid.Filler(self._correctionTxt, "middle")

		self._loop = urwid.MainLoop(self._mainFiller)

	def _clearInput(self):
		self._edit.edit_text = ""

	def _showCorrection(self, correctAnswer):
		self._loop.widget = self._correctionFiller
		self._correctionTxt.set_text(u"WRONG ANSWER. IT SHOULD HAVE BEEN: %s" % correctAnswer)
		self._loop.set_alarm_in(3, lambda x, y:self._controller.correctionShowingDone())

	def _hideCorrection(self):
		self._loop.widget = self._mainFiller

	def run(self):
		self._controller.lessonType.start()
		self._loop.run()

	def _onCheck(self):
		self._controller.checkTriggered(self._edit.edit_text)

	def quit(self):
		raise urwid.ExitMainLoop()

	def setNextItem(self, question):
		self._txt.set_text("QUESTION: %s" % question)

class CommandLineInterfaceModule(object):
	def __init__(self, moduleManager, *args, **kwargs):
		super(CommandLineInterfaceModule, self).__init__(*args, **kwargs)
		self._mm = moduleManager

		self.type = "cli"
		self.requires = (
			self._mm.mods(type="execute"),
			self._mm.mods(type="metadata"),
			self._mm.mods(type="wordListStringComposer"),
			self._mm.mods(type="wordListStringParser"),
			self._mm.mods(type="lessonType"),
			self._mm.mods(type="event"),
			self._mm.mods(type="inputTypingLogic"),
			self._mm.mods(type="wordsStringComposer"),
		)
		self.uses = (
			self._mm.mods(type="load"),
			self._mm.mods(type="save"),
			self._mm.mods(type="reverser"),
			self._mm.mods(type="ocrWordListLoader"),
		)
		self.priorities = {
			"cli": 0,
			"default": 960,
		}

	def _saveExts(self):
		yielded = set()
		for mod in self._modules.sort("active", type="save"):
			for exts in sorted(mod.saves.itervalues()):
				for ext in sorted(exts):
					if ext not in yielded:
						yielded.add(ext)
						yield ext

	def _load(self, path):
		for mod in self._modules.sort("active", type="load"):
			type = mod.getFileTypeOf(path)
			if type is None:
				#file not supported by this mod
				continue
			lesson = mod.load(path)
			return type, lesson
		return None, None

	def _expandPaths(self, paths):
		newPaths = []
		for selector in paths:
			newPaths.extend(glob.iglob(selector))
		return newPaths

	def _reverseList(self, args):
		type, lesson = self._load(args["input-file"])
		if not lesson:
			print >> sys.stderr, "Couldn't load file '%s', not reversing." % args["input-file"]
			return

		try:
			self._modules.default("active", type="reverser", dataType=type).reverse(lesson["list"])
		except IndexError:
			print >> sys.stderr, "Couldn't reverse the file '%s'." % args["input-file"]
			return

		self._save(type, lesson, args["output-file"])

	def _convert(self, args):
		inputPaths = self._expandPaths(args["input-files"])
		outputFormat = args["output_format"]

		for inputPath in inputPaths:
			#loading
			type, lesson = self._load(inputPath)
			if not lesson:
				print >> sys.stderr, "Couldn't load file '%s', not converting." % inputPath
				#next file
				continue

			done = False
			outputPath = os.path.splitext(inputPath)[0] + "." + outputFormat
			if os.path.exists(outputPath):
				print >> sys.stderr, "The file '{outfile}' already exists, so '{infile}' can't be converted.".format(outfile=outputPath, infile=inputPath)
				#next file
				continue

			for mod in self._modules.sort("active", type="save"):
				for modType, exts in mod.saves.iteritems():
					if modType == type and outputFormat in exts:
						mod.save(type, DummyLesson(lesson), outputPath)
						done = True
						break
				if done:
					break
			else:
				print >> sys.stderr, "Couldn't save file '{infile}' in the '{format}' format, not converting.".format(infile=inputPath, format=outputFormat)
				#next file. Not strictly necessary, but just in case more code's added later...
				continue
			print "Converted file '{infile}' to '{outfile}'.".format(infile=inputPath, outfile=outputPath)
		print "Done."

	def _viewWordList(self, args):
		inputPaths = self._expandPaths(args["input-files"])
		for inputPath in inputPaths:
			type, lesson = self._load(inputPath)
			if type != "words":
				print >> sys.stderr, "File '%s' isn't a word list." % inputPath
				continue
			if not lesson:
				print >> sys.stderr, "Couldn't load file %s, not showing." % inputPath
				continue
			#lambda's for lazy loading. Handy for the compose case which
			#is a lot more likely to crash than the others + is
			#relatively slow. JS implementation only currently...
			print {
				"title": lambda: lesson["list"]["title"],
				"question-lang": lambda: lesson["list"]["questionLanguage"],
				"answer-lang": lambda: lesson["list"]["answerLanguage"],
				"list": lambda: self._composeWordList(lesson),
			}[args["part"]]()

	def _newWordList(self, args):
		if args["input-file"] == "-":
			inputFile = sys.stdin
		else:
			inputFile = open(args["input-file"], "r")
		data = unicode(inputFile.read(), sys.stdin.encoding or "UTF-8")

		lesson = self._parseWordList(data)

		if args["title"]:
			lesson["list"]["title"] = unicode(args["title"], encoding=sys.stdin.encoding or "UTF-8")
		if args["question_lang"]:
			lesson["list"]["questionLanguage"] = unicode(args["question_lang"], encoding=sys.stdin.encoding or "UTF-8")
		if args["answer_lang"]:
			lesson["list"]["answerLanguage"] = unicode(args["answer_lang"], encoding=sys.stdin.encoding or "UTF-8")

		self._save("words", lesson, args["output-file"])

	def _ocrWordList(self, args):
		loadWordList = self._modules.default("active", type="ocrWordListLoader").loadWordList
		lesson = loadWordList(args["input-file"])
		self._save("words", lesson, args["output-file"])

	def _save(self, type, lesson, path):
		#also strip the dot.
		ext = os.path.splitext(path)[1][1:]

		if os.path.isfile(path):
			print >> sys.stderr, "Output file already exists. Not saving."
			return

		for mod in self._modules.sort("active", type="save"):
			if not ext in mod.saves.get(type, []):
				continue
			mod.save("words", DummyLesson(lesson), path)
			print "Done."
			break
		else:
			print >> sys.stderr, "Couldn't save your input to '%s'." % path

	@property
	def _lessonTypes(self):
		lts = []
		for mod in self._modules.sort("active", type="lessonType"):
			lts.append(mod.name.encode(sys.stdin.encoding or "UTF-8"))
		return lts

	def _practiseWordList(self, args):
		inputFile = args["file"]

		type, lesson = self._load(inputFile)
		if type != "words":
			print >> sys.stderr, "File '%s' isn't a word file" % inputFile
		if not lesson:
			print >> sys.stderr, "The '%s' file can't be loaded." % inputFile

		lessonTypeMod = self._modules.default("active", type="lessonType", name=args["lesson_type"])
		lessonType = lessonTypeMod.createLessonType(lesson["list"], range(len(lesson["list"]["items"])))

		typingInputLogicMod = self._modules.default("active", type="inputTypingLogic")
		self._ui = PractisingInterface(typingInputLogicMod.createController, lessonType)

		lessonType.newItem.handle(self._setNextItem)
		lessonType.lessonDone.handle(self._ui.quit)
		self._ui.run()

	def _setNextItem(self, word):
		question = self._compose(word["questions"])
		self._ui.setNextItem(question)

	def run(self, argList=None):
		if argList is None:
			argList = sys.argv
		#setup parser: using + instead of - to distinguish from the
		#execute module's argparse. (the one providing the -p arg).
		parser = argparse.ArgumentParser(**{
			"prog": argList[0] + " -p cli",
			"prefix_chars": "+",
		})

		#--version
		version = self._metadata["name"] + " " + self._metadata["version"]
		parser.add_argument("+v", "++version", action="version", version=version)

		subparsers = parser.add_subparsers()

		#if at least one saver and loader available:
		if set(self._mm.mods("active", type="load")) and set(self._mm.mods("active", type="save")):
			#convert
			convert = subparsers.add_parser("convert", help="convert word, topo and media files", prefix_chars="+")
			convert.add_argument("+f", "++output-format", help="output format", default="otwd", choices=list(self._saveExts()))
			convert.add_argument("input-files", nargs="+", help="input files")
			convert.set_defaults(func=self._convert)

		#loader & saver required
		if set(self._mm.mods("active", type="load")) and set(self._mm.mods("active", type="save")):
			#reverse list
			reverseList = subparsers.add_parser("reverse-list", help="reverse list", prefix_chars="+")
			reverseList.add_argument("input-file", help="input files")
			reverseList.add_argument("output-file", help="output file")
			reverseList.set_defaults(func=self._reverseList)

		#if at least a loader is available.
		if set(self._mm.mods("active", type="load")):
			#view-word-list
			viewWordList = subparsers.add_parser("view-word-list", help="show a word list", prefix_chars="+")
			viewWordList.add_argument("input-files", nargs="+", help="input files")
			viewWordList.add_argument("+p", "++part", choices=["list", "title", "question-lang", "answer-lang"], default="list")
			viewWordList.set_defaults(func=self._viewWordList)

		#saver & ocrWordListLoader required
		if set(self._mm.mods("active", type="save")) and set(self._mm.mods("active", type="ocrWordListLoader")):
			#ocr-word-list
			ocrWordList = subparsers.add_parser("ocr-word-list", help="load a word list from a scan or photo", prefix_chars="+")
			ocrWordList.add_argument("input-file", help="input file")
			ocrWordList.add_argument("output-file", help="output file")
			ocrWordList.set_defaults(func=self._ocrWordList)

		#if at least a saver is available
		if set(self._mm.mods("active", type="save")):
			#new-word-list
			newWordList = subparsers.add_parser("new-word-list", help="make a new word list", prefix_chars="+")
			newWordList.add_argument("output-file", help="output file")
			newWordList.add_argument("input-file", help="input file (default: stdin)", nargs="?", default="-")
			newWordList.add_argument("+t", "++title")
			newWordList.add_argument("+q", "++question-lang")
			newWordList.add_argument("+a", "++answer-lang")
			newWordList.set_defaults(func=self._newWordList)

		#if curses framework used for practising and at least one loader
		#is available.
		if urwid and set(self._mm.mods("active", type="load")):
			#practise-word-list
			practiseWordList = subparsers.add_parser("practise-word-list", help="practise a word list", prefix_chars="+")
			practiseWordList.add_argument("file", help="the file to practise")
			practiseWordList.add_argument("+l", "++lesson-type", choices=self._lessonTypes, default=self._lessonTypes[0])
			practiseWordList.set_defaults(func=self._practiseWordList)

		args = parser.parse_args(argList[1:])
		if not len(set(vars(args)) - set(["func"])):
			parser.print_usage()
			return
		args.func(vars(args))

	def enable(self):
		global urwid
		global EnterEdit
		try:
			import urwid
		except ImportError:
			urwid = None
		self._modules = next(iter(self._mm.mods(type="modules")))
		if self._modules.profile == "cli":
			self._modules.default("active", type="execute").startRunning.handle(self.run)

		self._metadata = self._modules.default("active", type="metadata").metadata
		self._composeWordList = self._modules.default("active", type="wordListStringComposer").composeList
		self._parseWordList = self._modules.default("active", type="wordListStringParser").parseList
		self._compose = self._modules.default("active", type="wordsStringComposer").compose

		if urwid:
			Event = self._modules.default("active", type="event").createEvent
			EnterEdit = getEnterEdit(Event)

		self.active = True

	def disable(self):
		self.active = False

		del self._modules
		del self._metadata
		del self._composeWordList
		del self._parseWordList
		del self._compose

def init(moduleManager):
	return CommandLineInterfaceModule(moduleManager)
