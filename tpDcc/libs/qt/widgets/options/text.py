#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains text option implementations
"""

from __future__ import print_function, division, absolute_import

from Qt.QtCore import *
from Qt.QtWidgets import *

import tpDcc as tp
from tpDcc.libs.qt.core import base
from tpDcc.libs.qt.widgets import layouts, label, buttons, lineedit
from tpDcc.libs.qt.widgets.options import option


class TextOption(option.Option, object):
    def __init__(self, name, parent, main_widget):
        super(TextOption, self).__init__(name=name, parent=parent, main_widget=main_widget)

    def get_option_type(self):
        return 'text'

    def get_option_widget(self):
        return TextWidget(self._name)

    def get_value(self):
        value = self._option_widget.get_text()
        if not value:
            value = ''

        return value

    def set_value(self, value):
        value = str(value)
        self._option_widget.set_text(value)

    def _setup_option_widget_value_change(self):
        self._option_widget.textChanged.connect(self._on_value_changed)


class NonEditTextOption(TextOption, object):
    def __init__(self, name, parent, main_widget):
        super(NonEditTextOption, self).__init__(name=name, parent=parent, main_widget=main_widget)

    def get_option_type(self):
        return 'nonedittext'

    def get_option_widget(self):
        text_widget = super(NonEditTextOption, self).get_option_widget()
        text_widget.text_widget.setReadOnly(True)
        text_widget.insert_button.setVisible(False)
        return text_widget


class TextWidget(base.BaseWidget, object):
    textChanged = Signal(str)

    def __init__(self, name='', parent=None):
        self._name = name
        super(TextWidget, self).__init__(parent=parent)

        self._use_button = False
        self._suppress_button_command = False

    def get_main_layout(self):
        main_layout = layouts.HorizontalLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        return main_layout

    def get_text_widget(self):
        return lineedit.BaseLineEdit()

    def _setup_text_widget(self):
        self.text_widget.textChanged.connect(self._on_text_changed)

    def ui(self):
        super(TextWidget, self).ui()

        self.text_widget = self.get_text_widget()
        self.text_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.text_label = label.BaseLabel(self._name)
        self.text_label.setAlignment(Qt.AlignRight)
        self.text_label.setMinimumWidth(75)
        self.text_label.setAttribute(Qt.WA_TransparentForMouseEvents)
        self._setup_text_widget()

        self.main_layout.addWidget(self.text_label)
        self.main_layout.addSpacing(5)
        self.main_layout.addWidget(self.text_widget)

        if not self._name:
            self.text_label.setVisible(False)

        self.insert_button = buttons.BaseToolButton().image('back').icon_only()
        self.insert_button.setMaximumWidth(20)
        # self.insert_button.hide()
        self.main_layout.addWidget(self.insert_button)

    def setup_signals(self):
        self.insert_button.clicked.connect(self._on_button_command)

    def get_label_text(self):
        return self.text_label.text()

    def set_label_text(self, text):
        self.text_label.setText(text)
        self.text_label.setVisible(bool(text))

    def get_text(self):
        return self.text_widget.text()

    def set_text(self, text):
        self.text_widget.setText(text)

    def set_placeholder(self, text):
        self.text_widget.setPlaceholderText(text)

    def set_password_mode(self, flag):
        if flag:
            self.text_widget.setEchoMode(QLineEdit.Password)
        else:
            self.text_widget.setEchoMode(QLineEdit.Normal)

    def set_use_button(self, flag):
        if flag:
            self.insert_button.show()
        else:
            self.insert_button.hide()

    def get_button_text(self):
        return self.insert_button.text()

    def set_button_text(self, text):
        self.insert_button.setText(text)

    def set_button_to_first(self):
        self.main_layout.insertWidget(0, self.insert_button)

    def set_supress_button_command(self, flag):
        self._suppress_button_command = flag

    def get_text_as_list(self):
        text = str(self.text_widget.text())
        if text.find('[') > -1:
            try:
                text = eval(text)
                return text
            except Exception:
                pass

        if text:
            return [text]

    def _remove_unicode(self, list_or_tuple):
        new_list = list()
        for sub in list_or_tuple:
            new_list.append(str(sub))

    def _on_button_command(self):
        if self._suppress_button_command:
            return

        if tp.is_maya():
            import maya.cmds as cmds
            selection = cmds.ls(sl=True)
            if len(selection) > 1:
                selection = self._remove_unicode(selection)
                selection = str(selection)
            elif len(selection) == 1:
                selection = str(selection[0])
            else:
                selection = ''

            self.set_text(selection)

    def _on_text_changed(self):
        self.textChanged.emit(self.text_widget.text())
