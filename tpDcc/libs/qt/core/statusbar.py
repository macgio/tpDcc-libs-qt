#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Class that creates a status widgets which can be used the state of an app
"""

from __future__ import print_function, division, absolute_import

from Qt.QtCore import *
from Qt.QtWidgets import *
from Qt.QtGui import *

import tpDcc


class StatusWidget(QFrame, object):

    DEFAULT_DISPLAY_TIME = 10000  # milliseconds -> 15 seconds

    def __init__(self, *args):
        super(StatusWidget, self).__init__(*args)

        self._blocking = False
        self._timer = QTimer(self)

        self.setObjectName('StatusWidget')
        self.setFrameShape(QFrame.NoFrame)
        self.setFixedHeight(19)
        self.setMinimumWidth(5)

        self._label = QLabel('', self)
        self._label.setStyleSheet('background-color: transparent;')
        self._label.setCursor(Qt.IBeamCursor)
        self._label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self._label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        self._button = QPushButton(self)
        self._button.setMaximumSize(QSize(17, 17))
        self._button.setIconSize(QSize(20, 20))
        self._button.hide()

        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(5, 0, 0, 0)

        self.main_layout.addWidget(self._button)
        self.main_layout.addWidget(self._label)

        self.setLayout(self.main_layout)

        self._timer.timeout.connect(self._reset)

    def is_blocking(self):
        """
        Returns True if the status widget is blocking, otherwise return False
        :return: bool
        """

        return self._blocking

    def show_ok_message(self, message, msecs=None):
        """
        Set an ok message to be displayed in the status widget
        :param message: str
        :param msecs: int
        """

        if self.is_blocking():
            return

        icon = tpDcc.ResourcesMgr().icon('ok', extension='png')
        self._show_message(message, icon, msecs)

    def show_info_message(self, message, msecs=None):
        """
        Set an info message to be displayed in the status widget
        :param message: str
        :param msecs: int
        """

        if self.is_blocking():
            return

        icon = tpDcc.ResourcesMgr().icon('info', extension='png')
        self._show_message(message, icon, msecs)

    def show_warning_message(self, message, msecs=None):
        """
       Set a warning message to be displayed in the status widget
       :param message: str
       :param msecs: int
       """

        if self.is_blocking():
            return

        icon = tpDcc.ResourcesMgr().icon('warning', extension='png')
        self._show_message(message, icon, msecs)

    def show_error_message(self, message, msecs=None):
        """
       Set an error message to be displayed in the status widget
       :param message: str
       :param msecs: int
       """

        icon = tpDcc.ResourcesMgr().icon('error', extension='png')
        self._show_message(message, icon, msecs)

    def _reset(self):
        """
        Called when the current animation has finished
        """

        self._timer.stop()
        self._button.hide()
        self._label.setText('')
        icon = tpDcc.ResourcesMgr().icon('blank')
        self._button.setIcon(icon) if icon else self._button.setIcon(QIcon())
        self.setStyleSheet('')
        self._blocking = False

    def _show_message(self, message, icon, msecs=None, blocking=False):
        """
        Set the given text to be displayed in the status widget
        :param message: str
        :param icon: QIcon
        :param msecs: int
        :param blocking: bool
        """

        msecs = msecs or self.DEFAULT_DISPLAY_TIME
        self._blocking = blocking

        self._button.setStyleSheet('border: 0px;')

        if icon:
            self._button.setIcon(icon)
            self._button.show()
        else:
            self._button.hide()

        if message:
            self._label.setText(str(message))
            self._timer.stop()
            self._timer.start(msecs)
        else:
            self._reset()

        self.update()
