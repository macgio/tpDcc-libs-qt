#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains classes to create breadcrumb widgets
"""

from __future__ import print_function, division, absolute_import

import os

from Qt.QtCore import *
from Qt.QtWidgets import *

from tpDcc.libs.python import path, python
from tpDcc.libs.qt.core import resource, base, qtutils
from tpDcc.libs.qt.widgets import label


class Breadcrumb(object):
    def __init__(self, label):
        """
        Constructor
        :param label: QLabel, label used in this breadcrumb
        """

        self._label = label

    @property
    def label(self):
        return self._label


class BreadcrumbWidget(QWidget, object):
    def __init__(self, parent=None):
        super(BreadcrumbWidget, self).__init__(parent=parent)

        self.setObjectName('BreadcrumbWidget')

        self._widgets = list()

        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        self.setLayout(main_layout)

        self._path_label = label.ElidedLabel()
        sp = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        sp.setHorizontalStretch(0)
        sp.setVerticalStretch(0)
        sp.setHeightForWidth(self._path_label.sizePolicy().hasHeightForWidth())
        self._path_label.setSizePolicy(sp)
        main_layout.addWidget(self._path_label)

    def set(self, breadcrumbs):
        """
        Populates the breadcrumb control with a list of breadcrumbs
        :param breadcrumbs: each breadcrumb should derive from Breadcrumb class
        """

        breadcrumbs = python.force_list(breadcrumbs)
        self._widgets = list()
        for b in breadcrumbs:
            if not isinstance(b, Breadcrumb):
                if type(b) in [str, unicode]:
                    self._widgets.append(Breadcrumb(b))
                else:
                    tp.logger.warning('Impossible to convert {} to Breadcrumb'.format(b))
            else:
                self._widgets.append(b)

        path = "<span style='color:#E2AC2C'> &#9656; </span>".join([crumb.label for crumb in self._widgets])
        path = "<big>%s</big>" % path

        self._path_label.setText(path)

    def set_from_path(self, file_path):
        """
        Creates a proper Breadcrumb list for given path and sets the text
        """

        self._widgets = list()
        file_path = os.path.dirname(file_path)
        folders = path.get_folders_from_path(file_path)
        self._widgets = [Breadcrumb(f) for f in folders]
        self.set(self._widgets)

    def get_texts(self):
        """
        Returns current
        :return: list(str)
        """

        return [crumb.label for crumb in self._widgets]


class BreadcrumbButtonWidget(base.BaseWidget, object):
    def __init__(self, parent=None):
        super(BreadcrumbButtonWidget, self).__init__(parent=parent)

    def ui(self):
        super(BreadcrumbButtonWidget, self).ui()

        self._bread_layout = QHBoxLayout()
        self._bread_layout.setContentsMargins(2, 2, 2, 2)
        self._bread_layout.setSpacing(2)
        self._bread_layout.setAlignment(Qt.AlignLeft)
        self.main_layout.addLayout(self._bread_layout)

    def update_path(self, names_lists):
        qtutils.clear_layout(self._bread_layout)

        for name in names_lists:
            new_btn = QPushButton(name)
            btn_width = new_btn.fontMetrics().boundingRect(new_btn.text()).width()
            new_btn.setMaximumWidth(btn_width + 10)
            self._bread_layout.addWidget(new_btn)

    def add_separator(self):
        sep_lbl = QLabel()
        sep_pixmap = resource.pixmap(name='play', extension='png').scaled(20, 20, Qt.KeepAspectRatio)
        sep_lbl.setPixmap(sep_pixmap)
        self._bread_layout.addWidget(sep_lbl)


class BreadcrumbFrame(QFrame, object):
    def __init__(self, parent=None):
        super(BreadcrumbFrame, self).__init__(parent)

        self.setObjectName('TaskFrame')
        self.setFrameStyle(QFrame.StyledPanel)

        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(2, 2, 2, 2)
        main_layout.setSpacing(2)
        self.setLayout(main_layout)

        self._breadcrumb = BreadcrumbWidget()

        title_layout = QHBoxLayout()
        title_layout.addItem(QSpacerItem(30, 0, QSizePolicy.Expanding, QSizePolicy.Fixed))
        title_layout.addWidget(self._breadcrumb)
        title_layout.addItem(QSpacerItem(30, 0, QSizePolicy.Expanding, QSizePolicy.Fixed))

        main_layout.addLayout(title_layout)

    def set(self, breadcrumbs):
        """
        Populates the breadcrumb control with a list of breadcrumbs
        :param breadcrumbs: each breadcrumb should derive from Breadcrumb class
        """

        self._breadcrumb.set(breadcrumbs)

    def set_from_path(self, file_path):
        """
        Creates a proper Breadcrumb list for given path and sets the text
        """

        self._breadcrumb.set_from_path(file_path)

    def get_texts(self):
        """
        Returns current
        :return: list(str)
        """

        return self._breadcrumb.get_texts()
