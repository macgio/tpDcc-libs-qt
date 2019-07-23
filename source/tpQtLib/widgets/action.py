#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that defines that implements different types of actions
"""

from __future__ import print_function, division, absolute_import

from Qt.QtCore import *
from Qt.QtWidgets import *


class SeparatorLine(QFrame, object):

    pass


class SeparatorWidgetAction(QFrame, object):

    pass


class SeparatorAction(QWidgetAction, object):
    def __init__(self, label='', parent=None):
        super(SeparatorAction, self).__init__(parent)

        self._widget = SeparatorWidgetAction(parent)
        self._label = QLabel(self._widget)
        self._label.setText(label)
        self._line = SeparatorLine(self._widget)
        self._line.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def widget(self):
        """
        Returns separator widget action object
        :return: SeparatorWidgetAction
        """

        return self._widget

    def label(self):
        """
        Returns label widget object
        :return: SeparatorLine
        """

        return self._label

    def line(self):
        """
        Returns line widget
        :return: SeparatorLine
        """

        return self._line

    def setText(self, text):
        """
        Overrides base QWidgetAction setText function
        Sets the text of the separator
        :param text: str
        """

        self._label().setText(text)

    def createWidget(self, menu):
        """
        Overrides base QWidgetAction createWidget function
        :param menu: QMenu
        """

        action_widget = self.widget()
        action_layout = QHBoxLayout(action_widget)
        action_layout.setContentsMargins(0, 0, 0, 0)
        action_layout.addWidget(self.label())
        action_layout.addWidget(self.line())
        action_widget.setLayout(action_layout)

        return action_widget


class LabelAction(QWidgetAction, object):

    def __init__(self, name='', parent=None):
        super(LabelAction, self).__init__(parent)

        self._name = name

    def createWidget(self, menu):
        """
        Overrides base QWidgetAction createWidget function
        :param menu: QMenu
        """

        widget = QFrame(self.parent())
        widget.setObjectName('filterByAction')
        title = self._name
        label = QCheckBox(widget)
        label.setText(title)
        label.setAttribute(Qt.WA_TransparentForMouseEvents)
        label.toggled.connect(self._on_triggered)
        label.setStyleSheet("""
        #QCheckBox::indicator:checked {
            image: url(none.png)
        }
        QCheckBox::indicator:unchecked {
            image: url(none.png)
        }
        """)
        action_layout = QHBoxLayout(widget)
        action_layout.setContentsMargins(0, 0, 0, 0)
        action_layout.addWidget(label, stretch=1)
        widget.setLayout(action_layout)

        return widget

    def _on_triggered(self, checked=None):
        """
        Internal callback function that is triggered when the checkbox value has changed
        :param checked: bool
        """

        self.triggered.emit()
        self.parent().close()


class SliderWidgetAction(QFrame):
    pass


class SliderAction(QWidgetAction):

    def __init__(self, label="", parent=None):
        super(SliderAction, self).__init__(parent)

        self._widget = SliderWidgetAction(parent)
        self._label = QLabel(label, self._widget)

        self._slider = QSlider(Qt.Horizontal, self._widget)
        self._slider.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.valueChanged = self._slider.valueChanged

    def widget(self):
        """
        Returns the widget for this action
        :return: QWidget
        """

        return self._widget

    def label(self):
        """
        Returns label widget for this action
        :return: QLabel
        """

        return self._label

    def slider(self):
        """
        Returns slider action widget for this action
        :return: SliderWidgetAction
        """

        return self._slider

    def createWidget(self, menu):
        """
        Overrides base WidgetAction createWidget function
        :param menu: QMenu
        """

        action_widget = self.widget()

        action_layout = QHBoxLayout(action_widget)
        action_layout.setContentsMargins(0, 0, 0, 0)
        action_layout.addWidget(self.label())
        action_layout.addWidget(self.slider())
        action_widget.setLayout(action_layout)

        return action_widget
