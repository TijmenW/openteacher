#! /usr/bin/env python
# -*- coding: utf-8 -*-

#	Copyright 2011, Milan Boers
#	Copyright 2011, Marten de Vries
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

from PyQt4 import QtGui
from PyQt4 import QtWebKit
from PyQt4.phonon import Phonon


"""
The video player and web viewer combination widget with controls
"""
class MediaControlDisplay(QtGui.QWidget):
	def __init__(self,autoplay=True,*args, **kwargs):
		super(MediaControlDisplay, self).__init__(*args, **kwargs)
		
		self.autoplay = autoplay
		self.activeModule = None
		
		self.noPhonon = True
		
		for module in base._modules.sort("active", type="mediaType"):
			if module.phononControls == True:
				self.noPhonon = False
		
		self.mediaDisplay = MediaDisplay(self.autoplay, self.noPhonon)
		# Do not add the Phonon widget if it is not necessary
		if not self.noPhonon:
			self.mediaDisplay.videoPlayer.mediaObject().stateChanged.connect(self._playPauseButtonUpdate)
		
		layout = QtGui.QVBoxLayout()
		
		# Do not add the controls if there is not going to be any Phonon
		if not self.noPhonon:
			buttonsLayout = QtGui.QHBoxLayout()
			
			self.pauseButton = QtGui.QPushButton()
			self.pauseButton.setIcon(QtGui.QIcon.fromTheme("media-playback-pause",QtGui.QIcon(base._mm.resourcePath("icons/player_pause.png"))))
			self.pauseButton.clicked.connect(self.playPause)
			buttonsLayout.addWidget(self.pauseButton)
			
			self.seekSlider = Phonon.SeekSlider(self.mediaDisplay.videoPlayer.mediaObject())
			buttonsLayout.addWidget(self.seekSlider)
			
			self.volumeSlider = Phonon.VolumeSlider(self.mediaDisplay.videoPlayer.audioOutput())
			self.volumeSlider.setMaximumWidth(100)
			buttonsLayout.addWidget(self.volumeSlider)
		
		# Add the stacked widget
		layout.addWidget(self.mediaDisplay)
		
		if not self.noPhonon:
			layout.addLayout(buttonsLayout)
		
		self.setLayout(layout)
		
		# Disable the controls
		self.setControls()
	
	def showMedia(self, path, remote, autoplay):
		modules = base._modules.sort("active", type="mediaType")
		for module in modules:
			if module.supports(path):
				chosenModule = module
				break
		
		chosenModule.showMedia(chosenModule.path(path, self.autoplay), self.mediaDisplay, autoplay)
		self.activeModule = chosenModule
		
		self.setControls()
	
	def setControls(self):
		# Only if there are controls
		if not self.noPhonon:
			if self.activeModule == None or not self.activeModule.phononControls:
				self._setControlsEnabled(False)
			else:
				self._setControlsEnabled(True)
	
	def playPause(self, event):
		if not self.noPhonon:
			if self.mediaDisplay.videoPlayer.isPaused():
				self.mediaDisplay.videoPlayer.play()
			else:
				self.mediaDisplay.videoPlayer.pause()
	
	def stop(self):
		if not self.noPhonon:
			self.mediaDisplay.videoPlayer.stop()
	
	def clear(self):
		self.mediaDisplay.clear()
	
	def _playPauseButtonUpdate(self, newstate, oldstate):
		if self.mediaDisplay.videoPlayer.isPaused():
			self.pauseButton.setIcon(QtGui.QIcon.fromTheme("media-playback-play",QtGui.QIcon(base._mm.resourcePath("icons/player_play.png"))))
		else:
			self.pauseButton.setIcon(QtGui.QIcon.fromTheme("media-playback-pause",QtGui.QIcon(base._mm.resourcePath("icons/player_pause.png"))))
	
	def _setControlsEnabled(self, enabled):
		self.pauseButton.setEnabled(enabled)
		self.volumeSlider.setEnabled(enabled)
		self.seekSlider.setEnabled(enabled)

"""
The video player and web viewer combination widget
"""
class MediaDisplay(QtGui.QStackedWidget):
	def __init__(self,autoplay,noPhonon,*args, **kwargs):
		super(MediaDisplay, self).__init__(*args, **kwargs)
		
		#self.activeType = None
		self.autoplay = autoplay
		
		self.noPhonon = noPhonon
		
		if not self.noPhonon:
			self.videoPlayer = Phonon.VideoPlayer(Phonon.VideoCategory, self)
		
		self.webviewer = QtWebKit.QWebView()
		self.webviewer.settings().setAttribute(QtWebKit.QWebSettings.PluginsEnabled, True)
		
		self.addWidget(self.webviewer)
		
		if not self.noPhonon:
			self.addWidget(self.videoPlayer)
	
	def clear(self):
		self.webviewer.setHtml('''
		<html><head><title>Nothing</title></head><body></body></html>
		''')
		if not self.noPhonon:
			self.videoPlayer.stop()
		# Set the active type
		self.activeModule = None

class MediaDisplayModule(object):
	def __init__(self, moduleManager, *args, **kwargs):
		super(MediaDisplayModule, self).__init__(*args, **kwargs)
		
		global base
		base = self
		
		self._mm = moduleManager
		
		self.type = "mediaDisplay"
		self.priorities = {
			"student@home": 495,
			"student@school": 495,
			"teacher": 495,
			"wordsonly": -1,
			"selfstudy": 495,
			"testsuite": 495,
			"codedocumentation": 495,
			"all": 495,
		}

		self.requires = (
			self._mm.mods(type="settings"),
		)
		
		self.uses = (
			self._mm.mods(type="translator"),
		)
	
	def enable(self):
		self._modules = set(self._mm.mods("active", type="modules")).pop()
		self.active = True
		
		#setup translation
		global _
		global ngettext
		
		try:
			translator = self._modules.default("active", type="translator")
		except IndexError:
			_, ngettext = unicode, lambda a, b, n: a if n == 1 else b
		else:
			_, ngettext = translator.gettextFunctions(
				self._mm.resourcePath("translations")
			)
		
		# Add settings
		self._settings = self._modules.default("active", type="settings")
		# Settings (used in mediaTypes)
		self._html5VideoSetting = self._settings.registerSetting(**{
			"internal_name": "org.openteacher.lessons.media.videohtml5",
			"name": "Use HTML5 for video",
			"type": "boolean",
			"category": "Media Lesson",
			"subcategory": "Output",
			"defaultValue": False,
			"advanced": True,
		})
		
		self._html5AudioSetting = self._settings.registerSetting(**{
			"internal_name": "org.openteacher.lessons.media.audiohtml5",
			"name": "Use HTML5 for audio",
			"type": "boolean",
			"category": "Media Lesson",
			"subcategory": "Output",
			"defaultValue": False,
			"advanced": True,
		})
	
	def disable(self):
		self.active = False
		del self._settings
		del self._html5VideoSetting
		del self._html5AudioSetting
	
	def createDisplay(self, autoplay):
		return MediaControlDisplay(autoplay)

def init(moduleManager):
	return MediaDisplayModule(moduleManager)
