#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains consts definitions used by libraries
"""

from __future__ import print_function, division, absolute_import

from Qt.QtCore import *
from Qt.QtGui import *


class LibraryItemSignals(QObject, object):
    """
    Class that contains definition for LibraryItem signals
    """

    saved = Signal(object)
    saving = Signal(object)
    loaded = Signal(object)
    copied = Signal(object, object, object)
    deleted = Signal(object)
    renamed = Signal(object, object, object)


LIBRARY_DEFAULT_NAME = 'DefaultLibrary'

DEFAULT_ICON_MODE = 'icon'
DEFAULT_TABLE_MODE = 'table'

DPI_ENABLED = True
DPI_MIN_VALUE = 80
DPI_MAX_VALUE = 250

ITEM_DEFAULT_SORT_ROLE = 'SortRole'
ITEM_DEFAULT_DATA_ROLE = 'DataRole'
ITEM_DEFAULT_MAX_ICON_SIZE = 256
ITEM_DEFAULT_FONT_SIZE = 13
ITEM_DEFAULT_PLAYHEAD_COLOR = QColor(255, 255, 255, 220)
ITEM_DEFAULT_THUMBNAIL_COLUMN = 0
ITEM_DEFAULT_ENABLE_THUMBNAIL_THREAD = True
ITEM_DEFAULT_ENABLE_DELETE = False
ITEM_DEFAULT_ENABLE_NESTED_ITEMS = False
ITEM_DEFAULT_EXTENSION = ''
ITEM_DEFAULT_MENU_NAME = ''
ITEM_DEFAULT_MENU_ORDER = 10
ITEM_DEFAULT_MENU_ICON = ''

GROUP_ITEM_DEFAULT_FONT_SIZE = 24

TREE_MINIMUM_WIDTH = 5
TREE_DEFAULT_WIDTH = 100

LIST_DEFAULT_DRAG_THRESHOLD = 10

VIEWER_DEFAULT_PADDING = 5
VIEWER_DEFAULT_ZOOM_AMOUNT = 90
VIEWER_DEFAULT_TEXT_HEIGHT = 20
VIEWER_DEFAULT_WHEEL_SCROLL_STEP = 2
VIEWER_DEFAULT_MIN_SPACING = 0
VIEWER_DEFAULT_MAX_SPACING = 50
VIEWER_DEFAULT_MIN_LIST_SIZE = 15
VIEWER_DEFAULT_MIN_ICON_SIZE = 50
VIEWER_DEFAULT_TEXT_COLOR = QColor(255, 255, 255, 200)
VIEWER_DEFAULT_SELECTED_TEXT_COLOR = QColor(255, 255, 255, 200)
VIEWER_DEFAULT_BACKGROUND_COLOR = QColor(255, 255, 255, 30)
VIEWER_DEFAULT_BACKGROUND_HOVER_COLOR = QColor(255, 255, 255, 35)
VIEWER_DEFAULT_BACKGROUND_SELECTED_COLOR = QColor(30, 150, 255)

ICON_COLOR = QColor(255, 255, 255)
ICON_BADGE_COLOR = QColor(230, 230, 0)

PROGRESS_BAR_VISIBLE = True
SETTINGS_DIALOG_ENABLED = False
RECURSIVE_SEARCH_ENABLED = False

TRASH_NAME = 'trash'
TRASH_ENABLED = True

DEFAULT_RECURSIVE_DEPTH = 8
DEFAULT_RECURSIVE_SEARCH_ENABLED = False

DEFAULT_SETTINGS = {
    "library": {
        "sortBy": ["name:asc"],
        "groupBy": ["category:asc"]
    },
    "paneSizes": [160, 280, 180],
    "geometry": [-1, -1, 860, 720],
    "trashFolderVisible": False,
    "sidebarWidgetVisible": True,
    "previewWidgetVisible": True,
    "menuBarWidgetVisible": True,
    "statusBarWidgetVisible": True,
    "recursiveSearchEnabled": True,
    "itemsWidget": {
        "spacing": 2,
        "padding": 6,
        "zoomAmount": 80,
        "textVisible": True,
    },
    "searchWidget": {
        "text": "",
    },
    "filterByMenu": {
        "Folder": False
    },
    "theme": {
        "accentColor": "rgb(0, 175, 240, 255)",
        "backgroundColor": "rgb(60, 64, 79, 255)",
    }
}
