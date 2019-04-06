#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains console widgets
"""

from __future__ import print_function, division, absolute_import

from tpQtLib.Qt.QtCore import *
from tpQtLib.Qt.QtWidgets import *
from tpQtLib.Qt.QtGui import *


class ConsoleInput(QLineEdit, object):
    def __init__(self, commands=[], parent=None):
        super(ConsoleInput, self).__init__(parent=parent)

        self._commands = commands

        self._model = QStringListModel()
        self._model.setStringList(self._commands)
        self._completer = QCompleter(self)
        self._completer.setModel(self._model)
        self._completer.setCompletionMode(QCompleter.PopupCompletion)
        self._completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.setCompleter(self._completer)
        self.setFont(QFont('Consolas', 9, QFont.Bold, False))


class Console(QTextEdit, object):
    def __init__(self, parent=None):
        super(Console, self).__init__(parent=parent)

        size_policy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        size_policy.setHorizontalStretch(0)
        size_policy.setVerticalStretch(0)
        size_policy.setHeightForWidth(self.sizePolicy().hasHeightForWidth())
        self.setSizePolicy(size_policy)

        self.setMaximumSize(QSize(16777215, 16777215))
        self.setStyleSheet(
            """
            background-color: rgb(49, 49, 49);
            font: 8pt "Consolas";
            color: rgb(200, 200, 200);
            """
        )

        self.setLineWrapMode(QTextEdit.NoWrap)
        self.setReadOnly(True)
        self.setContextMenuPolicy(Qt.ActionsContextMenu)

        self._clear_action = QAction('Clear', self)
        self._clear_action.triggered.connect(lambda: self.clear())
        self.addAction(self._clear_action)
