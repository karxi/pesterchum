# -*- coding=UTF-8; tab-width: 4 -*-
# karxi: This file is a stand-in until I write my own to take its place.
# cf. https://pythonhosted.org/pyamp/_modules/pyamp/ui/qt/styleSheet.html
# ==================================
# Copyright 2012 Brett Ponsler
# This file is part of pyamp.
#
# pyamp is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# pyamp is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with pyamp.  If not, see <http://www.gnu.org/licenses/>.
'''The styleSheet module contains the StyleSheet class which provides the
ability to more easily create a string for setting the style sheet of a
QWidget.

'''


class StyleSheet:
    '''The StyleSheet class provides a wrapper for :class:`PyQt4.QtGui.QWidget`
    style sheet strings. StyleSheets can be easily created an exported into a
    string that is properly formatted for setting the style sheet of a
    :class:`PyQt4.QtGui.QWidget`.

    Example::

        from PyQt4.QtGui import QApplication, QWidget
        from pyamp.ui.qt import StyleSheet

        # Create the widget, and set its name
        app = QApplication([])
        widget = QWidget()
        widget.setObjectName("ObjectName")

        # Create a simple style sheet
        style = StyleSheet(border="2px solid black")
        normal = "border: 2px solid black"

        # These calls are identical
        widget.setStyleSheet(str(style))
        widget.setStyleSheet(normal)

        # Create another style sheet, notice that underscores in the
        # StylSheet parameter names are converted to dashes in the
        # style sheet string
        style = StyleSheet(background_color="red", color="blue",
                           font_weight="bold")
        normal = "background-color: red; color: blue; font-weight: bold"

        # These calls are identical
        widget.setStyleSheet(str(style))
        widget.setStyleSheet(normal)

        # You can also specify a specific CSS selector string, which can be
        # either a specific string, or a widget. If given a widget, the
        # selector will be created using the object's class name (e.g.,
        # QWidget) and will append an ID selector with the object's name (if
        # and only if the widget is named).
        style1 = StyleSheet(widget="QWidget#ObjectName",
                            border="1px solid red", margin_top="10")
        style2 = StyleSheet(widget, border="1px solid red", margin_top="10")
        normal = "QWidget#ObjectName { border: 1px solid red; margin-top: 10;"

        # These calls are identical
        widget.setStyleSheet(str(style1))
        widget.setStyleSheet(str(style2))
        widget.setStyleSheet(normal)

    '''

    def __init__(self, widget=None, **kwargs):
        '''
        * widget -- The widget selector for this style sheet. Can be either a
                    string, or an actual widget object
        * kwargs -- The keyword arguments

        '''
        self.__widget = widget
        self.__properties = kwargs

    def __str__(self):
        '''Convert the StyleSheet into a string.'''
        itemStr = self.__propertiesToString()

        if self.__widget is not None:
            itemStr = "%s { %s }" % (self.__getWidgetSelector(), itemStr)

        return itemStr

    def __propertiesToString(self):
        '''Convert the given properties for this StyleSheet into a string that
        is usable to set the style sheet of a QWidget.

        '''
        items = map(lambda i: "%s: %s" % (self.__fixName(i[0]), i[1]),
                    self.__properties.items())
        return '; '.join(items)

    @classmethod
    def __fixName(cls, name):
        '''Translate a class argument name to a CSS property name by
        replacing underscores with dashes.

        * name -- The name to fix

        '''
        return name.replace("_", "-")

    def __getWidgetSelector(self):
        '''Return the CSS selector based on the current widget.'''
        if type(self.__widget) != type(str()):
            # If the widget is not a string, then use its class name
            # to create the selector
            widgetStr = self.__widget.__class__.__name__

            # If the widget also has a valid object name then apply the
            # id selector for the object name to the selector
            objectName = self.__widget.objectName()
            if len(objectName) > 0:
                widgetStr += "#%s" % objectName
        else:
            # If the widget is just a string, then we should use that as
            # the selector
            widgetStr = self.__widget

        return widgetStr



# vim: set autoindent ts=4 sts=4 sw=4 textwidth=79 expandtab:
