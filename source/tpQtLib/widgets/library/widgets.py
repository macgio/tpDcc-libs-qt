#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains different widgets used in libraries
"""

from __future__ import print_function, division, absolute_import

from tpQtLib.Qt.QtCore import *
from tpQtLib.Qt.QtWidgets import *
from tpQtLib.Qt.QtGui import *

from tpQtLib.core import animation, image
from tpQtLib.widgets import statusbar, progressbar, toolbar


class LibraryImageSequenceWidget(QToolButton, object):
    DEFAULT_PLAYHEAD_COLOR = QColor(255, 255, 255, 220)

    DEFAULT_STYLE = """
    QToolBar {
        border: 0px solid black; 
        border-radius:2px;
        background-color: rgb(0,0,0,100);
    }

    QToolButton {
        background-color: transparent;
    }
    """

    def __init__(self, *args):
        super(LibraryImageSequenceWidget, self).__init__(*args)

        self.setMouseTracking(True)

        self._image_sequence = image.ImageSequence('')
        self._image_sequence.frameChanged.connect(self._on_frame_changed)

        self._toolbar = QToolBar(self)
        self._toolbar.setStyleSheet(self.DEFAULT_STYLE)
        animation.fade_out_widget(self._toolbar, duration=0)

        spacer = QWidget()
        spacer.setMaximumWidth(4)
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self._toolbar.addWidget(spacer)

        spacer1 = QWidget()
        spacer1.setMaximumWidth(4)
        spacer1.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self._first_spacer = self._toolbar.addWidget(spacer1)

        self.set_size(150, 150)

    def set_size(self, w, h):
        """
        Set the size of the widget and updates icon size at the same time
        :param w: int
        :param h: int
        """

        self._size = QSize(w, h)
        self.setIconSize(self._size)
        self.setFixedSize(self._size)

    def _on_frame_changed(self, frame):
        pass


class LibrarySearchWidget(QLineEdit, object):
    SPACE_OPEARTOR = 'and'
    PLACEHOLDER_TEXT = 'Search'

    def __init__(self, *args):
        super(LibrarySearchWidget, self).__init__(*args)

        self._library = None

        tip = 'Search all current items'
        self.setToolTip(tip)
        self.setStatusTip(tip)

    def library(self):
        """
        Returns the library model for the menu
        :return: Library
        """

        return self._library

    def set_library(self, library):
        """
        Set the library model for the menu
        :param library: Library
        """

        self._library = library


class LibraryStatusWidget(statusbar.StatusWidget, object):
    DEFAULT_DISPLAY_TIME = 10000

    INFO_CSS = ''

    WARNING_CSS = """
        color: rgb(240, 240, 240);
        background-color: rgb(240, 170, 0);
    """

    ERROR_CSS = """
        color: rgb(240, 240, 240);
        background-color: rgb(220, 40, 40);
        selection-color: rgb(220, 40, 40);
        selection-background-color: rgb(240, 240, 240);
    """

    def __init__(self, *args):
        super(LibraryStatusWidget, self).__init__(*args)

        self.setFixedHeight(19)
        self.setMinimumWidth(5)

        self.main_layout.setContentsMargins(1, 0, 0, 0)

        self._progress_bar = progressbar.ProgressBar(self)
        self._progress_bar.hide()
        self.main_layout.addWidget(self._progress_bar)

    def show_info_message(self, message, msecs=None):
        """
        Overrides progressbar.ProgressBar show_info_message function
        Set an info message to be displayed in the status widget
        :param message: str
        :param msecs: float
        """

        self.setStyleSheet('')
        super(LibraryStatusWidget, self).show_info_message(message, msecs)

    def show_warning_message(self, message, msecs=None):
        """
        Overrides progressbar.ProgressBar show_warning_message function
        Set a warning message to be displayed in the status widget
        :param message: str
        :param msecs: float
        """

        if self.is_blocking():
            return

        self.setStyleSheet(self.WARNING_CSS)
        super(LibraryStatusWidget, self).show_warning_message(message, msecs)

    def show_error_message(self, message, msecs=None):
        """
        Overrides progressbar.ProgressBar show_error_message function
        Set an error message to be displayed in the status widget
        :param message: str
        :param msecs: float
        """

        self.setStyleSheet(self.ERROR_CSS)
        super(LibraryStatusWidget, self).show_error_message(message, msecs)

    def progress_bar(self):
        """
        Returns the progress bar widget
        :return:  progressbar.ProgressBar
        """

        return self._progress_bar


class LibraryToolbarWidget(toolbar.ToolBar, object):

    def __init__(self, *args):
        super(LibraryToolbarWidget, self).__init__(*args)

        self._dpi = 1

    def dpi(self):
        """
        Returns the zoom multiplier
        :return: float
        """

        return self._dpi

    def set_dpi(self, dpi):
        """
        Set the zoom multiplier
        :param dpi: float
        """

        self._dpi = dpi

    def expand_height(self):
        """
        Overrides base toolbar.Toolbar expand_height function
        Returns the height of menu bar when is expanded
        :return: int
        """

        return int(self._expanded_height * self.dpi())

    def collapse_height(self):
        """
        Overrides base toolbar.Toolbar collapse_height function
        Returns the height of widget when collapsed
        :return: int
        """

        return int(self._collapsed_height * self.dpi())


class LibrarySidebarWidget(QWidget, object):
    def __init__(self, *args):
        super(LibrarySidebarWidget, self).__init__(*args)

        self._library = None

    def library(self):
        """
        Returns the library model for the menu
        :return: Library
        """

        return self._library

    def set_library(self, library):
        """
        Set the library model for the menu
        :param library: Library
        """

        self._library = library
        self._library.dataChanged.connect(self._on_data_changed)
        self._on_data_changed()

    def _on_data_changed(self):
        """
        Internal callback function that is triggered when the library data changes
        """

        pass


class SortByMenu(QMenu, object):
    def __init__(self, *args, **kwargs):
        super(SortByMenu, self).__init__(*args, **kwargs)

        self._library = None

    def library(self):
        """
        Returns the library model for the menu
        :return: Library
        """

        return self._library

    def set_library(self, library):
        """
        Set the library model for the menu
        :param library: Library
        """

        self._library = library


class GroupByMenu(QMenu, object):
    def __init__(self, *args, **kwargs):
        super(GroupByMenu, self).__init__(*args, **kwargs)

        self._library = None

    def library(self):
        """
        Returns the library model for the menu
        :return: Library
        """

        return self._library

    def set_library(self, library):
        """
        Set the library model for the menu
        :param library: Library
        """

        self._library = library


class FilterByMenu(QMenu, object):
    def __init__(self, *args, **kwargs):
        super(FilterByMenu, self).__init__(*args, **kwargs)

        self._facets = list()
        self._library = None
        self._options = {'field': 'type'}
        self._settings = dict()

    def library(self):
        """
        Returns the library model for the menu
        :return: Library
        """

        return self._library

    def set_library(self, library):
        """
        Set the library model for the menu
        :param library: Library
        """

        self._library = library
        library.searchStarted.connect(self._on_search_init)

    def _on_search_init(self):
        pass

    def settings(self):
        """
        Returns the settings for the filter menu
        :return: dict
        """

        return self._settings

    def set_settings(self, settings):
        """
        Set the settings for the filter menu
        :param settings: dict
        """

        self._settings = settings

    def name(self):
        """
        Returns the name of the fulter used by the library
        """

        return self._options.get('field') + 'FilterMenu'

    def set_all_enabled(self, enabled):
        """
        Set all the filters enabled
        :param enabled: bool
        """

        for facet in self._facets:
            self._settings[facet.get('name')] = enabled

    def is_show_all_enabled(self):
        """
        Returns whether all current filters are enabled or not
        :return: bool
        """

        for facet in self._facets:
            if not self._settings.get(facet.get('name'), True):
                return False

        return True

    def is_active(self):
        """
        Returns whether are any filters currently active using the settings
        :return: bool
        """

        settings = self.settings()
        for name in settings:
            if not settings.get(name):
                return True

        return False
