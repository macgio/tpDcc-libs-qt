#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains different group widgets
"""

from __future__ import print_function, division, absolute_import

from Qt.QtCore import *
from Qt.QtWidgets import *
from Qt.QtGui import *

from tpDcc.libs.python import decorators, python
from tpDcc.libs.qt.core import qtutils, base, theme
from tpDcc.libs.qt.widgets import buttons


class BaseGroup(QGroupBox, object):
    def __init__(self, name='', parent=None):
        super(BaseGroup, self).__init__(parent)

        self.setTitle(name)

        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(2, 2, 2, 2)
        self.main_layout.setSpacing(2)
        self.main_layout.setAlignment(Qt.AlignCenter)
        self.setLayout(self.main_layout)

        self.ui()
        self.setup_signals()

    def ui(self):
        """
        Function that sets up the ui of the widget
        Override it on new widgets
        """

        pass

    def setup_signals(self):
        """
        Function that set up signals of the group widgets
        """

        pass

    def set_title(self, new_title):
        """
        Set the title of the group
        """

        self.setTitle(new_title)


class CollapsableGroup(BaseGroup, object):
    def __init__(self, name='', parent=None, collapsable=True):
        super(CollapsableGroup, self).__init__(name, parent)
        self._collapsable = collapsable

    def mousePRessEvent(self, event):
        super(CollapsableGroup, self).mousePressEvent(event)

        if not event.button() == Qt.LeftButton:
            return

        if self._collapsable:
            if event.y() < 30:
                self._base_widget.setVisible(not self._base_widget.isVisible())

    def set_collapsable(self, flag):
        """
        Sets if the group can be collapsed or not
        :param collapsable: flag
        """

        self._collapsable = flag

    def expand_group(self):
        """
        Expands the content of the group
        """

        self.setFixedSize(qtutils.QWIDGET_SIZE_MAX)
        self.setVisible(True)

    def collapse_group(self):
        """
        Collapse the content of the group
        """

        self._base_widget.setVisible(False)


class BaseButtonGroup(base.BaseWidget, object):
    def __init__(self, orientation=Qt.Horizontal, parent=None):

        self._orientation = 'horizontal' if orientation == Qt.Horizontal else 'vertical'

        super(BaseButtonGroup, self).__init__(parent=parent)

    def get_main_layout(self):
        main_layout = QBoxLayout(
            QBoxLayout.LeftToRight if self._orientation == 'horizontal' else QBoxLayout.TopToBottom)
        main_layout.setContentsMargins(0, 0, 0, 0)

        return main_layout

    def ui(self):
        super(BaseButtonGroup, self).ui()

        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)

        self._button_group = QButtonGroup()

    @decorators.abstractmethod
    def create_button(self, data_dict):
        """
        Must be implemented in custom button groups
        Creates a new button for this group
        :param data_dict: dict
        :return: new button instance
        """

        raise NotImplementedError(
            'Function create_button for class "{}" is not implemented!'.format(self.__class__.__name__))

    def get_button_group(self):
        """
        Returns button group internal object
        :return: QButtonGroup
        """

        return self._button_group

    def clear(self):
        """
        Clears all buttons contained in this group
        """

        for btn in self._button_group.buttons():
            self._button_group.removeButton(btn)
            self.main_layout.removeWidget(btn)
            btn.setVisible(False)
            btn.deleteLater()

    def add_button(self, data_dict, index=None):
        """
        Adds a new button to this group
        :param data_dict: dict
        :param index: int or None
        :return: new added button
        """

        if python.is_string(data_dict):
            data_dict = {'text': data_dict}
        elif isinstance(data_dict, QIcon):
            data_dict = {'icon': data_dict}

        new_btn = self.create_button(data_dict)
        new_btn.setProperty('combine', self._orientation)

        if data_dict.get('text'):
            new_btn.setProperty('text', data_dict.get('text'))
        if data_dict.get('icon'):
            new_btn.setProperty('icon', data_dict.get('icon'))
        if data_dict.get('data'):
            new_btn.setProperty('data', data_dict.get('data'))
        if data_dict.get('checked'):
            new_btn.setProperty('checked', data_dict.get('checked'))
        if data_dict.get('shortcut'):
            new_btn.setProperty('shortcut', data_dict.get('shortcut'))
        if data_dict.get('tooltip'):
            new_btn.setProperty('toolTip', data_dict.get('tooltip'))
        if data_dict.get('clicked'):
            new_btn.clicked.connect(data_dict.get('clicked'))
        if data_dict.get('toggled'):
            new_btn.toggled.connect(data_dict.get('toggled'))

        if index is None:
            self._button_group.addButton(new_btn)
        else:
            self._button_group.addButton(new_btn, index)

        if self.main_layout.count() == 0:
            new_btn.setChecked(True)

        self.main_layout.insertWidget(self.main_layout.count(), new_btn)

        return new_btn

    def set_button_list(self, button_list):
        """
        Empties group and add all buttons given in the list of buttons
        :param button_list: list(dict)
        """

        self.clear()

        for index, data_dict in enumerate(button_list):
            new_btn = self.add_button(data_dict=data_dict, index=index)
            if index == 0:
                new_btn.setProperty('position', 'left')
            elif index == len(button_list) - 1:
                new_btn.setProperty('position', 'right')
            else:
                new_btn.setProperty('position', 'center')


class PushButtonGroup(BaseButtonGroup, object):
    def __init__(self, orientation=Qt.Horizontal, parent=None):
        super(PushButtonGroup, self).__init__(orientation=orientation, parent=parent)

        self._type = buttons.BaseButton.Types.PRIMARY
        self._size = theme.Theme.DEFAULT_SIZE
        self._button_group.setExclusive(True)
        self.set_spacing(1)

    @property
    def type(self):
        return self._type

    @type.setter
    def type(self, value):
        self._type = value

    @property
    def size(self):
        return self._size

    @size.setter
    def size(self, value):
        self._size = value

    def create_button(self, data_dict):
        """
        Implements BaseButtonGroup create_button abstract function
        :param data_dict:
        :return:
        """

        new_btn = buttons.StyleBaseButton()
        new_btn.size = data_dict.get('size', self._size)
        new_btn.type = data_dict.get('type', self._type)

        return new_btn


class RadioButtonGroup(BaseButtonGroup, object):
    checkedChanged = Signal(int)

    def __init__(self, orientation=Qt.Horizontal, parent=None):
        super(RadioButtonGroup, self).__init__(orientation=orientation, parent=parent)

        self._button_group.setExclusive(True)
        self.set_spacing(15)

    def setup_signals(self):
        self._button_group.buttonClicked.connect(self.checkedChanged)

    def create_button(self, data_dict):
        """
        Implements BaseButtonGroup create_button abstract function
        :param data_dict:
        :return:
        """

        return buttons.BaseRadioButton()

    def _get_checked(self):
        return self._button_group.checkedId()

    def _sert_checked(self, value):
        btn = self._button_group.button(value)
        if btn:
            btn.setChecked(True)
            self.checkedChanged.emiet(value)

    checked = Property(int, _get_checked, _sert_checked, notify=checkedChanged)
