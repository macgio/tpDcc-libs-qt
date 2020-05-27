#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Register module for tpDcc-libs-qt
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

import tpDcc.libs.qt


# =================================================================================

REGISTER_ATTR = '_registered_classes'

# =================================================================================


def register_class(cls_name, cls, is_unique=True, skip_store=False):
    """
    This function registers given class into tpRigToolkit module
    :param cls_name: str, name of the class we want to register
    :param cls: class, class we want to register
    :param is_unique: bool, Whether if the class should be updated if new class is registered with the same name
    :param skip_store: bool, Whether the registered class should be removed during cleanup operation
        Useful in scenarios where we want to cleanup registered class manually.
    """

    if REGISTER_ATTR not in tpDcc.libs.qt.__dict__:
        tpDcc.libs.qt.__dict__[REGISTER_ATTR] = list()

    if not is_unique and cls_name in tpDcc.libs.qt.__dict__:
        return

    tpDcc.libs.qt.__dict__[cls_name] = cls
    if not skip_store:
        tpDcc.libs.qt.__dict__[REGISTER_ATTR].append(cls_name)


def cleanup():

    if REGISTER_ATTR not in tpDcc.libs.qt.__dict__:
        return

    for cls_name in tpDcc.libs.qt.__dict__[REGISTER_ATTR]:
        if cls_name not in tpDcc.libs.qt.__dict__:
            continue
        print('Deleting: {}'.format(cls_name))
        del tpDcc.libs.qt.__dict__[cls_name]
    del tpDcc.libs.qt.__dict__[REGISTER_ATTR]
