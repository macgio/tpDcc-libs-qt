#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains different types of Qt timers
"""

from __future__ import print_function, division, absolute_import

from Qt.QtCore import *


class ClickTimer(QObject, object):
    EXECUTE = Signal()

    # region Methods
    def __init__(self):
        super(ClickTimer, self).__init__()
        self.timer_id = None
        self.init_data()

    def set_data(self, button, modifier, pos, selected):
        self.button = button
        self.modifier = modifier
        self.pos = pos
        self.isSelected = selected

    def init_data(self):
        self.button = None
        self.modifier = None
        self.pos = None
        self.isSelected = False

    def start(self, interval):
        self.timer_id = self.startTimer(interval)

    def remove_timer(self):
        if self.timer_id:
            self.killTimer(self.timer_id)
        self.timer_id = None
        return
    # endregion

    # region Override Methods
    def timerEvent(self, event):
        if self.timer_id == event.timerId():
            self.EXECUTE.emit()
        self.remove_timer()
    # endregion
