#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains factory class to create tpRigToolkit options
"""

from __future__ import print_function, division, absolute_import

import tpDcc as tp
from tpDcc.libs.python import decorators, name as name_utils
from tpDcc.libs.qt.widgets.options import option


class OptionsFactory(object):
    def __init__(self):
        super(OptionsFactory, self).__init__()

    OPTIONS_MAP = {
        'group': add_group
    }

    def get_unique_name(self, option_list, name, parent):
        """
        Internal function that returns unique name for the new group
        :param name: str
        :param parent: QWidget
        :return: str
        """

        found = option_list.get_widget_names(parent)
        while name in found:
            name = name_utils.increment_last_number(name)

        return name

    def add_option(self, name, option_list, value=None, parent=None):
        name = self.get_unique_name(name, parent)




    def add_group(self, name='group', value=True, parent=None):
        """
        Adds new group property to the group box
        :param name: str
        :param value: bool, default value
        :param parent: Option
        """

        if type(name) == bool:
            name = 'group'

        group = option.OptionListGroup(name=name, option_object=option_object, parent=self._parent)
        group.set_expanded(value)
        if self.__class__ == OptionListGroup or parent.__class__ == OptionListGroup:
            if tp.is_maya():
                group.group.set_inset_dark()
        self._handle_parenting(group, parent)
        self._write_options(clear=False)
        self._has_first_group = True

        return group


@decorators.Singleton
class OptionsFactorySingleton(OptionsFactory, object):
    def __init__(self):
        OptionsFactory.__init__(self)
