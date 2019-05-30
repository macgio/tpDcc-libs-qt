#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains consts exception used by libraries
"""

from __future__ import print_function, division, absolute_import


class ItemError(Exception):
    pass


class ItemSaveError(Exception):
    pass


class ItemLoadError(Exception):
    pass
