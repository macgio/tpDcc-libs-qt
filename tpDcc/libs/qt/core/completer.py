#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains abstract definition of basic DCC syntax completer
"""

from __future__ import print_function, division, absolute_import

from tpDcc import register
from tpDcc.libs.python import decorators


class BaseCompleter(object):
    def __init__(self):
        super(BaseCompleter, self).__init__()

    @staticmethod
    @decorators.abstractmethod
    def get_auto_import():
        return None

    @staticmethod
    @decorators.abstractmethod
    def wrap_dropped_text(namespace, text, event):
        return text


register.register_class('Completer', BaseCompleter)
