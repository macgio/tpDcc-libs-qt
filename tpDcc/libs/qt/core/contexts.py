#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains contexts for Qt
"""

from __future__ import print_function, division, absolute_import

import sys
import contextlib

from Qt.QtWidgets import *

import tpDcc


@contextlib.contextmanager
def application():
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)
        yield app
        app.exec_()
    else:
        yield app
        if tpDcc.is_standalone():
            app.exec_()
