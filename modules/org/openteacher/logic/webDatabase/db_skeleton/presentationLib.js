/*
	Copyright 2013, Marten de Vries

	This file is part of OpenTeacher.

	OpenTeacher is free software: you can redistribute it and/or modify
	it under the terms of the GNU General Public License as published by
	the Free Software Foundation, either version 3 of the License, or
	(at your option) any later version.

	OpenTeacher is distributed in the hope that it will be useful,
	but WITHOUT ANY WARRANTY; without even the implied warranty of
	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
	GNU General Public License for more details.

	You should have received a copy of the GNU General Public License
	along with OpenTeacher.  If not, see <http://www.gnu.org/licenses/>.
*/

exports.xmlEscape = function (xml) {
	xml = xml.replace(/&/g, "&amp;");
	xml = xml.replace(/>/g, "&gt;");
	xml = xml.replace(/</g, "&lt;");

	return xml;
};

exports.generateWordsHtml = function (list) {
	return generateWordsHtml(list, {margin: "1em"});
};
