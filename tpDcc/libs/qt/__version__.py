#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Version module for tpDcc-libs-qt
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

from ._version import get_versions


__version__ = get_versions()['version']
del get_versions
