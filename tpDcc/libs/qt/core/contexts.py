#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains contexts for Qt
"""

from __future__ import print_function, division, absolute_import

import sys
import contextlib

from Qt.QtWidgets import QApplication

from tpDcc import dcc


@contextlib.contextmanager
def application():
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)
        yield app
        app.exec_()
    else:
        yield app
        if dcc.is_standalone():
            app.exec_()
